from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('tema-zero/', views.tema_zero, name='tema_zero'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('etapa/<int:etapa_id>/', views.etapa_detalhe, name='etapa_detalhe'),
    path('qrcode-scanner/', views.qrcode_scanner, name='qrcode_scanner'),
    path('validar-qrcode/', views.validar_qrcode, name='validar_qrcode'),
    path('aguardando-grupo/<int:etapa_id>/', views.aguardando_grupo, name='aguardando_grupo'),
    path('vitoria/', views.vitoria, name='vitoria'),
]