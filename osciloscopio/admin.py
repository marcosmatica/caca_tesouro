from django.contrib import admin
from .models import NivelOsciloscopio

@admin.register(NivelOsciloscopio)
class NivelAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo_func', 'A', 'B', 'C', 'D', 'ordem']
    list_editable = ['ordem']
    fieldsets = (
        ("Missão", {'fields': ('titulo', 'descricao', 'ordem')}),
        ("Função Alvo", {
            'description': "f(x) = A + B · func(C·π·x + D)",
            'fields': ('tipo_func', 'A', 'B', 'C', 'D'),
        }),
    )