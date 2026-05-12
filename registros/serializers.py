"""
=============================================================================
SERIALIZERS — Focus Log API
=============================================================================

Serializers fazem duas coisas fundamentais:

1. DESERIALIZAÇÃO (entrada): Recebem JSON do cliente → validam os dados
   → convertem para objetos Python prontos para salvar no banco.

2. SERIALIZAÇÃO (saída): Pegam objetos do banco → convertem para JSON
   que será enviado ao cliente.

É aqui que ficam as regras de validação dos campos!

Analogia: o serializer é como um formulário inteligente que:
  - Define quais campos aceita
  - Valida cada campo individualmente (validate_<campo>)
  - Valida a combinação de campos (validate)
  - Sabe como salvar no banco (create/update)
=============================================================================
"""

from rest_framework import serializers
from .models import RegistroFoco


class RegistroFocoSerializer(serializers.ModelSerializer):
    """
    Serializer para criação e leitura de RegistroFoco.

    ModelSerializer: gera automaticamente os campos baseado no Model.
    Menos código, menos chance de erro, fácil de manter.
    """

    # Campos extras calculados (read_only → só aparecem na saída, nunca na entrada)
    # SerializerMethodField → chama um método get_<nome_do_campo>
    nivel_descricao = serializers.SerializerMethodField(
        help_text='Descrição textual do nível de foco'
    )
    tempo_formatado = serializers.SerializerMethodField(
        help_text='Duração em formato legível (ex: 1h 30min)'
    )

    class Meta:
        model = RegistroFoco
        fields = [
            # Campos do banco
            'id',
            'nivel_foco',
            'tempo_minutos',
            'comentario',
            'categoria',
            'tags',
            'data_criacao',
            'data_atualizacao',
            # Campos calculados (read_only)
            'nivel_descricao',
            'tempo_formatado',
        ]
        # Campos que só aparecem na resposta, nunca aceitos na entrada
        read_only_fields = ['id', 'data_criacao', 'data_atualizacao']

    # =========================================================================
    # MÉTODOS DE CAMPO CALCULADO
    # =========================================================================

    def get_nivel_descricao(self, obj):
        """
        `obj` é a instância do RegistroFoco sendo serializado.
        Chamamos a propriedade que definimos no model.
        """
        return obj.nivel_descricao

    def get_tempo_formatado(self, obj):
        """Retorna a duração em formato legível."""
        return obj.tempo_formatado

    # =========================================================================
    # VALIDAÇÕES DE CAMPOS INDIVIDUAIS
    # =========================================================================
    # Padrão DRF: métodos validate_<nome_do_campo> são chamados automaticamente.
    # Se lançar serializers.ValidationError, o DRF retorna 400 Bad Request.

    def validate_nivel_foco(self, value):
        """
        Validação do campo nivel_foco.
        `value` já é um inteiro (o DRF já fez a conversão de tipo).
        """
        # Essa validação é redundante com os validators do model,
        # mas temos aqui também para uma mensagem de erro mais clara na API.
        if not 1 <= value <= 5:
            raise serializers.ValidationError(
                f'O nível de foco deve ser entre 1 e 5. Você enviou: {value}'
            )
        return value

    def validate_tempo_minutos(self, value):
        """
        Validação do campo tempo_minutos.
        Verificamos limites razoáveis de duração.
        """
        if value <= 0:
            raise serializers.ValidationError(
                'O tempo deve ser maior que 0 minutos.'
            )
        # 24 horas = 1440 minutos — limite razoável para uma sessão
        if value > 1440:
            raise serializers.ValidationError(
                f'O tempo máximo é 1440 minutos (24 horas). Você enviou: {value} min.'
            )
        return value

    def validate_comentario(self, value):
        """
        Validação do campo comentario.
        Garantimos que não seja só espaços em branco.
        """
        # strip() remove espaços do início e fim
        comentario_limpo = value.strip()
        if not comentario_limpo:
            raise serializers.ValidationError(
                'O comentário não pode ser vazio ou conter apenas espaços.'
            )
        if len(comentario_limpo) < 5:
            raise serializers.ValidationError(
                'O comentário deve ter pelo menos 5 caracteres.'
            )
        return comentario_limpo

    def validate_tags(self, value):
        """
        Validação do campo tags.
        Tags deve ser uma lista de strings, e cada tag deve ser válida.
        """
        if value is None:
            return []

        if not isinstance(value, list):
            raise serializers.ValidationError(
                'Tags deve ser uma lista. Ex: ["backend", "sprint"]'
            )

        tags_validas = []
        for i, tag in enumerate(value):
            if not isinstance(tag, str):
                raise serializers.ValidationError(
                    f'A tag na posição {i} deve ser uma string, não {type(tag).__name__}.'
                )
            tag_limpa = tag.strip().lower()
            if not tag_limpa:
                raise serializers.ValidationError(
                    f'A tag na posição {i} está vazia.'
                )
            if len(tag_limpa) > 50:
                raise serializers.ValidationError(
                    f'A tag "{tag_limpa[:20]}..." é muito longa. Máximo 50 caracteres.'
                )
            tags_validas.append(tag_limpa)

        # Remove tags duplicadas mantendo a ordem
        return list(dict.fromkeys(tags_validas))

    # =========================================================================
    # VALIDAÇÃO CRUZADA (valida a combinação de campos)
    # =========================================================================

    def validate(self, data):
        """
        Chamado DEPOIS de todas as validate_<campo>().
        Aqui validamos regras que dependem de múltiplos campos ao mesmo tempo.
        `data` é um dicionário com todos os campos já validados individualmente.
        """
        nivel = data.get('nivel_foco')
        tempo = data.get('tempo_minutos')

        # Regra de negócio: sessões de altíssimo foco muito curtas são suspeitas
        # Um "estado de flow" (nível 5) dura tipicamente mais de 25 minutos
        if nivel == 5 and tempo is not None and tempo < 10:
            raise serializers.ValidationError({
                'non_field_errors': (
                    'Uma sessão de nível 5 (estado de flow) com menos de 10 minutos '
                    'parece inconsistente. Verifique os dados.'
                )
            })

        return data


class DiagnosticoSerializer(serializers.Serializer):
    """
    Serializer para a resposta do endpoint /diagnostico-produtividade.

    Aqui usamos Serializer (base) em vez de ModelSerializer,
    porque a resposta não é um model — é um objeto calculado.
    Este serializer é usado apenas para SAÍDA (serialização).
    """

    # Campos do diagnóstico
    total_registros = serializers.IntegerField()
    media_nivel_foco = serializers.FloatField()
    tempo_total_minutos = serializers.IntegerField()
    tempo_total_formatado = serializers.CharField()
    nivel_predominante = serializers.CharField()
    categoria_mais_frequente = serializers.CharField()
    message_feedback = serializers.CharField()
    pontuacao_produtividade = serializers.FloatField()
    distribuicao_niveis = serializers.DictField(child=serializers.IntegerField())
    distribuicao_categorias = serializers.DictField(child=serializers.IntegerField())
    periodo = serializers.DictField()
    dicas = serializers.ListField(child=serializers.CharField())
