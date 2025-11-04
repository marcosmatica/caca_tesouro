# etapas/models.py

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
import qrcode
from io import BytesIO
from django.core.files import File


class Etapa(models.Model):
    """
    Modelo para cada etapa da caça ao tesouro.
    Suporta etapas individuais e em grupo com validação de QR codes.
    """

    # Tipos de etapas
    TIPO_INDIVIDUAL = 'individual'
    TIPO_DUPLA = 'dupla'
    TIPO_TRIO = 'trio'
    TIPO_GRUPO = 'grupo'

    TIPOS_ETAPA = [
        (TIPO_INDIVIDUAL, 'Individual'),
        (TIPO_DUPLA, 'Dupla (2 dispositivos)'),
        (TIPO_TRIO, 'Trio (3 dispositivos)'),
        (TIPO_GRUPO, 'Grupo (todos os dispositivos)'),
    ]

    nome = models.CharField(max_length=100)
    ordem = models.IntegerField(unique=True, help_text="Ordem da etapa (0 a 12, sendo 0 o tema zero)")
    tipo = models.CharField(max_length=20, choices=TIPOS_ETAPA, default=TIPO_INDIVIDUAL)

    # Conteúdo da etapa
    pista = models.TextField(help_text="Texto ou descrição da pista")
    imagem = models.ImageField(upload_to='etapas/', blank=True, null=True)
    resposta_correta = models.CharField(max_length=200, blank=True,
                                        help_text="Resposta esperada (deixe vazio se for apenas QR code)")

    # QR Code único para esta etapa
    qrcode_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    qrcode_imagem = models.ImageField(upload_to='qrcodes/', blank=True, null=True)

    # Controle de tempo
    requer_tempo_minimo = models.BooleanField(default=False, help_text="Etapa só pode ser completada após tempo mínimo")
    tempo_minimo_segundos = models.IntegerField(default=0, help_text="Tempo mínimo em segundos desde início da etapa")

    # Navegação
    etapa_anterior = models.OneToOneField(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proxima_etapa_rel'
    )

    ativa = models.BooleanField(default=True, help_text="Se está ativa no jogo")
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ordem}. {self.nome} ({self.get_tipo_display()})"

    def save(self, *args, **kwargs):
        # Gera QR code automaticamente se não existir
        super().save(*args, **kwargs)
        if not self.qrcode_imagem:
            self.gerar_qrcode()

    def gerar_qrcode(self):
        """Gera a imagem do QR code para esta etapa"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(str(self.qrcode_token))
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        filename = f'qrcode_etapa_{self.ordem}.png'
        self.qrcode_imagem.save(filename, File(buffer), save=True)

    def dispositivos_necessarios(self):
        """Retorna número de dispositivos necessários"""
        if self.tipo == self.TIPO_INDIVIDUAL:
            return 1
        elif self.tipo == self.TIPO_DUPLA:
            return 2
        elif self.tipo == self.TIPO_TRIO:
            return 3
        return 999  # Todos do grupo

    class Meta:
        verbose_name = 'Etapa'
        verbose_name_plural = 'Etapas'
        ordering = ['ordem']


class ProgressoEtapa(models.Model):
    """
    Rastreia o progresso de cada equipe em cada etapa.
    Controla tempo de início e dispositivos que já validaram QR code.
    """
    equipe = models.ForeignKey('equipes.Equipe', on_delete=models.CASCADE, related_name='progressos')
    etapa = models.ForeignKey(Etapa, on_delete=models.CASCADE, related_name='progressos')

    inicio = models.DateTimeField(auto_now_add=True)
    conclusao = models.DateTimeField(null=True, blank=True)

    # Controle de dispositivos para etapas em grupo
    dispositivos_validados = models.JSONField(default=list,
                                              help_text="Lista de session_keys dos dispositivos que validaram")

    qrcode_escaneado = models.BooleanField(default=False)
    resposta_validada = models.BooleanField(default=False)

    class Meta:
        unique_together = ['equipe', 'etapa']
        verbose_name = 'Progresso da Etapa'
        verbose_name_plural = 'Progressos das Etapas'

    def __str__(self):
        return f"{self.equipe.username} - {self.etapa.nome}"

    def tempo_decorrido_segundos(self):
        """Retorna tempo decorrido desde início em segundos"""
        if self.conclusao:
            return (self.conclusao - self.inicio).total_seconds()
        return (timezone.now() - self.inicio).total_seconds()

    def pode_validar_por_tempo(self):
        """Verifica se já passou o tempo mínimo necessário"""
        if not self.etapa.requer_tempo_minimo:
            return True
        return self.tempo_decorrido_segundos() >= self.etapa.tempo_minimo_segundos

    def adicionar_dispositivo(self, session_key):
        """Adiciona dispositivo à lista de validados"""
        if session_key not in self.dispositivos_validados:
            self.dispositivos_validados.append(session_key)
            self.save()

    def dispositivos_faltantes(self):
        """Retorna quantos dispositivos ainda precisam validar"""
        necessarios = self.etapa.dispositivos_necessarios()
        validados = len(self.dispositivos_validados)
        return max(0, necessarios - validados)

    def todos_dispositivos_validados(self):
        """Verifica se todos dispositivos necessários já validaram"""
        return self.dispositivos_faltantes() == 0


class LogAcao(models.Model):
    """
    Log de todas as ações das equipes para auditoria e análise.
    """
    TIPO_LOGIN = 'login'
    TIPO_QRCODE = 'qrcode'
    TIPO_RESPOSTA = 'resposta'
    TIPO_AVANÇO = 'avanco'

    TIPOS = [
        (TIPO_LOGIN, 'Login'),
        (TIPO_QRCODE, 'QR Code Escaneado'),
        (TIPO_RESPOSTA, 'Resposta Enviada'),
        (TIPO_AVANÇO, 'Avanço de Etapa'),
    ]

    equipe = models.ForeignKey('equipes.Equipe', on_delete=models.CASCADE, related_name='logs')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    etapa = models.ForeignKey(Etapa, on_delete=models.SET_NULL, null=True, blank=True)

    descricao = models.TextField()
    dados_extra = models.JSONField(default=dict, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = 'Log de Ação'
        verbose_name_plural = 'Logs de Ações'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.equipe.username} - {self.get_tipo_display()} - {self.timestamp}"