# equipes/decorators.py

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from etapas.models import Etapa


def etapa_liberada_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        etapa_id = kwargs.get('etapa_id')
        if not etapa_id:
            return view_func(request, *args, **kwargs)

        try:
            etapa = Etapa.objects.get(id=etapa_id, ativa=True)
            user = request.user

            # Verifica se é a etapa atual
            if user.etapa_atual and user.etapa_atual.id == etapa.id:
                return view_func(request, *args, **kwargs)

            # Verifica se já passou desta etapa
            if user.etapa_atual and user.etapa_atual.ordem > etapa.ordem:
                return view_func(request, *args, **kwargs)

            # Acesso negado
            messages.error(request, f'Você não tem acesso à etapa "{etapa.nome}" ainda!')
            return redirect('dashboard')

        except Etapa.DoesNotExist:
            messages.error(request, 'Etapa não encontrada.')
            return redirect('dashboard')

    return _wrapped_view