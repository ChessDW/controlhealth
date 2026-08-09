from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0
    fields = (
        'medical_conditions', 'current_medications', 'emergency_contact_email',
        'age', 'sex', 'is_athlete', 'is_sedentary', 'is_overweight', 'resting_heart_rate',
    )

    def get_extra(self, request, obj=None, **kwargs):
        return 0 if obj and hasattr(obj, 'profile') else 1


class VitalSyncUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active')
    list_display_links = ('username',)
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)


admin.site.unregister(User)
admin.site.register(User, VitalSyncUserAdmin)

admin.site.site_header = 'Administración VitalSync'
admin.site.site_title = 'VitalSync Admin'
admin.site.index_title = 'Usuarios y perfiles registrados'
