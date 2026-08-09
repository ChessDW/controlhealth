import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Crea o actualiza un administrador desde variables de entorno durante el despliegue.'

    def handle(self, *args, **options):
        username = os.environ.get('BOOTSTRAP_ADMIN_USERNAME', '').strip()
        password = os.environ.get('BOOTSTRAP_ADMIN_PASSWORD', '')

        if not username or not password:
            self.stdout.write('Administrador inicial no configurado; se omite el bootstrap.')
            return

        user, created = User.objects.get_or_create(username=username)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        action = 'creado' if created else 'actualizado'
        self.stdout.write(self.style.SUCCESS(f'Administrador {action}: {username}'))
