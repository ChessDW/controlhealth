from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('vitalsync', '0002_userprofile_personalization'),
    ]

    operations = [
        migrations.CreateModel(
            name='HeartRateMeasurement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bpm', models.PositiveSmallIntegerField()),
                ('device_name', models.CharField(blank=True, max_length=120)),
                ('recorded_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='heart_rate_measurements', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-recorded_at']},
        ),
    ]
