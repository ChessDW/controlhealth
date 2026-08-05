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
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`: credenciales SMTP para las alertas de emergencia.
- `EMERGENCY_EMAIL_FROM`: dirección remitente de esas alertas (normalmente la misma cuenta SMTP).

El botón de emergencia envía un correo al contacto de emergencia configurado para el usuario después de tres pulsaciones realizadas en seis segundos. Si el usuario autoriza la ubicación, el correo incluye un enlace a Google Maps. El envío se limita a una alerta cada cinco minutos por usuario.


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

## Despliegue en Railway

El repositorio incluye `railway.json`: Railway instala las dependencias, recopila archivos estáticos, aplica las migraciones y arranca Gunicorn. Crea un servicio PostgreSQL en el mismo proyecto y define en el servicio web:

```text
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=<clave larga y aleatoria>
DEBUG=false
GEMINI_API_KEY=<tu clave Gemini>
EMAIL_HOST=<host SMTP>
EMAIL_PORT=587
EMAIL_HOST_USER=<usuario SMTP>
EMAIL_HOST_PASSWORD=<contraseña de aplicación SMTP>
EMAIL_USE_TLS=true
EMERGENCY_EMAIL_FROM=<correo remitente>
```

Después de generar el dominio público de Railway, define también `ALLOWED_HOSTS` con el dominio sin `https://` y `CSRF_TRUSTED_ORIGINS` con la URL completa. No configures `RAILWAY_PUBLIC_DOMAIN` manualmente: Railway lo proporciona al generar el dominio.

## Despliegue en Render

El archivo `render.yaml` crea un servicio web y una base de datos PostgreSQL mediante un Blueprint. En Render, selecciona **New → Blueprint**, conecta este repositorio y confirma la configuración. Render define automáticamente el dominio de su servicio y VitalSync lo usa para `ALLOWED_HOSTS` y CSRF.

Antes del primer despliegue, introduce en Render los valores secretos solicitados: `GEMINI_API_KEY`, `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` y `EMERGENCY_EMAIL_FROM`.

Si no tienes acceso a Render Shell, agrega temporalmente `BOOTSTRAP_ADMIN_USERNAME` (la cédula que usarás para entrar) y `BOOTSTRAP_ADMIN_PASSWORD`. El siguiente despliegue creará ese administrador. Elimina ambas variables después de confirmar el acceso.
