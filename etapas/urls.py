from django.urls import path
from . import views

urlpatterns = [
    path('painel-admin/', views.painel_admin, name='painel_admin'),
    path('api/progresso-realtime/', views.api_progresso_realtime, name='api_progresso_realtime'),
]