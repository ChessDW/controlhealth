from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.cache import cache
import json
from django.shortcuts import redirect, render

from cedulas_proxy.views import CedulaLookupError, get_cedula_data
from .models import UserProfile
from .chatbot import GeminiConfigurationError, GeminiRequestError, emergency_reply, generate_reply


def _official_name(data):
    """Acepta las formas comunes de respuesta del API de cédulas."""
    if isinstance(data, dict):
        candidates = data.get('results') or data.get('data') or [data]
    else:
        candidates = data
    if not isinstance(candidates, list) or not candidates:
        return ''
    first = candidates[0]
    if not isinstance(first, dict):
        return ''
    return first.get('name') or first.get('nombre') or first.get('fullname') or ''


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    error_message = ''
    if request.method == 'POST':
        cedula = request.POST.get('cedula', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=cedula, password=password)
        if user is None:
            if not User.objects.filter(username=cedula).exists():
                error_message = 'La cédula no está registrada en VitalSync.'
            else:
                error_message = 'La contraseña es incorrecta.'
        else:
            try:
                data = get_cedula_data(cedula)
                name = _official_name(data)
            except CedulaLookupError:
                name = ''
            request.session['official_name'] = name or user.get_full_name() or cedula
            login(request, user)
            return redirect('dashboard')
    return render(request, 'login.html', {'error_message': error_message})


@login_required
def dashboard_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    official_name = request.session.get('official_name') or request.user.get_full_name() or request.user.username
    context = {
        'cedula': request.user.username,
        'official_name': official_name,
        'medical_conditions': profile.medical_conditions,
        'current_medications': profile.current_medications,
        'emergency_contact_email': profile.emergency_contact_email,
        'dashboard_data': {
            'name': official_name,
            'cedula': request.user.username,
            'conditions': profile.medical_conditions,
            'medications': profile.current_medications,
            'emergencyEmail': profile.emergency_contact_email,
        },
    }
    return render(request, 'vitalsync.html', context)


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def register_user_view(request):
    """Registro manual, reservado para el superusuario del prototipo."""
    if not request.user.is_superuser:
        return HttpResponseForbidden('Solo el superusuario puede registrar usuarios.')

    context = {'error_message': '', 'success_message': ''}
    if request.method == 'POST':
        cedula = request.POST.get('cedula', '').strip()
        password = request.POST.get('password', '')
        password_confirmation = request.POST.get('password_confirmation', '')
        conditions = [item.strip() for item in request.POST.get('conditions', '').split(',') if item.strip()]
        medications = [item.strip() for item in request.POST.get('medications', '').split(',') if item.strip()]
        emergency_email = request.POST.get('emergency_email', '').strip()

        if not cedula or not password:
            context['error_message'] = 'La cédula y la contraseña son obligatorias.'
        elif password != password_confirmation:
            context['error_message'] = 'Las contraseñas no coinciden.'
        elif User.objects.filter(username=cedula).exists():
            context['error_message'] = 'Esta cédula ya está registrada.'
        else:
            user = User.objects.create_user(username=cedula, password=password)
            UserProfile.objects.create(
                user=user,
                medical_conditions=conditions,
                current_medications=medications,
                emergency_contact_email=emergency_email,
            )
            context['success_message'] = f'Usuario con cédula {cedula} registrado correctamente.'

    return render(request, 'register_user.html', context)


@login_required
@require_POST
def chatbot_view(request):
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'La solicitud no tiene un formato válido.'}, status=400)

    message = str(payload.get('message', '')).strip()
    if not message or len(message) > 2000:
        return JsonResponse({'error': 'Escribe un mensaje de hasta 2,000 caracteres.'}, status=400)

    if emergency_reply(message):
        return JsonResponse({
            'reply': 'Lo siento que estés pasando por esto. Por los síntomas que describes, busca ayuda médica inmediata: llama al 9-1-1 o acude al servicio de emergencias más cercano. Si puedes, pide a alguien de confianza que se quede contigo.',
            'emergency': True,
        })

    rate_key = f'chatbot-rate-{request.user.pk}'
    attempts = cache.get(rate_key, 0)
    if attempts >= 12:
        return JsonResponse({'error': 'Has enviado muchos mensajes. Espera un minuto e inténtalo de nuevo.'}, status=429)
    cache.set(rate_key, attempts + 1, timeout=60)

    metrics = payload.get('metrics', {})
    if not isinstance(metrics, dict):
        metrics = {}
    clean_metrics = {}
    for key in ('systolic', 'diastolic', 'heart_rate', 'anxiety_estimate'):
        value = metrics.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            clean_metrics[key] = value

    history = payload.get('history', [])
    if not isinstance(history, list):
        history = []
    safe_history = [item for item in history if isinstance(item, dict) and item.get('role') in ('user', 'assistant')]

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    try:
        reply = generate_reply(message, profile, clean_metrics, safe_history)
    except GeminiConfigurationError:
        return JsonResponse({'error': 'El asistente no está configurado todavía. Contacta al administrador.'}, status=503)
    except GeminiRequestError:
        return JsonResponse({'error': 'El asistente no está disponible en este momento. Inténtalo de nuevo pronto.'}, status=502)

    return JsonResponse({'reply': reply, 'emergency': False})
