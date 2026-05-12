"""
=============================================================================
VIEWS — Focus Log API
=============================================================================

As views são o ponto de entrada das requisições HTTP.
Elas recebem o request, orquestram o trabalho (serializer + service)
e retornam uma response.

Princípio: views devem ser FINAS. Lógica de negócio vai em services.
A view só sabe: "recebi dados, validei, salvei, respondi".

Estrutura de cada view:
  1. Recebe o request
  2. Serializer valida os dados de entrada
  3. Service executa a lógica
  4. Retorna Response com os dados serializados
=============================================================================
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import RegistroFoco
from .serializers import RegistroFocoSerializer, DiagnosticoSerializer
from .services import DiagnosticoService


class RegistroFocoView(APIView):
    """
    Endpoint: POST /api/v1/registro-foco

    Responsabilidade: Receber e salvar um novo bloco de trabalho.

    APIView: classe base do DRF para views baseadas em classes.
    Cada método HTTP (get, post, put, delete) é um método da classe.
    """

    def post(self, request):
        """
        Cria um novo registro de foco.

        Fluxo:
        1. Instancia o serializer com os dados do request
        2. Valida (chama validate_<campo> e validate)
        3. Se válido → salva no banco e retorna 201 Created
        4. Se inválido → retorna 400 com os erros de validação

        HTTP 201 Created: padrão REST para criação bem-sucedida de recurso.
        """
        # request.data: corpo da requisição já parseado para dict Python
        serializer = RegistroFocoSerializer(data=request.data)

        if serializer.is_valid():
            # is_valid() executou todas as validações — dados limpos e válidos
            # save() chama o create() do serializer, que salva no banco
            registro = serializer.save()

            # Serializamos de volta para retornar ao cliente com os campos extras
            # (incluindo id, data_criacao, nivel_descricao, etc.)
            resposta = {
                'sucesso': True,
                'mensagem': 'Registro de foco criado com sucesso!',
                'dados': RegistroFocoSerializer(registro).data,
            }
            return Response(resposta, status=status.HTTP_201_CREATED)

        # Dados inválidos — retornamos os erros de validação
        return Response(
            {
                'sucesso': False,
                'erro': {
                    'mensagem': 'Dados inválidos. Verifique os campos.',
                    'detalhes': serializer.errors,
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get(self, request):
        """
        Lista todos os registros de foco.

        Endpoint: GET /api/v1/registro-foco

        Parâmetros de query opcionais:
          ?categoria=coding  → filtra por categoria
          ?nivel_foco=5      → filtra por nível
          ?limit=10          → limita resultados (padrão: 50)
        """
        queryset = RegistroFoco.objects.all()

        # Filtros opcionais via query params (ex: ?categoria=coding)
        categoria = request.query_params.get('categoria')
        nivel_foco = request.query_params.get('nivel_foco')
        limit = request.query_params.get('limit', 50)

        if categoria:
            queryset = queryset.filter(categoria=categoria)

        if nivel_foco:
            try:
                nivel_foco = int(nivel_foco)
                if 1 <= nivel_foco <= 5:
                    queryset = queryset.filter(nivel_foco=nivel_foco)
            except ValueError:
                pass  # Ignora filtro inválido silenciosamente

        try:
            limit = min(int(limit), 100)  # Máximo de 100 registros por request
        except (ValueError, TypeError):
            limit = 50

        queryset = queryset[:limit]

        serializer = RegistroFocoSerializer(queryset, many=True)
        return Response({
            'sucesso': True,
            'total': len(serializer.data),
            'dados': serializer.data,
        })


class DiagnosticoView(APIView):
    """
    Endpoint: GET /api/v1/diagnostico-produtividade

    Responsabilidade: Calcular e retornar o diagnóstico completo
    baseado em todos os registros existentes.

    A view apenas chama o service e retorna o resultado.
    Toda a lógica de cálculo está em DiagnosticoService.
    """

    def get(self, request):
        """
        Retorna o diagnóstico de produtividade.

        Delega o cálculo para DiagnosticoService.gerar().
        A view não sabe NADA sobre como o diagnóstico é calculado.
        """
        diagnostico_data = DiagnosticoService.gerar()

        # Validamos a saída com o serializer (garante tipos corretos)
        serializer = DiagnosticoSerializer(data=diagnostico_data)
        serializer.is_valid()  # Diagnóstico gerado pelo service sempre é válido

        return Response({
            'sucesso': True,
            'diagnostico': diagnostico_data,
        }, status=status.HTTP_200_OK)
