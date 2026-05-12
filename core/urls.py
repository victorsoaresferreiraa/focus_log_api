"""
=============================================================================
URLs PRINCIPAIS DO PROJETO — Focus Log API
=============================================================================

Este é o "mapa de rotas" central da aplicação.
Toda requisição HTTP chega aqui primeiro, e este arquivo decide
para qual app encaminhar.

Padrão utilizado: incluir as URLs de cada app com `include()`.
Isso mantém cada app independente e organizado.

Conceito "namespace": o `app_name` nos permite referenciar URLs
pelo nome em vez do caminho. Ex: reverse('registros:registro-foco')
=============================================================================
"""

from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    # Interface administrativa do Django — útil para inspecionar dados
    path('admin/', admin.site.urls),

    # Todos os endpoints da nossa API ficam sob /api/v1/
    # O prefixo /api/v1/ é uma boa prática: permite versionar a API no futuro.
    # Ex: quando precisarmos quebrar compatibilidade, criamos /api/v2/
    path('api/v1/', include('registros.urls', namespace='registros')),
]
