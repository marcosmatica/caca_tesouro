from django.contrib import admin
from django.utils.html import format_html
from .models import Etapa, ProgressoEtapa, LogAcao


@admin.register(Etapa)
class EtapaAdmin(admin.ModelAdmin):
    list_display = ('ordem', 'nome', 'tipo', 'tem_qrcode', 'tem_resposta', 'requer_tempo', 'ativa')
    list_filter = ('tipo', 'ativa', 'requer_tempo_minimo')
    search_fields = ('nome', 'pista')
    ordering = ('ordem',)

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'ordem', 'tipo', 'ativa')
        }),
        ('Conteúdo', {
            'fields': ('pista', 'imagem', 'resposta_correta')
        }),
        ('QR Code', {
            'fields': ('qrcode_token', 'qrcode_imagem'),
            'description': 'O QR code é gerado automaticamente. Baixe a imagem para imprimir.'
        }),
        ('Controle de Tempo', {
            'fields': ('requer_tempo_minimo', 'tempo_minimo_segundos'),
            'classes': ('collapse',)
        }),
        ('Navegação', {
            'fields': ('etapa_anterior',)
        }),
    )

    readonly_fields = ('qrcode_token', 'qrcode_imagem')

    def tem_qrcode(self, obj):
        if obj.qrcode_imagem:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')

    tem_qrcode.short_description = 'QR Code'

    def tem_resposta(self, obj):
        if obj.resposta_correta:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: gray;">-</span>')

    tem_resposta.short_description = 'Resposta'

    def requer_tempo(self, obj):
        if obj.requer_tempo_minimo:
            return format_html(f'<span style="color: orange;">{obj.tempo_minimo_segundos}s</span>')
        return format_html('<span style="color: gray;">-</span>')

    requer_tempo.short_description = 'Tempo Mín.'

    actions = ['gerar_qrcodes_em_massa']

    def gerar_qrcodes_em_massa(self, request, queryset):
        for etapa in queryset:
            etapa.gerar_qrcode()
        self.message_user(request, f'{queryset.count()} QR codes gerados com sucesso!')

    gerar_qrcodes_em_massa.short_description = 'Gerar QR codes para etapas selecionadas'


@admin.register(ProgressoEtapa)
class ProgressoEtapaAdmin(admin.ModelAdmin):
    list_display = ('equipe', 'etapa', 'inicio', 'conclusao', 'tempo_gasto', 'status_dispositivos')
    list_filter = ('etapa', 'qrcode_escaneado', 'resposta_validada')
    search_fields = ('equipe__username', 'etapa__nome')
    date_hierarchy = 'inicio'

    readonly_fields = ('inicio', 'tempo_decorrido')

    def tempo_gasto(self, obj):
        segundos = obj.tempo_decorrido_segundos()
        minutos = int(segundos // 60)
        segs = int(segundos % 60)
        return f'{minutos}m {segs}s'

    tempo_gasto.short_description = 'Tempo'

    def status_dispositivos(self, obj):
        total = obj.etapa.dispositivos_necessarios()
        validados = len(obj.dispositivos_validados)

        if total == 1:
            return '-'

        cor = 'green' if validados >= total else 'orange'
        return format_html(f'<span style="color: {cor};">{validados}/{total}</span>')

    status_dispositivos.short_description = 'Dispositivos'

    def tempo_decorrido(self, obj):
        return f'{obj.tempo_decorrido_segundos():.1f} segundos'


@admin.register(LogAcao)
class LogAcaoAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'equipe', 'tipo', 'etapa', 'descricao_curta', 'ip_address')
    list_filter = ('tipo', 'timestamp', 'equipe')
    search_fields = ('equipe__username', 'descricao', 'etapa__nome')
    date_hierarchy = 'timestamp'

    readonly_fields = ('timestamp', 'equipe', 'tipo', 'etapa', 'descricao', 'dados_extra', 'ip_address')

    def descricao_curta(self, obj):
        return obj.descricao[:50] + '...' if len(obj.descricao) > 50 else obj.descricao

    descricao_curta.short_description = 'Descrição'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False