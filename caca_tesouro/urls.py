from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('equipes.urls')),
    path('etapas/', include('etapas.urls')),
path('osciloscopio/', include('osciloscopio.urls', namespace='osciloscopio')),
]

# Servir arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customização do admin
admin.site.site_header = "Caça ao Tesouro - Administração"
admin.site.site_title = "Admin Caça ao Tesouro"
admin.site.index_title = "Painel de Controle"