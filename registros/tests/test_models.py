"""
=============================================================================
TESTES DO MODEL — Focus Log API
=============================================================================

Testamos o model RegistroFoco isoladamente, sem HTTP.

Boas práticas de teste:
  - Cada teste testa UMA coisa específica
  - Nome do teste descreve o comportamento testado
  - Arrange (prepara) → Act (executa) → Assert (verifica)
  - Testes devem ser independentes entre si
=============================================================================
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from registros.models import RegistroFoco


class RegistroFocoModelTest(TestCase):
    """Testes unitários para o model RegistroFoco."""

    def setUp(self):
        """
        setUp: executado antes de CADA teste.
        Cria um registro padrão que cada teste pode usar.
        """
        self.registro_valido = RegistroFoco.objects.create(
            nivel_foco=4,
            tempo_minutos=90,
            comentario='Implementei a autenticação JWT com testes unitários.',
            categoria=RegistroFoco.Categoria.CODING,
            tags=['backend', 'jwt', 'testes'],
        )

    def test_criacao_registro_valido(self):
        """Verifica que um registro válido é criado com sucesso."""
        self.assertIsNotNone(self.registro_valido.id)
        self.assertEqual(self.registro_valido.nivel_foco, 4)
        self.assertEqual(self.registro_valido.tempo_minutos, 90)
        self.assertIsNotNone(self.registro_valido.data_criacao)

    def test_str_representation(self):
        """Verifica a representação textual do objeto."""
        str_repr = str(self.registro_valido)
        self.assertIn('4⭐', str_repr)
        self.assertIn('90 min', str_repr)

    def test_nivel_descricao_property(self):
        """Testa a propriedade nivel_descricao para cada nível."""
        descricoes_esperadas = {
            1: 'Muito distraído',
            2: 'Pouco focado',
            3: 'Foco moderado',
            4: 'Bem focado',
            5: 'Estado de flow',
        }
        for nivel, descricao in descricoes_esperadas.items():
            registro = RegistroFoco(nivel_foco=nivel, tempo_minutos=30, comentario='teste')
            self.assertEqual(registro.nivel_descricao, descricao)

    def test_tempo_formatado_horas_e_minutos(self):
        """Testa formatação de tempo quando há horas e minutos."""
        registro = RegistroFoco(nivel_foco=3, tempo_minutos=90, comentario='teste')
        self.assertEqual(registro.tempo_formatado, '1h 30min')

    def test_tempo_formatado_apenas_horas(self):
        """Testa formatação quando são horas exatas."""
        registro = RegistroFoco(nivel_foco=3, tempo_minutos=120, comentario='teste')
        self.assertEqual(registro.tempo_formatado, '2h')

    def test_tempo_formatado_apenas_minutos(self):
        """Testa formatação quando são menos de 60 minutos."""
        registro = RegistroFoco(nivel_foco=3, tempo_minutos=45, comentario='teste')
        self.assertEqual(registro.tempo_formatado, '45min')

    def test_tags_default_lista_vazia(self):
        """Verifica que tags tem lista vazia como padrão."""
        registro = RegistroFoco.objects.create(
            nivel_foco=3,
            tempo_minutos=30,
            comentario='Sem tags',
        )
        self.assertEqual(registro.tags, [])

    def test_ordering_mais_recentes_primeiro(self):
        """Verifica que os registros são ordenados do mais recente para o mais antigo."""
        RegistroFoco.objects.create(nivel_foco=2, tempo_minutos=30, comentario='Segundo')
        registros = RegistroFoco.objects.all()
        # O mais recente deve ser o primeiro
        self.assertGreaterEqual(
            registros[0].data_criacao,
            registros[1].data_criacao
        )
