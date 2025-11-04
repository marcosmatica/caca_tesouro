# equipes/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Equipe(AbstractUser):
    """
    Modelo customizado de usuário para as equipes.
    Cada equipe tem seu progresso individual na caça ao tesouro.
    """

    # Campos adicionais além dos padrões do AbstractUser
    etapa_atual = models.ForeignKey(
        'etapas.Etapa',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipes_na_etapa'
    )

    data_criacao = models.DateTimeField(auto_now_add=True)
    data_inicio_jogo = models.DateTimeField(null=True, blank=True, help_text="Quando a equipe iniciou o jogo")
    data_conclusao_jogo = models.DateTimeField(null=True, blank=True,
                                               help_text="Quando a equipe completou todas etapas")

    # Estatísticas
    total_tentativas_erradas = models.IntegerField(default=0)

    def __str__(self):
        return self.username

    def iniciar_jogo(self):
        """Marca o início do jogo para esta equipe"""
        if not self.data_inicio_jogo:
            self.data_inicio_jogo = timezone.now()
            self.save()

    def concluir_jogo(self):
        """Marca a conclusão do jogo"""
        if not self.data_conclusao_jogo:
            self.data_conclusao_jogo = timezone.now()
            self.save()

    def tempo_total_jogo(self):
        """Retorna tempo total gasto no jogo"""
        if not self.data_inicio_jogo:
            return None
        fim = self.data_conclusao_jogo or timezone.now()
        return fim - self.data_inicio_jogo

    def progresso_percentual(self):
        """Retorna percentual de conclusão do jogo"""
        from etapas.models import Etapa
        total_etapas = Etapa.objects.filter(ativa=True).count()
        if total_etapas == 0:
            return 0
        if not self.etapa_atual:
            return 0
        return int((self.etapa_atual.ordem / total_etapas) * 100)

    class Meta:
        verbose_name = 'Equipe'
        verbose_name_plural = 'Equipes'


class SessaoDispositivo(models.Model):
    """
    Rastreia sessões de dispositivos para controle de validações em grupo.
    """
    equipe = models.ForeignKey(Equipe, on_delete=models.CASCADE, related_name='sessoes')
    session_key = models.CharField(max_length=40, unique=True)

    nome_dispositivo = models.CharField(max_length=100, blank=True,
                                        help_text="Nome opcional para identificar dispositivo")
    user_agent = models.TextField(blank=True)

    primeiro_acesso = models.DateTimeField(auto_now_add=True)
    ultimo_acesso = models.DateTimeField(auto_now=True)

    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.equipe.username} - {self.nome_dispositivo or self.session_key[:8]}"

    class Meta:
        verbose_name = 'Sessão de Dispositivo'
        verbose_name_plural = 'Sessões de Dispositivos'