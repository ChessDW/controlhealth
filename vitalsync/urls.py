from django.contrib import admin
from django.urls import include, path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', views.healthcheck_view, name='healthcheck'),
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_user_view, name='register_user'),
    path('users/', views.manage_users_view, name='manage_users'),
    path('api/chat/', views.chatbot_view, name='chat_api'),
    path('api/emergency-alert/', views.emergency_alert_view, name='emergency_alert'),
    path('api/heart-rate-measurements/', views.heart_rate_measurement_view, name='heart_rate_measurement'),
    path('api/profile/', views.profile_update_view, name='profile_update'),
    path('api/', include('cedulas_proxy.urls')),
]
