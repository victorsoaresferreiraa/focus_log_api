"""
=============================================================================
TRATAMENTO DE EXCEÇÕES CUSTOMIZADO — Focus Log API
=============================================================================

Por padrão, o DRF retorna erros em formatos inconsistentes.
Ex: erros de validação têm um formato, erros 404 têm outro.

Nosso handler padroniza TODOS os erros da API no mesmo formato:
{
    "sucesso": false,
    "erro": {
        "tipo": "ValidationError",
        "mensagem": "Dados inválidos",
        "detalhes": { "campo": ["mensagem de erro"] }
    }
}

Isso facilita muito para o frontend tratar erros de forma uniforme.
=============================================================================
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

# Logger para registrar erros não tratados
# Em produção, esses logs vão para sistemas como Sentry, Datadog, etc.
logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Handler customizado de exceções para a API.

    Parâmetros:
        exc: A exceção que foi lançada
        context: Contexto da request (view, request object, etc.)

    Retorna:
        Response com formato padronizado de erro, ou None se o DRF
        não souber tratar (aí o Django assume e retorna 500).
    """
    # Primeiro, deixamos o handler padrão do DRF processar
    response = exception_handler(exc, context)

    if response is not None:
        # O DRF conhece esse tipo de erro — vamos reformatar
        erro_formatado = {
            'sucesso': False,
            'erro': {
                'tipo': type(exc).__name__,
                'status_code': response.status_code,
                'detalhes': response.data,
            }
        }

        # Mensagem amigável baseada no status code
        mensagens = {
            400: 'Dados inválidos. Verifique os campos enviados.',
            401: 'Autenticação necessária.',
            403: 'Você não tem permissão para esta ação.',
            404: 'Recurso não encontrado.',
            405: 'Método HTTP não permitido para este endpoint.',
            429: 'Muitas requisições. Aguarde um momento.',
        }
        erro_formatado['erro']['mensagem'] = mensagens.get(
            response.status_code,
            'Ocorreu um erro ao processar a requisição.'
        )

        response.data = erro_formatado
    else:
        # Erro não tratado pelo DRF (ex: erros 500, bugs no código)
        # Logamos para investigação futura
        logger.error(
            f'Exceção não tratada: {type(exc).__name__}: {exc}',
            exc_info=True,
            extra={'context': str(context)}
        )

    return response
