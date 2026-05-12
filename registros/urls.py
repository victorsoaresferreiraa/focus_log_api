"""
=============================================================================
URLs DO APP REGISTROS — Focus Log API
=============================================================================

Mapeamento dos endpoints deste app.

Boa prática: nomes de URL (`name=`) permitem referenciar URLs sem
hardcodar o caminho. Se o caminho mudar, o código continua funcionando.

Ex: reverse('registros:registro-foco') → '/api/v1/registro-foco'
=============================================================================
"""

from django.urls import path
from .views import RegistroFocoView, DiagnosticoView

# app_name define o namespace deste app
# Usado junto com o namespace no include() do core/urls.py
app_name = 'registros'

urlpatterns = [
    # POST /api/v1/registro-foco → criar novo registro
    # GET  /api/v1/registro-foco → listar todos os registros
    path('registro-foco', RegistroFocoView.as_view(), name='registro-foco'),

    # GET /api/v1/diagnostico-produtividade → retornar diagnóstico
    path('diagnostico-produtividade', DiagnosticoView.as_view(), name='diagnostico'),
]
