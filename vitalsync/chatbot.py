import re
from urllib.parse import quote

import requests
from django.conf import settings


SYSTEM_PROMPT = """You are VitalSync Assistant, an empathetic, clear, and privacy-focused health AI embedded within the VitalSync web application.

CORE RESPONSIBILITIES
1. Answer general wellness, nutrition, fitness, and health metric tracking questions.
2. Explain vital sign trends and data in plain, accessible language.
3. Help users understand common symptoms and provide actionable lifestyle or self-care insights.

CRITICAL SAFETY AND TRIAGE GUIDELINES
- You are an informational assistant, not a licensed medical professional. Do not provide diagnoses or prescribe treatment or medications.
- If the user describes high-risk symptoms, severe chest pain, sudden difficulty breathing, extreme dizziness, severe numbness, self-harm, or immediate danger, urge them to contact emergency services or the nearest emergency room immediately.
- When discussing specific symptoms, include a brief educational-only disclaimer that professional medical advice is not replaced.

RESPONSE STYLE
- Be empathetic, objective, calm, reassuring, concise, and easy to scan.
- Use short paragraphs or brief bullet points. Avoid dense clinical jargon.
- Reply in the user's language. Never invent measurements or medical history.
- Treat the supplied user context as private. Do not mention it unless it is useful to answer the user.
"""

RED_FLAG_PATTERN = re.compile(
    r'(dolor.{0,30}pecho|chest pain|dificultad.{0,20}respirar|shortness of breath|'
    r'no puedo respirar|entumecimiento.{0,30}(repentino|sudden)|desmayo|fainting|'
    r'extreme dizziness|mareo.{0,20}(extremo|severo)|suicid|matarme|hacerme da[ñn]o|self.?harm)',
    re.IGNORECASE,
)


class GeminiConfigurationError(Exception):
    pass


class GeminiRequestError(Exception):
    pass


def emergency_reply(message):
    return bool(RED_FLAG_PATTERN.search(message))


def _health_context(profile, metrics):
    details = []
    if profile.medical_conditions:
        details.append(f"Known medical conditions: {', '.join(profile.medical_conditions)}.")
    if profile.current_medications:
        details.append(f"Current medications: {', '.join(profile.current_medications)}.")

    metric_labels = {
        'systolic': 'Systolic blood pressure (mmHg)',
        'diastolic': 'Diastolic blood pressure (mmHg)',
        'heart_rate': 'Heart rate (bpm)',
        'anxiety_estimate': 'App wellness estimate (%)',
    }
    for key, label in metric_labels.items():
        value = metrics.get(key)
        if isinstance(value, (int, float)):
            details.append(f"{label}: {value}.")

    return 'User Data Context (private, supplied by VitalSync):\n' + ('\n'.join(details) if details else 'No current profile or metric data was supplied.')


def generate_reply(message, profile, metrics, history):
    if not settings.GEMINI_API_KEY:
        raise GeminiConfigurationError('GEMINI_API_KEY is not configured.')

    contents = []
    for item in history[-6:]:
        role = 'model' if item.get('role') == 'assistant' else 'user'
        text = item.get('text', '').strip()
        if text:
            contents.append({'role': role, 'parts': [{'text': text[:2000]}]})
    contents.append({'role': 'user', 'parts': [{'text': message}]})

    payload = {
        'systemInstruction': {'parts': [{'text': f'{SYSTEM_PROMPT}\n\n{_health_context(profile, metrics)}'}]},
        'contents': contents,
        'generationConfig': {'temperature': 0.35, 'maxOutputTokens': 500},
    }
    model = quote(settings.GEMINI_MODEL, safe='-._')
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    try:
        response = requests.post(
            url,
            headers={'x-goog-api-key': settings.GEMINI_API_KEY, 'Content-Type': 'application/json'},
            json=payload,
            timeout=25,
        )
        response.raise_for_status()
        data = response.json()
        parts = data['candidates'][0]['content']['parts']
        text = ''.join(part.get('text', '') for part in parts).strip()
        if not text:
            raise GeminiRequestError('Gemini returned an empty response.')
        return text
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
        raise GeminiRequestError('Gemini could not generate a response.') from exc
