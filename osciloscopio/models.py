from django.db import models

class NivelOsciloscopio(models.Model):
    TIPO_CHOICES = [('sen', 'Seno'), ('cos', 'Cosseno')]

    titulo = models.CharField(max_length=100, default="MISSÃO DESCONHECIDA")
    descricao = models.TextField(blank=True, help_text="Texto introdutório da missão")
    tipo_func = models.CharField(max_length=3, choices=TIPO_CHOICES, default='sen')

    # f(x) = A + B*sen(C*π*x + D)
    A = models.IntegerField(default=0, help_text="Deslocamento vertical (inteiro ≥ 0)")
    B = models.IntegerField(default=1, help_text="Amplitude (inteiro ≥ 1)")
    C = models.IntegerField(default=1, help_text="Frequência angular (inteiro ≥ 1)")
    D = models.IntegerField(default=0, help_text="Fase (inteiro ≥ 0)")

    ordem = models.PositiveIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordem', 'criado_em']
        verbose_name = "Nível"
        verbose_name_plural = "Níveis"

    def __str__(self):
        func = "sen" if self.tipo_func == 'sen' else "cos"
        return f"{self.titulo}: f(x) = {self.A} + {self.B}·{func}({self.C}πx + {self.D})"