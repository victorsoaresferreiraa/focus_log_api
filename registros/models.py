"""
=============================================================================
MODELOS DE DADOS — Focus Log API
=============================================================================

Os models são a camada de dados da aplicação. Cada classe Model
representa uma tabela no banco de dados.

O Django ORM (Object-Relational Mapper) converte automaticamente
nossas classes Python em tabelas SQL. Nunca precisamos escrever
SQL manual para operações básicas.

Fluxo: Model (Python) → Migration (SQL) → Banco de dados
=============================================================================
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class RegistroFoco(models.Model):
    """
    Modelo que representa um bloco de trabalho/estudo registrado.

    Cada instância deste model = uma linha na tabela `registros_registrofoco`
    no banco de dados SQLite.

    Campos obrigatórios do desafio: nivel_foco, tempo_minutos, comentario
    Campos extras (diferencial): categoria, tags, data_criacao
    """

    # =========================================================================
    # CONSTANTES — Escolhas válidas para campos com opções fixas
    # =========================================================================
    # Padrão Django: definir choices como constantes de classe.
    # Vantagem: autocompletar no editor, fácil de manter, evita typos.

    class Categoria(models.TextChoices):
        """
        Categorias possíveis para um bloco de trabalho.
        Formato: (valor_no_banco, 'Label legível para humanos')
        """
        CODING = 'coding', 'Programação'
        REUNIAO = 'reuniao', 'Reunião'
        ESTUDO = 'estudo', 'Estudo'
        ESCRITA = 'escrita', 'Escrita/Documentação'
        REVISAO = 'revisao', 'Revisão de Código'
        OUTRO = 'outro', 'Outro'

    # =========================================================================
    # CAMPOS DO MODEL
    # =========================================================================

    # IntegerField: inteiro simples.
    # validators: lista de funções que validam o valor antes de salvar.
    # MinValueValidator(1) → rejeita valores menores que 1
    # MaxValueValidator(5) → rejeita valores maiores que 5
    nivel_foco = models.IntegerField(
        verbose_name='Nível de Foco',
        help_text='Nível de 1 (muito distraído) a 5 (estado de flow)',
        validators=[
            MinValueValidator(1, message='O nível mínimo de foco é 1.'),
            MaxValueValidator(5, message='O nível máximo de foco é 5.'),
        ],
    )

    # PositiveIntegerField: inteiro que só aceita valores > 0
    # Perfeito para duração em minutos — não faz sentido ter minutos negativos!
    tempo_minutos = models.PositiveIntegerField(
        verbose_name='Duração (minutos)',
        help_text='Quantidade de minutos que durou a sessão de trabalho',
    )

    # TextField: texto de tamanho ilimitado (ao contrário do CharField que tem max_length)
    # Ideal para comentários e descrições longas.
    comentario = models.TextField(
        verbose_name='Comentário',
        help_text='Descreva o que foi feito ou o que causou distração',
    )

    # CharField com choices: armazena uma das opções definidas em Categoria
    # default: valor padrão quando o campo não é informado
    categoria = models.CharField(
        verbose_name='Categoria',
        max_length=20,
        choices=Categoria.choices,
        default=Categoria.OUTRO,
        help_text='Tipo de atividade realizada',
    )

    # JSONField: armazena listas/dicionários diretamente no banco.
    # Usamos para as tags — uma lista de strings como ["foco", "backend", "sprint"]
    # blank=True → permite que seja vazio na validação do form
    # null=True  → permite NULL no banco de dados
    # default=list → cria uma lista vazia [] por padrão (NUNCA use default=[])
    tags = models.JSONField(
        verbose_name='Tags',
        blank=True,
        null=True,
        default=list,
        help_text='Lista de tags para categorizar a sessão. Ex: ["sprint", "bug-fix"]',
    )

    # DateTimeField com auto_now_add=True:
    # Preenchido AUTOMATICAMENTE com a data/hora atual quando o registro é CRIADO.
    # Não pode ser modificado depois — perfeito para "created_at".
    data_criacao = models.DateTimeField(
        verbose_name='Criado em',
        auto_now_add=True,
    )

    # DateTimeField com auto_now=True:
    # Atualizado AUTOMATICAMENTE toda vez que o registro é SALVO.
    # Perfeito para "updated_at".
    data_atualizacao = models.DateTimeField(
        verbose_name='Atualizado em',
        auto_now=True,
    )

    # =========================================================================
    # METADADOS DO MODEL
    # =========================================================================

    class Meta:
        # Nome legível no admin
        verbose_name = 'Registro de Foco'
        verbose_name_plural = 'Registros de Foco'

        # Ordenação padrão: mais recentes primeiro (- = decrescente)
        ordering = ['-data_criacao']

        # Índices de banco de dados para acelerar consultas frequentes
        # O Django cria esses índices automaticamente durante as migrations
        indexes = [
            models.Index(fields=['data_criacao'], name='idx_data_criacao'),
            models.Index(fields=['nivel_foco'], name='idx_nivel_foco'),
            models.Index(fields=['categoria'], name='idx_categoria'),
        ]

    # =========================================================================
    # MÉTODOS DO MODEL
    # =========================================================================

    def __str__(self):
        """
        Representação textual do objeto. Aparece no admin e no shell.
        Ex: "[5⭐] Coding — 90 min (12/05/2025 10:30)"
        """
        return (
            f'[{self.nivel_foco}⭐] {self.get_categoria_display()} '
            f'— {self.tempo_minutos} min '
            f'({self.data_criacao.strftime("%d/%m/%Y %H:%M") if self.data_criacao else "sem data"})'
        )

    @property
    def nivel_descricao(self):
        """
        Propriedade calculada: retorna uma descrição textual do nível de foco.
        @property → acessado como atributo, não como método: registro.nivel_descricao
        """
        descricoes = {
            1: 'Muito distraído',
            2: 'Pouco focado',
            3: 'Foco moderado',
            4: 'Bem focado',
            5: 'Estado de flow',
        }
        return descricoes.get(self.nivel_foco, 'Desconhecido')

    @property
    def tempo_formatado(self):
        """Converte minutos em formato legível: 90 min → '1h 30min'"""
        horas = self.tempo_minutos // 60
        minutos = self.tempo_minutos % 60
        if horas > 0:
            return f'{horas}h {minutos}min' if minutos > 0 else f'{horas}h'
        return f'{minutos}min'
