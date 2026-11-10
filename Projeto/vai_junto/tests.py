from django.test import TestCase
from django.urls import reverse

from vai_junto.models import Instituicao, Rota, Usuario


class OferecerCaronaTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create(
            nome='Pessoa Estudante',
            email='estudante@example.com',
            matricula='12345',
            senha='hash',
        )
        self.instituicao = Instituicao.objects.create(
            nome='Universidade de Teste',
            sigla='UT',
        )
        session = self.client.session
        session['usuario_id'] = self.usuario.id_usuario
        session.save()

    def test_usuario_sem_sessao_e_redirecionado_ao_login(self):
        self.client.session.flush()

        response = self.client.get(reverse('oferecer_carona'))

        self.assertRedirects(response, reverse('login'))

    def test_publica_rota_com_dados_validos(self):
        response = self.client.post(reverse('oferecer_carona'), {
            'origem': 'Centro',
            'instituicao': str(self.instituicao.id_instituicao),
            'horario': '07:30',
            'vagas': '2',
            'transporte': 'Carro',
            'referencia': 'Estação central',
        })

        self.assertRedirects(response, reverse('rotas'))
        rota = Rota.objects.get()
        self.assertEqual(rota.origem, 'Centro')
        self.assertEqual(rota.id_usuario, self.usuario)
        self.assertEqual(rota.id_instituicao, self.instituicao)
        self.assertEqual(rota.vagas, 2)

    def test_rejeita_instituicao_invalida_sem_criar_rota(self):
        response = self.client.post(reverse('oferecer_carona'), {
            'origem': 'Centro',
            'instituicao': 'nao-numerico',
            'horario': '07:30',
            'vagas': '2',
            'transporte': 'Carro',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Selecione uma instituição válida.')
        self.assertFalse(Rota.objects.exists())

    def test_detalhes_da_rota_mostram_campos_reais_do_modelo(self):
        rota = Rota.objects.create(
            id_usuario=self.usuario,
            id_instituicao=self.instituicao,
            origem='Centro',
            horario='07:30',
            transporte='Carro',
            vagas=2,
        )

        response = self.client.get(reverse('rota_detalhes', args=[rota.id_rota]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Centro')
        self.assertContains(response, 'Universidade de Teste')
        self.assertContains(response, 'Pessoa Estudante')
