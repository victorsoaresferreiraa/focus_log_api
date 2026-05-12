"""
=============================================================================
TESTES DAS VIEWS (Integração) — Focus Log API
=============================================================================

Testes de integração simulam requisições HTTP reais.
O Django TestCase inclui um `client` que faz requests sem servidor.

Esses testes cobrem o fluxo completo: request → view → serializer → banco.
=============================================================================
"""

import json
from django.test import TestCase
from django.urls import reverse
from registros.models import RegistroFoco


class RegistroFocoViewTest(TestCase):
    """Testes do endpoint POST /api/v1/registro-foco."""

    def setUp(self):
        """URL do endpoint para reutilização nos testes."""
        self.url = reverse('registros:registro-foco')
        self.headers = {'content_type': 'application/json'}

    def _post(self, dados):
        """Helper para fazer POST com JSON."""
        return self.client.post(
            self.url,
            data=json.dumps(dados),
            content_type='application/json',
        )

    def test_criar_registro_minimo_retorna_201(self):
        """POST com campos mínimos obrigatórios deve retornar 201."""
        dados = {
            'nivel_foco': 3,
            'tempo_minutos': 45,
            'comentario': 'Estudei Python e Django REST Framework.',
        }
        response = self._post(dados)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['sucesso'])

    def test_criar_registro_completo_retorna_201(self):
        """POST com todos os campos deve criar o registro corretamente."""
        dados = {
            'nivel_foco': 5,
            'tempo_minutos': 120,
            'comentario': 'Implementei a API completa com testes.',
            'categoria': 'coding',
            'tags': ['django', 'drf', 'testes'],
        }
        response = self._post(dados)
        self.assertEqual(response.status_code, 201)
        dados_resposta = response.json()['dados']
        self.assertEqual(dados_resposta['nivel_foco'], 5)
        self.assertEqual(dados_resposta['nivel_descricao'], 'Estado de flow')
        self.assertEqual(dados_resposta['tempo_formatado'], '2h')

    def test_nivel_invalido_retorna_400(self):
        """nivel_foco fora do range deve retornar 400."""
        response = self._post({'nivel_foco': 10, 'tempo_minutos': 30, 'comentario': 'Teste'})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['sucesso'])

    def test_campos_ausentes_retorna_400(self):
        """Request sem campos obrigatórios deve retornar 400."""
        response = self._post({})
        self.assertEqual(response.status_code, 400)
        erros = response.json()['erro']['detalhes']
        self.assertIn('nivel_foco', erros)
        self.assertIn('tempo_minutos', erros)
        self.assertIn('comentario', erros)

    def test_body_nao_json_retorna_400(self):
        """Body que não é JSON deve retornar 400."""
        response = self.client.post(
            self.url,
            data='isso nao e json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_registro_persistido_no_banco(self):
        """Verifica que o registro realmente foi salvo no banco."""
        self._post({
            'nivel_foco': 4,
            'tempo_minutos': 60,
            'comentario': 'Sessão de revisão de código.',
        })
        self.assertEqual(RegistroFoco.objects.count(), 1)
        registro = RegistroFoco.objects.first()
        self.assertEqual(registro.nivel_foco, 4)

    def test_get_lista_registros(self):
        """GET deve retornar lista de registros."""
        RegistroFoco.objects.create(nivel_foco=3, tempo_minutos=30, comentario='Registro 1')
        RegistroFoco.objects.create(nivel_foco=5, tempo_minutos=90, comentario='Registro 2')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['total'], 2)


class DiagnosticoViewTest(TestCase):
    """Testes do endpoint GET /api/v1/diagnostico-produtividade."""

    def setUp(self):
        self.url = reverse('registros:diagnostico')

    def test_diagnostico_sem_registros(self):
        """Sem registros, deve retornar diagnóstico vazio com mensagem."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        diag = response.json()['diagnostico']
        self.assertEqual(diag['total_registros'], 0)
        self.assertEqual(diag['media_nivel_foco'], 0.0)

    def test_diagnostico_com_registros(self):
        """Com registros, deve calcular métricas corretamente."""
        RegistroFoco.objects.create(nivel_foco=4, tempo_minutos=60, comentario='Primeiro')
        RegistroFoco.objects.create(nivel_foco=2, tempo_minutos=30, comentario='Segundo')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        diag = response.json()['diagnostico']
        self.assertEqual(diag['total_registros'], 2)
        self.assertEqual(diag['media_nivel_foco'], 3.0)
        self.assertEqual(diag['tempo_total_minutos'], 90)
        self.assertEqual(diag['tempo_total_formatado'], '1h 30min')

    def test_diagnostico_tem_campos_obrigatorios(self):
        """A resposta deve ter todos os campos esperados."""
        response = self.client.get(self.url)
        diag = response.json()['diagnostico']
        campos_esperados = [
            'total_registros', 'media_nivel_foco', 'tempo_total_minutos',
            'tempo_total_formatado', 'message_feedback', 'pontuacao_produtividade',
            'distribuicao_niveis', 'dicas', 'periodo',
        ]
        for campo in campos_esperados:
            self.assertIn(campo, diag, f'Campo "{campo}" ausente no diagnóstico')

    def test_media_alta_gera_feedback_positivo(self):
        """Média acima de 4.5 deve gerar feedback de alto nível."""
        for _ in range(5):
            RegistroFoco.objects.create(nivel_foco=5, tempo_minutos=90, comentario='Flow')
        response = self.client.get(self.url)
        feedback = response.json()['diagnostico']['message_feedback']
        self.assertIn('maratona produtiva', feedback)

    def test_media_baixa_gera_feedback_de_melhoria(self):
        """Média abaixo de 2.5 deve gerar feedback construtivo."""
        for _ in range(5):
            RegistroFoco.objects.create(nivel_foco=1, tempo_minutos=20, comentario='Distração')
        response = self.client.get(self.url)
        feedback = response.json()['diagnostico']['message_feedback']
        self.assertIn('concentração', feedback)
