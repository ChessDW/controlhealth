"""WSGI config for the VitalSync production service."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vitalsync.settings')

application = get_wsgi_application()
