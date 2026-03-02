from django.urls import path
from . import views

app_name = 'osciloscopio'

urlpatterns = [
    path('', views.lista_niveis, name='lista'),
    path('jogar/<int:nivel_id>/', views.jogar, name='jogar'),
    path('jogar/<int:nivel_id>/verificar/', views.verificar_resposta, name='verificar'),
]