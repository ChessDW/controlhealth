from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """Datos simulados del usuario para el prototipo VitalSync."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    medical_conditions = models.JSONField(default=list, blank=True)
    current_medications = models.JSONField(default=list, blank=True)
    emergency_contact_email = models.EmailField(blank=True)

    def __str__(self):
        return f'Perfil de {self.user.username}'
