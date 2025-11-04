from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from .models import Etapa, ProgressoEtapa, LogAcao
from equipes.models import Equipe
from django.db.models import Count, Avg, Q
from django.utils import timezone


@staff_member_required
def painel_admin(request):
    """
    Painel administrativo para acompanhar progresso das equipes em tempo real.
    """
    equipes = Equipe.objects.all().order_by('-data_inicio_jogo')
    etapas = Etapa.objects.filter(ativa=True).order_by('ordem')

    # Estatísticas gerais
    total_equipes = equipes.count()
    equipes_jogando = equipes.filter(data_inicio_jogo__isnull=False, data_conclusao_jogo__isnull=True).count()
    equipes_concluidas = equipes.filter(data_conclusao_jogo__isnull=False).count()

    # Monta matriz de progresso
    progresso_matriz = []
    for equipe in equipes:
        etapas_status = []
        for etapa in etapas:
            try:
                progresso = ProgressoEtapa.objects.get(equipe=equipe, etapa=etapa)
                status = {
                    'concluida': progresso.conclusao is not None,
                    'em_andamento': progresso.conclusao is None,
                    'tempo': progresso.tempo_decorrido_segundos() if progresso.conclusao else None
                }
            except ProgressoEtapa.DoesNotExist:
                status = {'concluida': False, 'em_andamento': False, 'tempo': None}
            etapas_status.append(status)

        progresso_matriz.append({
            'equipe': equipe,
            'etapas': etapas_status,
            'tempo_total': equipe.tempo_total_jogo()
        })

    context = {
        'equipes': equipes,
        'etapas': etapas,
        'progresso_matriz': progresso_matriz,
        'total_equipes': total_equipes,
        'equipes_jogando': equipes_jogando,
        'equipes_concluidas': equipes_concluidas,
    }

    return render(request, 'etapas/painel_admin.html', context)


@staff_member_required
def api_progresso_realtime(request):
    """
    API para atualização em tempo real do painel administrativo.
    """
    equipes_data = []

    for equipe in Equipe.objects.all():
        equipes_data.append({
            'username': equipe.username,
            'etapa_atual': equipe.etapa_atual.nome if equipe.etapa_atual else 'Não iniciado',
            'progresso': equipe.progresso_percentual(),
            'tempo_jogo': str(equipe.tempo_total_jogo()) if equipe.tempo_total_jogo() else '0:00:00',
            'concluido': equipe.data_conclusao_jogo is not None
        })

    return JsonResponse({'equipes': equipes_data})