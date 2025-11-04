# equipes/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from etapas.models import Etapa, ProgressoEtapa, LogAcao
from .models import SessaoDispositivo
from .decorators import etapa_liberada_required


def login_view(request):
    """View de login das equipes"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Registra log de login
            LogAcao.objects.create(
                equipe=user,
                tipo=LogAcao.TIPO_LOGIN,
                descricao=f"Login realizado",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            # Redireciona baseado no progresso
            if not user.etapa_atual:
                return redirect('tema_zero')
            return redirect('dashboard')
        else:
            messages.error(request, 'Credenciais inválidas')

    return render(request, 'equipes/login.html')


@login_required
def tema_zero(request):
    """
    Primeira etapa - senha inicial antes do dashboard.
    Etapa 0 é especial e não usa QR code.
    """
    user = request.user

    # Se já passou do tema zero, redireciona
    if user.etapa_atual and user.etapa_atual.ordem > 0:
        return redirect('dashboard')

    try:
        etapa_zero = Etapa.objects.get(ordem=0, ativa=True)
    except Etapa.DoesNotExist:
        messages.error(request, 'Configuração do jogo incompleta - Tema Zero não encontrado.')
        return redirect('dashboard')

    if request.method == 'POST':
        senha_digitada = request.POST.get('senha', '').strip().lower()

        if senha_digitada == etapa_zero.resposta_correta.lower():
            # Inicia o jogo e avança para próxima etapa
            user.iniciar_jogo()

            try:
                proxima = Etapa.objects.get(ordem=1, ativa=True)
                user.etapa_atual = proxima
                user.save()

                # Cria progresso para a nova etapa
                ProgressoEtapa.objects.get_or_create(equipe=user, etapa=proxima)

                # Log de avanço
                LogAcao.objects.create(
                    equipe=user,
                    tipo=LogAcao.TIPO_AVANCO,
                    etapa=proxima,
                    descricao=f"Passou do Tema Zero para {proxima.nome}",
                    ip_address=request.META.get('REMOTE_ADDR')
                )

                messages.success(request, f'Parabéns! Você desbloqueou: {proxima.nome}')
                return redirect('dashboard')
            except Etapa.DoesNotExist:
                messages.error(request, 'Erro: próxima etapa não configurada.')
        else:
            user.total_tentativas_erradas += 1
            user.save()

            LogAcao.objects.create(
                equipe=user,
                tipo=LogAcao.TIPO_RESPOSTA,
                etapa=etapa_zero,
                descricao=f"Resposta incorreta no Tema Zero: '{senha_digitada}'",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            messages.error(request, 'Senha incorreta! Tente novamente.')

    return render(request, 'equipes/tema_zero.html', {'etapa': etapa_zero})


@login_required
def dashboard(request):
    """
    Dashboard principal com mapa de progresso e etapas disponíveis.
    """
    user = request.user

    # Garante que usuário tem sessão de dispositivo
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    sessao, created = SessaoDispositivo.objects.get_or_create(
        equipe=user,
        session_key=session_key,
        defaults={'user_agent': request.META.get('HTTP_USER_AGENT', '')}
    )

    if not created:
        sessao.ultimo_acesso = timezone.now()
        sessao.save()

    # Busca todas etapas ativas
    etapas = Etapa.objects.filter(ativa=True).order_by('ordem')

    # Prepara informações de progresso para cada etapa
    etapas_info = []
    for etapa in etapas:
        info = {
            'etapa': etapa,
            'desbloqueada': False,
            'atual': False,
            'concluida': False,
            'aguardando_grupo': False,
        }

        # Verifica se é a etapa atual
        if user.etapa_atual and user.etapa_atual.id == etapa.id:
            info['desbloqueada'] = True
            info['atual'] = True

            # Verifica se está aguardando outros dispositivos
            try:
                progresso = ProgressoEtapa.objects.get(equipe=user, etapa=etapa)
                if etapa.tipo != Etapa.TIPO_INDIVIDUAL and not progresso.todos_dispositivos_validados():
                    info['aguardando_grupo'] = True
                    info['dispositivos_faltantes'] = progresso.dispositivos_faltantes()
            except ProgressoEtapa.DoesNotExist:
                pass

        # Verifica se foi concluída
        elif user.etapa_atual and user.etapa_atual.ordem > etapa.ordem:
            info['desbloqueada'] = True
            info['concluida'] = True

        etapas_info.append(info)

    context = {
        'etapas_info': etapas_info,
        'etapa_atual': user.etapa_atual,
        'progresso_percentual': user.progresso_percentual(),
        'sessao': sessao,
    }

    return render(request, 'equipes/dashboard.html', context)


@login_required
@etapa_liberada_required
def etapa_detalhe(request, etapa_id):
    """
    View detalhada de uma etapa específica.
    Mostra pista, permite entrada de resposta e validação de QR code.
    """
    etapa = get_object_or_404(Etapa, id=etapa_id, ativa=True)
    user = request.user

    # Pega ou cria progresso desta etapa
    progresso, created = ProgressoEtapa.objects.get_or_create(
        equipe=user,
        etapa=etapa
    )

    # Verifica se está aguardando outros dispositivos
    aguardando_grupo = False
    if etapa.tipo != Etapa.TIPO_INDIVIDUAL:
        if not progresso.todos_dispositivos_validados():
            aguardando_grupo = True

    # Processa resposta (se houver)
    if request.method == 'POST' and etapa.resposta_correta:
        resposta = request.POST.get('resposta', '').strip().lower()

        if resposta == etapa.resposta_correta.lower():
            progresso.resposta_validada = True
            progresso.save()

            # Se não precisa de QR code OU já foi escaneado, avança
            if not etapa.qrcode_imagem or progresso.qrcode_escaneado:
                if progresso.todos_dispositivos_validados() and progresso.pode_validar_por_tempo():
                    return avancar_etapa(request, user, etapa, progresso)

            messages.success(request, 'Resposta correta! Agora escaneie o QR code.')
        else:
            user.total_tentativas_erradas += 1
            user.save()

            LogAcao.objects.create(
                equipe=user,
                tipo=LogAcao.TIPO_RESPOSTA,
                etapa=etapa,
                descricao=f"Resposta incorreta: '{resposta}'",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            messages.error(request, 'Resposta incorreta! Tente novamente.')

    context = {
        'etapa': etapa,
        'progresso': progresso,
        'aguardando_grupo': aguardando_grupo,
        'dispositivos_faltantes': progresso.dispositivos_faltantes(),
        'tempo_minimo_restante': max(0,
                                     etapa.tempo_minimo_segundos - progresso.tempo_decorrido_segundos()) if etapa.requer_tempo_minimo else 0,
    }

    return render(request, 'equipes/etapa.html', context)


@login_required
@require_http_methods(["POST"])
def validar_qrcode(request):
    """
    API endpoint para validar QR code escaneado.
    Retorna JSON com resultado da validação.
    """
    qrcode_token = request.POST.get('qrcode_token', '').strip()
    user = request.user
    session_key = request.session.session_key

    if not qrcode_token:
        return JsonResponse({'success': False, 'error': 'Token não fornecido'})

    try:
        # Busca etapa pelo token do QR code
        etapa = Etapa.objects.get(qrcode_token=qrcode_token, ativa=True)

        # Verifica se é a etapa atual do usuário
        if not user.etapa_atual or user.etapa_atual.id != etapa.id:
            LogAcao.objects.create(
                equipe=user,
                tipo=LogAcao.TIPO_QRCODE,
                etapa=etapa,
                descricao=f"QR code escaneado fora de ordem (etapa atual: {user.etapa_atual})",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return JsonResponse({
                'success': False,
                'error': 'QR code da etapa errada! Você deve seguir a ordem.',
                'etapa_errada': etapa.nome
            })

        # Pega progresso
        progresso, _ = ProgressoEtapa.objects.get_or_create(equipe=user, etapa=etapa)

        # Verifica tempo mínimo
        if not progresso.pode_validar_por_tempo():
            tempo_restante = int(etapa.tempo_minimo_segundos - progresso.tempo_decorrido_segundos())
            return JsonResponse({
                'success': False,
                'error': f'Aguarde {tempo_restante} segundos antes de validar este QR code.',
                'tempo_restante': tempo_restante
            })

        # Adiciona dispositivo à lista de validados
        progresso.adicionar_dispositivo(session_key)
        progresso.qrcode_escaneado = True
        progresso.save()

        LogAcao.objects.create(
            equipe=user,
            tipo=LogAcao.TIPO_QRCODE,
            etapa=etapa,
            descricao=f"QR code validado com sucesso (dispositivo: {session_key[:8]})",
            dados_extra={'session_key': session_key},
            ip_address=request.META.get('REMOTE_ADDR')
        )

        # Verifica se todos dispositivos já validaram
        if progresso.todos_dispositivos_validados():
            # Verifica se também precisa de resposta
            if etapa.resposta_correta and not progresso.resposta_validada:
                return JsonResponse({
                    'success': True,
                    'message': 'QR code validado! Agora responda a pergunta.',
                    'aguardando_resposta': True
                })

            # Pode avançar!
            resultado = avancar_etapa(request, user, etapa, progresso)
            if isinstance(resultado, JsonResponse):
                return resultado

            return JsonResponse({
                'success': True,
                'message': 'Etapa concluída! Avançando...',
                'avancar': True,
                'redirect_url': '/dashboard/'
            })
        else:
            # Aguardando outros dispositivos
            return JsonResponse({
                'success': True,
                'message': f'QR code validado! Aguardando {progresso.dispositivos_faltantes()} dispositivo(s).',
                'aguardando_grupo': True,
                'dispositivos_faltantes': progresso.dispositivos_faltantes()
            })

    except Etapa.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'QR code inválido!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Erro ao validar: {str(e)}'})


def avancar_etapa(request, user, etapa_atual, progresso):
    """
    Função auxiliar para avançar para próxima etapa.
    Usado tanto por validação de resposta quanto de QR code.
    """
    # Marca conclusão
    progresso.conclusao = timezone.now()
    progresso.save()

    # Busca próxima etapa
    try:
        proxima_etapa = Etapa.objects.get(ordem=etapa_atual.ordem + 1, ativa=True)
        user.etapa_atual = proxima_etapa
        user.save()

        # Cria progresso para nova etapa
        ProgressoEtapa.objects.get_or_create(equipe=user, etapa=proxima_etapa)

        # Log
        LogAcao.objects.create(
            equipe=user,
            tipo=LogAcao.TIPO_AVANCO,
            etapa=proxima_etapa,
            descricao=f"Avançou de '{etapa_atual.nome}' para '{proxima_etapa.nome}'",
            ip_address=request.META.get('REMOTE_ADDR')
        )

        messages.success(request, f'Parabéns! Você desbloqueou: {proxima_etapa.nome}')

        if request.is_ajax() or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Etapa concluída! Próxima: {proxima_etapa.nome}',
                'avancar': True,
                'redirect_url': '/dashboard/'
            })

        return redirect('dashboard')

    except Etapa.DoesNotExist:
        # Completou todas etapas!
        user.concluir_jogo()

        messages.success(request, '🎉 Parabéns! Você completou todas as etapas da Caça ao Tesouro!')

        if request.is_ajax() or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Jogo concluído!',
                'fim_jogo': True,
                'redirect_url': '/vitoria/'
            })

        return redirect('vitoria')


@login_required
def qrcode_scanner(request):
    """View para interface de scanner de QR code"""
    return render(request, 'equipes/qrcode_scanner.html')


@login_required
def aguardando_grupo(request, etapa_id):
    """View de espera quando aguardando outros dispositivos do grupo"""
    etapa = get_object_or_404(Etapa, id=etapa_id)
    progresso = get_object_or_404(ProgressoEtapa, equipe=request.user, etapa=etapa)

    return render(request, 'equipes/aguardando_grupo.html', {
        'etapa': etapa,
        'progresso': progresso,
        'dispositivos_faltantes': progresso.dispositivos_faltantes()
    })


@login_required
def vitoria(request):
    """View de conclusão do jogo"""
    user = request.user
    tempo_total = user.tempo_total_jogo()

    return render(request, 'equipes/vitoria.html', {
        'tempo_total': tempo_total,
        'tentativas_erradas': user.total_tentativas_erradas
    })