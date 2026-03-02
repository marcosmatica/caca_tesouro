import json
import math
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import NivelOsciloscopio


def _calcular_pontos_dica(nivel):
    """
    Calcula pontos críticos (máximos/mínimos) e cruzamentos com y=A
    para a função f(x) = A + B·func(C·π·x + D), x ∈ [-2, 2].
    Retorna lista de {'x': ..., 'y': ..., 'tipo': 'max'|'min'|'zero'}.
    """
    A, B, C, D = nivel.A, nivel.B, nivel.C, nivel.D
    func = math.sin if nivel.tipo_func == 'sen' else math.cos
    deriv = math.cos if nivel.tipo_func == 'sen' else (lambda t: -math.sin(t))

    pontos = []
    passos = 2000
    x_min, x_max = -2, 2

    prev_deriv = None
    for i in range(passos + 1):
        x = x_min + (x_max - x_min) * i / passos
        arg = C * math.pi * x + D
        y = A + B * func(arg)
        dy = B * C * math.pi * deriv(arg)

        if prev_deriv is not None:
            # Mudança de sinal na derivada → ponto crítico
            if prev_deriv * dy < 0:
                x_c = x - (x_max - x_min) / passos / 2
                y_c = A + B * func(C * math.pi * x_c + D)
                tipo = 'max' if prev_deriv > 0 else 'min'
                pontos.append({'x': round(x_c, 3), 'y': round(y_c, 3), 'tipo': tipo})

            # Cruzamento com y = A (zero da oscilação)
            prev_y = A + B * func(C * math.pi * (x - (x_max - x_min) / passos) + D)
            if (prev_y - A) * (y - A) < 0:
                x_z = x - (x_max - x_min) / passos / 2
                pontos.append({'x': round(x_z, 3), 'y': A, 'tipo': 'zero'})

        prev_deriv = dy

    return pontos


def jogar(request, nivel_id):
    nivel = get_object_or_404(NivelOsciloscopio, pk=nivel_id)
    pontos_dica = _calcular_pontos_dica(nivel)

    context = {
        'nivel': nivel,
        'nivel_json': json.dumps({
            'id': nivel.id,
            'titulo': nivel.titulo,
            'descricao': nivel.descricao,
            'tipo_func': nivel.tipo_func,
            'A': nivel.A, 'B': nivel.B, 'C': nivel.C, 'D': nivel.D,
        }),
        'pontos_dica_json': json.dumps(pontos_dica),
    }
    return render(request, 'osciloscopio/painel.html', context)


def lista_niveis(request):
    niveis = NivelOsciloscopio.objects.all()
    return render(request, 'osciloscopio/lista.html', {'niveis': niveis})


def verificar_resposta(request, nivel_id):
    """Endpoint AJAX — valida A, B, C, D enviados pelo usuário."""
    if request.method != 'POST':
        return JsonResponse({'erro': 'Método inválido'}, status=405)
    nivel = get_object_or_404(NivelOsciloscopio, pk=nivel_id)
    data = json.loads(request.body)
    correto = (
        int(data.get('A', -1)) == nivel.A and
        int(data.get('B', -1)) == nivel.B and
        int(data.get('C', -1)) == nivel.C and
        int(data.get('D', -1)) == nivel.D and
        data.get('tipo_func') == nivel.tipo_func
    )
    return JsonResponse({'correto': correto})