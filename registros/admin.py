"""
=============================================================================
ADMIN — Focus Log API
=============================================================================

O Django Admin é uma interface web gerada automaticamente para
gerenciar os dados da aplicação.

Acesse em: http://localhost:8000/admin/
(Crie um superusuário com: python manage.py createsuperuser)

Aqui configuramos como os dados aparecem e podem ser filtrados no admin.
=============================================================================
"""

from django.contrib import admin
from .models import RegistroFoco


@admin.register(RegistroFoco)
class RegistroFocoAdmin(admin.ModelAdmin):
    """Configuração do model RegistroFoco no painel admin."""

    # Colunas exibidas na listagem
    list_display = [
        'id',
        'nivel_foco',
        'nivel_descricao_display',
        'tempo_formatado_display',
        'categoria',
        'data_criacao',
    ]

    # Filtros na barra lateral direita
    list_filter = ['nivel_foco', 'categoria', 'data_criacao']

    # Campo de busca
    search_fields = ['comentario', 'tags']

    # Campos somente leitura (não editáveis via admin)
    readonly_fields = ['data_criacao', 'data_atualizacao']

    # Ordenação padrão na listagem
    ordering = ['-data_criacao']

    # Quantidade de registros por página
    list_per_page = 25

    # Organização dos campos no formulário de edição
    fieldsets = (
        ('Dados Principais', {
            'fields': ('nivel_foco', 'tempo_minutos', 'comentario')
        }),
        ('Categorização', {
            'fields': ('categoria', 'tags'),
            'classes': ('collapse',),  # Seção colapsável
        }),
        ('Metadados', {
            'fields': ('data_criacao', 'data_atualizacao'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Nível')
    def nivel_descricao_display(self, obj):
        return obj.nivel_descricao

    @admin.display(description='Duração')
    def tempo_formatado_display(self, obj):
        return obj.tempo_formatado
