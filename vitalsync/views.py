from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseForbidden
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import json
from django.shortcuts import redirect, render

from cedulas_proxy.views import CedulaLookupError, get_cedula_data
from .models import UserProfile
from .chatbot import GeminiConfigurationError, GeminiRequestError, emergency_reply, generate_reply


def healthcheck_view(request):
    return HttpResponse('ok', content_type='text/plain')


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
                error_message = 'La cédula no está registrada en ControlHealth.'
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
def manage_users_view(request):
    """Permite al administrador restablecer contraseñas sin usar Django Admin."""
    if not request.user.is_superuser:
        return HttpResponseForbidden('Solo el superusuario puede administrar usuarios.')

    context = {'error_message': '', 'success_message': '', 'users': User.objects.order_by('username')}
    if request.method == 'POST':
        user_id = request.POST.get('user_id', '')
        password = request.POST.get('password', '')
        password_confirmation = request.POST.get('password_confirmation', '')
        try:
            target_user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError):
            context['error_message'] = 'El usuario seleccionado no existe.'
        else:
            if len(password) < 8:
                context['error_message'] = 'La contraseña debe tener al menos 8 caracteres.'
            elif password != password_confirmation:
                context['error_message'] = 'Las contraseñas no coinciden.'
            else:
                target_user.set_password(password)
                target_user.save(update_fields=['password'])
                context['success_message'] = f'Contraseña actualizada para {target_user.username}.'

    return render(request, 'manage_users.html', context)


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


@login_required
@require_POST
def emergency_alert_view(request):
    """Envía una alerta limitada al correo de emergencia registrado."""
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'La solicitud no tiene un formato válido.'}, status=400)

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if not profile.emergency_contact_email:
        return JsonResponse({'error': 'No hay un correo de emergencia configurado para este perfil.'}, status=400)
    if not settings.EMAIL_HOST or not settings.EMERGENCY_EMAIL_FROM:
        return JsonResponse({'error': 'El envío de alertas aún no está configurado.'}, status=503)

    rate_key = f'emergency-alert-rate-{request.user.pk}'
    if cache.get(rate_key):
        return JsonResponse({'error': 'Ya se envió una alerta. Espera 5 minutos antes de enviar otra.'}, status=429)

    location = payload.get('location')
    location_text = 'Ubicación no disponible (el usuario no la autorizó o el dispositivo no pudo obtenerla).'
    if isinstance(location, dict):
        latitude, longitude = location.get('latitude'), location.get('longitude')
        if (isinstance(latitude, (int, float)) and not isinstance(latitude, bool) and
                isinstance(longitude, (int, float)) and not isinstance(longitude, bool) and
                -90 <= latitude <= 90 and -180 <= longitude <= 180):
            location_text = f'Ubicación aproximada: https://maps.google.com/?q={latitude},{longitude}'

    name = request.session.get('official_name') or request.user.get_full_name() or request.user.username
    message = (
        f'{name} dice que está en una emergencia.\n\n'
        f'{location_text}\n\n'
        'Esta alerta fue enviada desde VitalSync. Si crees que hay peligro inmediato, contacta al 9-1-1.'
    )
    try:
        send_mail(
            subject=f'Alerta de emergencia de {name}',
            message=message,
            from_email=settings.EMERGENCY_EMAIL_FROM,
            recipient_list=[profile.emergency_contact_email],
            fail_silently=False,
        )
    except Exception:
        return JsonResponse({'error': 'No fue posible enviar la alerta. Intenta llamar al 9-1-1 o a tu contacto.'}, status=502)

    cache.set(rate_key, True, timeout=60 * 5)
    return JsonResponse({'sent': True})


@login_required
@require_POST
def profile_update_view(request):
    """Guarda los datos de perfil editables desde el panel."""
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'La solicitud no tiene un formato válido.'}, status=400)

    email = str(payload.get('emergency_email', '')).strip()
    if email:
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({'error': 'Ingresa un correo de emergencia válido.'}, status=400)

    def clean_list(value):
        if not isinstance(value, list):
            return []
        return [str(item).strip()[:120] for item in value[:20] if str(item).strip()]

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.emergency_contact_email = email
    profile.medical_conditions = clean_list(payload.get('conditions'))
    profile.current_medications = clean_list(payload.get('medications'))
    profile.save()
    return JsonResponse({'saved': True, 'emergency_email': profile.emergency_contact_email})
