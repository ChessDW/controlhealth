from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from vitalsync.models import UserProfile


PROTOTYPE_USERS = [
    {'cedula': '108880123', 'password': 'vital123', 'conditions': ['Hipertensión'], 'medications': ['Losartán 50 mg'], 'email': 'contacto.demo1@example.com'},
    {'cedula': '107650432', 'password': 'vital456', 'conditions': ['Asma'], 'medications': ['Salbutamol'], 'email': 'contacto.demo2@example.com'},
]


class Command(BaseCommand):
    help = 'Crea o actualiza dos usuarios de prueba para el prototipo VitalSync.'

    def handle(self, *args, **options):
        for item in PROTOTYPE_USERS:
            user, _ = User.objects.get_or_create(username=item['cedula'])
            user.set_password(item['password'])
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'medical_conditions': item['conditions'],
                    'current_medications': item['medications'],
                    'emergency_contact_email': item['email'],
                },
            )
            self.stdout.write(self.style.SUCCESS(f"Usuario creado/actualizado: {item['cedula']}"))
