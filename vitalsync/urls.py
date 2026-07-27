from django.contrib import admin
from django.urls import include, path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_user_view, name='register_user'),
    path('api/chat/', views.chatbot_view, name='chat_api'),
    path('api/', include('cedulas_proxy.urls')),
]
