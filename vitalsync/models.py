from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """Datos simulados del usuario para el prototipo VitalSync."""

    SEX_CHOICES = [
        ('F', 'Femenino'),
        ('M', 'Masculino'),
        ('O', 'Otro / prefiero no decir'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    medical_conditions = models.JSONField(default=list, blank=True)
    # Cada medicamento se guarda como dict: {generic_name, commercial_name,
    # times_per_day, dosage_mg, affects_heart_rate, active}
    current_medications = models.JSONField(default=list, blank=True)
    emergency_contact_email = models.EmailField(blank=True)

    # --- Personalización para la estimación de ansiedad ---
    age = models.PositiveIntegerField(null=True, blank=True)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, blank=True)
    is_athlete = models.BooleanField(default=False)
    is_sedentary = models.BooleanField(default=False)
    is_overweight = models.BooleanField(default=False)
    resting_heart_rate = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Frecuencia cardíaca habitual en reposo (lpm).'
    )

    def __str__(self):
        return f'Perfil de {self.user.username}'
