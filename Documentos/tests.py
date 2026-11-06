from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Usuario, Carona


class ListarUsuariosTest(TestCase):
    def test_pagina_abre(self):
        resposta = self.client.get(reverse("listar_usuarios"))
        self.assertEqual(resposta.status_code, 200)

    def test_mostra_mensagem_quando_nao_ha_usuarios(self):
        resposta = self.client.get(reverse("listar_usuarios"))
        self.assertContains(resposta, "Nenhum usuário cadastrado")

    def test_mostra_usuario_cadastrado(self):
        Usuario.objects.create(nome="Ana", username="ana", email="ana@aluno.puc-rio.br")
        resposta = self.client.get(reverse("listar_usuarios"))
        self.assertContains(resposta, "Ana")


class DetalhesCaronaTest(TestCase):
    def setUp(self):
        motorista = Usuario.objects.create(
            nome="Bruno", username="bruno", email="bruno@aluno.puc-rio.br"
        )
        self.carona = Carona.objects.create(
            origem="Campus",
            destino="Centro",
            horario=timezone.now(),
            vagas=3,
            motorista=motorista,
        )

    def test_pagina_abre(self):
        url = reverse("detalhes_carona", args=[self.carona.id])
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, 200)

    def test_mostra_dados_da_carona(self):
        url = reverse("detalhes_carona", args=[self.carona.id])
        resposta = self.client.get(url)
        self.assertContains(resposta, "Campus")
        self.assertContains(resposta, "Centro")
        self.assertContains(resposta, "Bruno")

    def test_carona_inexistente_da_404(self):
        url = reverse("detalhes_carona", args=[9999])
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, 404)


class ComoFuncionaTest(TestCase):
    def test_pagina_abre(self):
        resposta = self.client.get(reverse("como_funciona"))
        self.assertEqual(resposta.status_code, 200)
