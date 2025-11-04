from django.core.management.base import BaseCommand
from etapas.models import Etapa
import os


def criar_etapas_exemplo():
    """
    Função auxiliar para criar 12 etapas de exemplo.
    Útil para testes e demonstração.
    """
    etapas_config = [
        {
            'ordem': 0,
            'nome': 'Tema Zero',
            'tipo': Etapa.TIPO_INDIVIDUAL,
            'pista': 'Bem-vindo à Caça ao Tesouro! Decifre a senha inicial para começar sua jornada.',
            'resposta_correta': 'iniciar',
            'etapa_anterior': None
        },
        {
            'ordem': 1,
            'nome': 'O Portal',
            'tipo': Etapa.TIPO_INDIVIDUAL,
            'pista': 'Encontre o portal mágico escondido no jardim. Ele brilha quando a lua está cheia.',
            'resposta_correta': '',  # Apenas QR code
        },
        {
            'ordem': 2,
            'nome': 'Dupla Misteriosa',
            'tipo': Etapa.TIPO_DUPLA,
            'pista': 'Dois caminhos se encontram. Somente juntos vocês podem prosseguir. Escaneiem os QR codes simultaneamente.',
            'resposta_correta': 'união',
            'requer_tempo_minimo': True,
            'tempo_minimo_segundos': 60
        },
        {
            'ordem': 3,
            'nome': 'A Biblioteca Antiga',
            'tipo': Etapa.TIPO_INDIVIDUAL,
            'pista': 'Entre as páginas amareladas, uma palavra ecoa através dos séculos. Qual é o nome do autor do primeiro livro?',
            'resposta_correta': 'shakespeare',
        },
        {
            'ordem': 4,
            'nome': 'Trio do Saber',
            'tipo': Etapa.TIPO_TRIO,
            'pista': 'Três pilares do conhecimento devem ser reunidos. Matemática, Ciência e Arte se encontram aqui.',
            'resposta_correta': 'sabedoria',
        },
        {
            'ordem': 5,
            'nome': 'O Labirinto',
            'tipo': Etapa.TIPO_INDIVIDUAL,
            'pista': 'Esquerda, direita, frente... qual caminho seguir? A resposta está nas estrelas.',
            'resposta_correta': 'norte',
            'requer_tempo_minimo': True,
            'tempo_minimo_segundos': 120
        },
        {
            'ordem': 6,
            'nome': 'Quebra-Cabeça Coletivo',
            'tipo': Etapa.TIPO_GRUPO,
            'pista': 'Todas as peças devem estar presentes. Somente unidos vocês verão a imagem completa.',
            'resposta_correta': 'equipe',
        },
        {
            'ordem': 7,
            'nome': 'A Caverna dos Ecos',
            'tipo': Etapa.TIPO_INDIVIDUAL,
            'pista': 'Seu grito retorna multiplicado. Quantas vezes você se ouve?',
            'resposta_correta': 'sete',
        },
        {
            'ordem': 8,
            'nome': 'Parceiros do Destino',
            'tipo': Etapa.TIPO_DUPLA,
            'pista': 'O destino une dois corações. Encontrem os símbolos gêmeos e escaneiem juntos.',
            'resposta_correta': 'destino',
        },
        {
            'ordem': 9,
            'nome': 'O Oráculo',
            'tipo': Etapa.TIPO_INDIVIDUAL,
            'pista': 'O oráculo fala em enigmas. "Eu começo com E e termino com E, mas só contenho uma letra. O que sou eu?"',
            'resposta_correta': 'envelope',
        },
        {
            'ordem': 10,
            'nome': 'Trindade Final',
            'tipo': Etapa.TIPO_TRIO,
            'pista': 'Corpo, mente e espírito. Três elementos se unem para a vitória final.',
            'resposta_correta': 'harmonia',
            'requer_tempo_minimo': True,
            'tempo_minimo_segundos': 90
        },
        {
            'ordem': 11,
            'nome': 'O Tesouro',
            'tipo': Etapa.TIPO_GRUPO,
            'pista': 'Vocês chegaram! O tesouro aguarda. Mas só pode ser aberto quando TODOS estiverem presentes.',
            'resposta_correta': 'vitoria',
        },
    ]

    etapas_criadas = []
    etapa_anterior_obj = None

    for config in etapas_config:
        etapa, created = Etapa.objects.get_or_create(
            ordem=config['ordem'],
            defaults={
                'nome': config['nome'],
                'tipo': config['tipo'],
                'pista': config['pista'],
                'resposta_correta': config['resposta_correta'],
                'requer_tempo_minimo': config.get('requer_tempo_minimo', False),
                'tempo_minimo_segundos': config.get('tempo_minimo_segundos', 0),
                'etapa_anterior': etapa_anterior_obj,
            }
        )

        if created:
            etapa.gerar_qrcode()
            print(f'✓ Etapa criada: {etapa.nome}')
        else:
            print(f'- Etapa já existe: {etapa.nome}')

        etapas_criadas.append(etapa)
        etapa_anterior_obj = etapa

    return etapas_criadas