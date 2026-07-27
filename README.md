# VitalSync

VitalSync es un prototipo de aplicaci�n web de salud construido con Django. Est� pensado para monitoreo de signos vitales, soporte personal de bienestar y consulta de c�dulas desde un proxy seguro.

## Caracter�sticas principales

- Inicio de sesi�n con c�dula como identificador de usuario
- Dashboard de salud con perfil m�dico y estado de bienestar
- Asistente AI con integraci�n a Gemini / Google Generative Language
- Proxy de consulta de c�dulas con cach� local de 7 d�as
- Interfaz de usuario tipo app m�vil servida desde `templates/vitalsync.html`
- Registro de usuarios manual limitado al superusuario

## Estructura del proyecto

```
VitalSync/
+-- README.md
+-- .gitignore
+-- vitalsync_backend/
    +-- manage.py
    +-- requirements.txt
    +-- db.sqlite3
    +-- templates/
    �   +-- login.html
    �   +-- register_user.html
    �   +-- vitalsync.html
    +-- vitalsync/
    �   +-- __init__.py
    �   +-- settings.py
    �   +-- urls.py
    �   +-- views.py
    �   +-- models.py
    �   +-- chatbot.py
    �   +-- wsgi.py
    +-- cedulas_proxy/
        +-- __init__.py
        +-- urls.py
        +-- views.py
```

## Requisitos

- Python 3.11+ o compatible con Django 5.1
- `pip`

## Instalaci�n local

```bash
cd vitalsync_backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abre `http://localhost:8000` en tu navegador.

## Variables de entorno

- `GEMINI_API_KEY`: clave de API para el asistente de IA
- `GEMINI_MODEL`: modelo de Gemini a usar (por defecto `gemini-2.5-flash`)


## Uso

1. Inicia sesi�n con una c�dula registrada.
2. Si eres superusuario, ve a `/register/` para crear nuevos usuarios.
3. Navega el dashboard para ver estado, perfil, regulaciones de respiraci�n y AI.
4. La ruta `/api/cedulas/<query>/` consulta c�dulas v�a proxy hacia `https://apis.gometa.org/cedulas/<query>`.

## Rutas principales

- `/` � dashboard de usuario
- `/login/` � inicio de sesi�n
- `/logout/` � cerrar sesi�n
- `/register/` � registrar usuario (superusuario)
- `/api/chat/` � endpoint de chat AI
- `/api/cedulas/<query>/` � proxy de consulta de c�dulas

## Componentes clave

- `vitalsync_backend/vitalsync/views.py`: autenticaci�n, dashboard, registro y API del asistente
- `vitalsync_backend/vitalsync/chatbot.py`: l�gica de generaci�n de respuestas con Gemini
- `vitalsync_backend/vitalsync/models.py`: modelo `UserProfile`
- `vitalsync_backend/cedulas_proxy/views.py`: consulta y cache de c�dulas
- `vitalsync_backend/templates/vitalsync.html`: UI principal tipo app m�vil

## Dependencias

- Django==5.1.15
- django-cors-headers==4.9.0
- requests==2.32.5
