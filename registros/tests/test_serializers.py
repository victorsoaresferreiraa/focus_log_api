"""
=============================================================================
TESTES DOS SERIALIZERS — Focus Log API
=============================================================================

Testamos as validações dos serializers sem fazer requisições HTTP.
Mais rápido e mais focado que testes de integração.
=============================================================================
"""

from django.test import TestCase
from registros.serializers import RegistroFocoSerializer


class RegistroFocoSerializerTest(TestCase):
    """Testes de validação do RegistroFocoSerializer."""

    def _dados_validos(self, **kwargs):
        """Helper: retorna dados válidos, podendo sobrescrever campos."""
        base = {
            'nivel_foco': 4,
            'tempo_minutos': 60,
            'comentario': 'Sessão de coding produtiva.',
            'categoria': 'coding',
            'tags': ['backend', 'api'],
        }
        base.update(kwargs)
        return base

    def test_dados_validos_sao_aceitos(self):
        """Dados corretos devem passar na validação."""
        serializer = RegistroFocoSerializer(data=self._dados_validos())
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_nivel_foco_menor_que_1_rejeitado(self):
        """Nível 0 deve ser rejeitado."""
        serializer = RegistroFocoSerializer(data=self._dados_validos(nivel_foco=0))
        self.assertFalse(serializer.is_valid())
        self.assertIn('nivel_foco', serializer.errors)

    def test_nivel_foco_maior_que_5_rejeitado(self):
        """Nível 6 deve ser rejeitado."""
        serializer = RegistroFocoSerializer(data=self._dados_validos(nivel_foco=6))
        self.assertFalse(serializer.is_valid())
        self.assertIn('nivel_foco', serializer.errors)

    def test_nivel_foco_string_rejeitada(self):
        """String no lugar de inteiro deve ser rejeitada."""
        serializer = RegistroFocoSerializer(data=self._dados_validos(nivel_foco='alto'))
        self.assertFalse(serializer.is_valid())
        self.assertIn('nivel_foco', serializer.errors)

    def test_tempo_negativo_rejeitado(self):
        """Tempo negativo deve ser rejeitado."""
        serializer = RegistroFocoSerializer(data=self._dados_validos(tempo_minutos=-10))
        self.assertFalse(serializer.is_valid())
        self.assertIn('tempo_minutos', serializer.errors)

    def test_tempo_zero_rejeitado(self):
        """Tempo zero deve ser rejeitado."""
        serializer = RegistroFocoSerializer(data=self._dados_validos(tempo_minutos=0))
        self.assertFalse(serializer.is_valid())
        self.assertIn('tempo_minutos', serializer.errors)

    def test_tempo_acima_de_1440_rejeitado(self):
        """Mais de 24 horas deve ser rejeitado."""
        serializer = RegistroFocoSerializer(data=self._dados_validos(tempo_minutos=1441))
        self.assertFalse(serializer.is_valid())
        self.assertIn('tempo_minutos', serializer.errors)

    def test_comentario_vazio_rejeitado(self):
        """Comentário vazio deve ser rejeitado."""
        serializer = RegistroFocoSerializer(data=self._dados_validos(comentario=''))
        self.assertFalse(serializer.is_valid())
        self.assertIn('comentario', serializer.errors)

    def test_comentario_apenas_espacos_rejeitado(self):
        """Comentário com só espaços deve ser rejeitado."""
        serializer = RegistroFocoSerializer(data=self._dados_validos(comentario='   '))
        self.assertFalse(serializer.is_valid())
        self.assertIn('comentario', serializer.errors)

    def test_tags_invalidas_rejeitadas(self):
        """Tags que não são lista devem ser rejeitadas."""
        serializer = RegistroFocoSerializer(data=self._dados_validos(tags='backend'))
        self.assertFalse(serializer.is_valid())
        self.assertIn('tags', serializer.errors)

    def test_tags_com_numeros_rejeitadas(self):
        """Tags com números (não strings) devem ser rejeitadas."""
        serializer = RegistroFocoSerializer(data=self._dados_validos(tags=[1, 2, 3]))
        self.assertFalse(serializer.is_valid())
        self.assertIn('tags', serializer.errors)

    def test_tags_duplicadas_sao_removidas(self):
        """Tags duplicadas devem ser removidas automaticamente."""
        serializer = RegistroFocoSerializer(
            data=self._dados_validos(tags=['backend', 'backend', 'api'])
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['tags'], ['backend', 'api'])

    def test_campos_obrigatorios_ausentes(self):
        """Campos obrigatórios ausentes devem gerar erro."""
        serializer = RegistroFocoSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('nivel_foco', serializer.errors)
        self.assertIn('tempo_minutos', serializer.errors)
        self.assertIn('comentario', serializer.errors)

    def test_nivel_5_tempo_muito_curto_rejeitado(self):
        """Nível 5 com menos de 10 minutos deve ser rejeitado (validação cruzada)."""
        serializer = RegistroFocoSerializer(
            data=self._dados_validos(nivel_foco=5, tempo_minutos=5)
        )
        self.assertFalse(serializer.is_valid())
