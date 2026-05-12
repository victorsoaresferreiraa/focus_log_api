"""
=============================================================================
SERVICES — Focus Log API
=============================================================================

A camada de Services é onde mora a LÓGICA DE NEGÓCIO da aplicação.

Por que separar da view?
  - Views devem ser "burras" — só recebem request e retornam response.
  - Services são testáveis de forma independente — sem HTTP, sem banco real.
  - Reutilizáveis — a mesma lógica pode ser usada por múltiplas views.
  - Mais fácil de manter — quando a regra mudar, você sabe exatamente onde ir.

Esse padrão se chama "Service Layer" e é amplamente usado em empresas.

Referência: Martin Fowler — Patterns of Enterprise Application Architecture
=============================================================================
"""

from django.db.models import Avg, Sum, Count
from collections import Counter
from .models import RegistroFoco


class DiagnosticoService:
    """
    Serviço responsável por calcular o diagnóstico de produtividade.

    Encapsula toda a lógica de análise dos registros.
    A view só chama DiagnosticoService.gerar() e recebe o resultado.
    """

    # =========================================================================
    # CONSTANTES DE FEEDBACK
    # =========================================================================

    # Mensagens de feedback indexadas pela média de foco (arredondada)
    # Key: (min_incluso, max_excluso) → (mensagem, emoji, nível)
    FEEDBACK_RANGES = [
        (0.0, 1.5, {
            'mensagem': (
                'Você está com muita dificuldade de concentração. '
                'Considere eliminar distrações: celular no silencioso, '
                'fones de ouvido com música instrumental e pausas estruturadas.'
            ),
            'nivel': 'critico',
        }),
        (1.5, 2.5, {
            'mensagem': (
                'Seu foco está abaixo do ideal. '
                'Experimente a técnica Pomodoro: 25 min de trabalho + 5 min de pausa. '
                'Identifique e elimine as principais fontes de distração.'
            ),
            'nivel': 'baixo',
        }),
        (2.5, 3.5, {
            'mensagem': (
                'Foco moderado — você está trabalhando, mas com interrupções. '
                'Tente blocos de tempo maiores sem verificar mensagens. '
                'Pequenas melhorias no ambiente podem fazer grande diferença.'
            ),
            'nivel': 'moderado',
        }),
        (3.5, 4.5, {
            'mensagem': (
                'Bom nível de foco! Você está produtivo e no caminho certo. '
                'Continue com suas rotinas atuais e experimente aumentar '
                'gradualmente a duração das sessões.'
            ),
            'nivel': 'bom',
        }),
        (4.5, 5.1, {
            'mensagem': (
                'Excelente! Você está em uma maratona produtiva de alto nível! '
                'Estado de flow consistente. Documente sua rotina atual — '
                'ela está funcionando muito bem. Apenas lembre-se de descansar!'
            ),
            'nivel': 'excelente',
        }),
    ]

    # Dicas personalizadas por nível
    DICAS_POR_NIVEL = {
        'critico': [
            'Remova o celular da mesa durante as sessões de trabalho.',
            'Defina um horário fixo para verificar e-mails e mensagens.',
            'Experimente trabalhar em blocos curtos de 15 minutos inicialmente.',
            'Identifique qual horário do dia você tem mais energia e use-o para tarefas difíceis.',
        ],
        'baixo': [
            'Aplique a técnica Pomodoro: 25 min foco + 5 min pausa.',
            'Use fones de ouvido com música instrumental ou ruído branco.',
            'Anote as distrações que surgem para processá-las depois.',
            'Feche abas desnecessárias do navegador antes de começar.',
        ],
        'moderado': [
            'Tente aumentar seus blocos de foco para 45-50 minutos.',
            'Pratique meditação ou respiração profunda antes das sessões.',
            'Organize suas tarefas do dia anterior — chegue com um plano.',
            'Avalie se reuniões frequentes estão fragmentando sua concentração.',
        ],
        'bom': [
            'Experimente técnicas de deep work: blocos de 90-120 minutos.',
            'Compartilhe suas estratégias com a equipe — você está indo bem!',
            'Considere trabalhar em tarefas cognitivamente mais desafiadoras.',
            'Revise suas prioridades — produtividade alta é ótima para as tarefas certas.',
        ],
        'excelente': [
            'Você está em estado de flow regularmente — isso é raro e valioso!',
            'Documente sua rotina e ambiente para replicar esse sucesso.',
            'Certifique-se de incluir tempo de recuperação — sustentabilidade é chave.',
            'Considere mentorar colegas com suas estratégias de produtividade.',
        ],
    }

    @classmethod
    def gerar(cls):
        """
        Método principal do serviço. Gera o diagnóstico completo.

        Returns:
            dict: Dicionário com todas as métricas de produtividade.
                  Retorna um diagnóstico vazio se não houver registros.

        @classmethod: pode ser chamado sem instanciar a classe.
        DiagnosticoService.gerar() em vez de DiagnosticoService().gerar()
        """
        queryset = RegistroFoco.objects.all()
        total = queryset.count()

        # Caso especial: sem dados ainda
        if total == 0:
            return cls._diagnostico_vazio()

        # Calculamos tudo de uma vez com aggregate() — UMA query ao banco
        # Mais eficiente do que queries separadas para cada métrica
        agregados = queryset.aggregate(
            media_foco=Avg('nivel_foco'),
            tempo_total=Sum('tempo_minutos'),
        )

        media = round(agregados['media_foco'], 2)
        tempo_total = agregados['tempo_total'] or 0

        # Distribuição dos níveis de foco (quantos registros em cada nível)
        distribuicao_niveis = cls._calcular_distribuicao_niveis(queryset)

        # Distribuição das categorias
        distribuicao_categorias = cls._calcular_distribuicao_categorias(queryset)

        # Análises derivadas
        nivel_predominante = cls._nivel_predominante(distribuicao_niveis)
        categoria_predominante = cls._categoria_predominante(distribuicao_categorias)
        feedback = cls._gerar_feedback(media)
        pontuacao = cls._calcular_pontuacao(media, tempo_total, total)
        dicas = cls._selecionar_dicas(feedback['nivel'])
        periodo = cls._calcular_periodo(queryset)

        return {
            'total_registros': total,
            'media_nivel_foco': media,
            'tempo_total_minutos': tempo_total,
            'tempo_total_formatado': cls._formatar_tempo(tempo_total),
            'nivel_predominante': nivel_predominante,
            'categoria_mais_frequente': categoria_predominante,
            'message_feedback': feedback['mensagem'],
            'pontuacao_produtividade': pontuacao,
            'distribuicao_niveis': distribuicao_niveis,
            'distribuicao_categorias': distribuicao_categorias,
            'periodo': periodo,
            'dicas': dicas,
        }

    # =========================================================================
    # MÉTODOS AUXILIARES PRIVADOS
    # =========================================================================
    # Convenção: prefixo _ indica método interno, não deve ser chamado de fora.

    @classmethod
    def _calcular_distribuicao_niveis(cls, queryset):
        """
        Retorna quantos registros existem para cada nível de foco.
        Ex: {1: 2, 2: 0, 3: 5, 4: 8, 5: 3}
        """
        # values('nivel_foco') agrupa por nível
        # annotate(Count) conta quantos registros em cada grupo
        contagem_raw = (
            queryset
            .values('nivel_foco')
            .annotate(total=Count('id'))
            .order_by('nivel_foco')
        )

        # Garantimos que todos os níveis (1-5) aparecem, mesmo com contagem 0
        distribuicao = {str(nivel): 0 for nivel in range(1, 6)}
        for item in contagem_raw:
            distribuicao[str(item['nivel_foco'])] = item['total']

        return distribuicao

    @classmethod
    def _calcular_distribuicao_categorias(cls, queryset):
        """Retorna contagem de registros por categoria."""
        contagem_raw = (
            queryset
            .values('categoria')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        return {item['categoria']: item['total'] for item in contagem_raw}

    @classmethod
    def _nivel_predominante(cls, distribuicao):
        """Retorna o nível de foco mais comum nos registros."""
        if not distribuicao:
            return 'N/A'
        nivel = max(distribuicao, key=distribuicao.get)
        descricoes = {
            '1': 'Muito distraído', '2': 'Pouco focado',
            '3': 'Foco moderado',   '4': 'Bem focado',
            '5': 'Estado de flow',
        }
        return f'Nível {nivel} — {descricoes.get(nivel, "")}'

    @classmethod
    def _categoria_predominante(cls, distribuicao):
        """Retorna a categoria mais frequente."""
        if not distribuicao:
            return 'N/A'
        categoria_key = max(distribuicao, key=distribuicao.get)
        # get_<campo>_display() retorna o label legível do choice
        labels = dict(RegistroFoco.Categoria.choices)
        return labels.get(categoria_key, categoria_key)

    @classmethod
    def _gerar_feedback(cls, media):
        """
        Seleciona a mensagem de feedback baseada na média de foco.
        Percorre os ranges e retorna o primeiro que contém a média.
        """
        for min_val, max_val, feedback in cls.FEEDBACK_RANGES:
            if min_val <= media < max_val:
                return feedback
        # Fallback (não deve acontecer, mas defensive programming)
        return cls.FEEDBACK_RANGES[-1][2]

    @classmethod
    def _calcular_pontuacao(cls, media, tempo_total, total_registros):
        """
        Calcula uma pontuação de produtividade de 0 a 100.

        Fórmula:
          - 60% do peso vem da média de foco (normalizada para 0-60)
          - 40% vem da consistência (quantidade de registros, cap em 20)

        Retorna: float arredondado em 1 casa decimal
        """
        # Componente 1: qualidade do foco (0 a 60 pontos)
        qualidade = (media / 5) * 60

        # Componente 2: consistência (0 a 40 pontos, cap em 20 registros)
        consistencia = min(total_registros, 20) * 2

        pontuacao = qualidade + consistencia
        return round(min(pontuacao, 100), 1)

    @classmethod
    def _selecionar_dicas(cls, nivel):
        """Retorna 3 dicas aleatórias para o nível de produtividade."""
        dicas = cls.DICAS_POR_NIVEL.get(nivel, cls.DICAS_POR_NIVEL['moderado'])
        # Retornamos as 3 primeiras dicas (poderíamos randomizar)
        return dicas[:3]

    @classmethod
    def _formatar_tempo(cls, minutos):
        """Converte minutos totais em string legível. Ex: 150 → '2h 30min'"""
        if minutos == 0:
            return '0 min'
        horas = minutos // 60
        mins = minutos % 60
        if horas > 0:
            return f'{horas}h {mins}min' if mins > 0 else f'{horas}h'
        return f'{mins}min'

    @classmethod
    def _calcular_periodo(cls, queryset):
        """Retorna informações sobre o período coberto pelos registros."""
        from django.db.models import Min, Max
        datas = queryset.aggregate(
            primeiro=Min('data_criacao'),
            ultimo=Max('data_criacao'),
        )

        def fmt(dt):
            return dt.strftime('%d/%m/%Y %H:%M') if dt else None

        return {
            'primeiro_registro': fmt(datas['primeiro']),
            'ultimo_registro': fmt(datas['ultimo']),
        }

    @classmethod
    def _diagnostico_vazio(cls):
        """Resposta padrão quando não há registros cadastrados."""
        return {
            'total_registros': 0,
            'media_nivel_foco': 0.0,
            'tempo_total_minutos': 0,
            'tempo_total_formatado': '0 min',
            'nivel_predominante': 'N/A',
            'categoria_mais_frequente': 'N/A',
            'message_feedback': (
                'Nenhum registro encontrado. '
                'Comece a registrar suas sessões de trabalho para receber um diagnóstico!'
            ),
            'pontuacao_produtividade': 0.0,
            'distribuicao_niveis': {str(i): 0 for i in range(1, 6)},
            'distribuicao_categorias': {},
            'periodo': {'primeiro_registro': None, 'ultimo_registro': None},
            'dicas': [
                'Registre pelo menos uma sessão de trabalho para começar.',
                'Use a API POST /api/v1/registro-foco para criar seu primeiro registro.',
            ],
        }
