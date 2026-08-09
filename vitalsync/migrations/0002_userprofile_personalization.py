from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vitalsync', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='age',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='sex',
            field=models.CharField(
                blank=True,
                choices=[('F', 'Femenino'), ('M', 'Masculino'), ('O', 'Otro / prefiero no decir')],
                max_length=1,
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='is_athlete',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='is_sedentary',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='is_overweight',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='resting_heart_rate',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Frecuencia cardíaca habitual en reposo (lpm).',
                null=True,
            ),
        ),
    ]
