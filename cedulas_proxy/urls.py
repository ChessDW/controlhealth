from django.urls import path
from . import views

urlpatterns = [
    path('cedulas/<str:query>/', views.cedula_proxy),
]