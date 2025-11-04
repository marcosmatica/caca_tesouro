from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import Equipe, SessaoDispositivo


@admin.register(Equipe)
class EquipeAdmin(UserAdmin):
    list_display = ('username', 'email', 'etapa_atual', 'progresso_visual', 'tempo_jogo', 'is_active')
    list_filter = ('etapa_atual', 'is_active', 'data_inicio_jogo', 'data_conclusao_jogo')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    fieldsets = UserAdmin.fieldsets + (
        ('Progresso da Caça ao Tesouro', {
            'fields': ('etapa_atual', 'data_inicio_jogo', 'data_conclusao_jogo', 'total_tentativas_erradas')
        }),
    )

    readonly_fields = ('data_criacao', 'data_inicio_jogo', 'data_conclusao_jogo')

    def progresso_visual(self, obj):
        percentual = obj.progresso_percentual()
        cor = 'green' if percentual == 100 else 'orange' if percentual > 50 else 'red'
        return format_html(
            '<div style="width:100px; background:#ddd; height:20px; border-radius:10px;">'
            '<div style="width:{}px; background:{}; height:20px; border-radius:10px; text-align:center; color:white; font-size:12px; line-height:20px;">{}&thinsp;%</div>'
            '</div>',
            percentual, cor, percentual
        )

    progresso_visual.short_description = 'Progresso'

    def tempo_jogo(self, obj):
        tempo = obj.tempo_total_jogo()
        if not tempo:
            return '-'

        segundos = int(tempo.total_seconds())
        horas = segundos // 3600
        minutos = (segundos % 3600) // 60
        segs = segundos % 60

        return f'{horas:02d}:{minutos:02d}:{segs:02d}'

    tempo_jogo.short_description = 'Tempo Total'

    actions = ['resetar_progresso']

    def resetar_progresso(self, request, queryset):
        for equipe in queryset:
            equipe.etapa_atual = None
            equipe.data_inicio_jogo = None
            equipe.data_conclusao_jogo = None
            equipe.total_tentativas_erradas = 0
            equipe.save()

            # Limpa progressos
            equipe.progressos.all().delete()

        self.message_user(request, f'{queryset.count()} equipe(s) resetada(s) com sucesso!')

    resetar_progresso.short_description = 'Resetar progresso das equipes selecionadas'


@admin.register(SessaoDispositivo)
class SessaoDispositivoAdmin(admin.ModelAdmin):
    list_display = ('equipe', 'nome_dispositivo_ou_key', 'primeiro_acesso', 'ultimo_acesso', 'ativo')
    list_filter = ('ativo', 'primeiro_acesso')
    search_fields = ('equipe__username', 'nome_dispositivo', 'session_key')
    date_hierarchy = 'primeiro_acesso'

    readonly_fields = ('session_key', 'primeiro_acesso', 'ultimo_acesso', 'user_agent')

    def nome_dispositivo_ou_key(self, obj):
        return obj.nome_dispositivo or f'[{obj.session_key[:12]}...]'

    nome_dispositivo_ou_key.short_description = 'Dispositivo'