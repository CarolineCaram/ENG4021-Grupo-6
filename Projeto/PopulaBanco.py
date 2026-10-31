import os
import django
from datetime import datetime, time, date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vai_junto.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from django.utils import timezone
from vai_junto.models import (Instituicao, Usuario, Rota, Solicitacao,
                              Grupo, Mensagem, Carona)

print("--- INICIANDO POPULAÇÃO DO BANCO ---")

puc, _ = Instituicao.objects.get_or_create(
    id_instituicao=1,
    defaults={'nome': 'Pontifícia Universidade Católica do Rio de Janeiro',
              'sigla': 'PUC-Rio'})

ana, _ = Usuario.objects.get_or_create(
    id_usuario=1,
    defaults={'nome': 'Ana Souza', 'email': 'ana@email.com',
              'matricula': '2610001', 'senha': make_password('senha123')})
bruno, _ = Usuario.objects.get_or_create(
    id_usuario=2,
    defaults={'nome': 'Bruno Lima', 'email': 'bruno@email.com',
              'matricula': '2610002', 'senha': make_password('senha123')})

rota, _ = Rota.objects.get_or_create(
    id_rota=1,
    defaults={'usuario': ana, 'instituicao': puc, 'origem': 'Irajá',
              'referencia': 'Próximo ao metrô', 'horario': time(7, 0),
              'transporte': 'carro', 'vagas': 3})

Solicitacao.objects.get_or_create(
    rota=rota, solicitante=bruno,
    defaults={'status': 'pendente',
              'criada_em': timezone.make_aware(datetime(2026, 10, 9, 3, 0, 15))})

grupo, _ = Grupo.objects.get_or_create(
    id_grupo=1, defaults={'rota': rota, 'nome': 'Irajá → PUC'})
grupo.usuarios.add(ana, bruno)

Mensagem.objects.get_or_create(
    id_mensagem=1,
    defaults={'grupo': grupo, 'usuario': ana, 'texto': 'Bom dia, saio às 7h!',
              'enviada_em': timezone.make_aware(datetime(2026, 10, 9, 3, 0, 15))})

carona, _ = Carona.objects.get_or_create(
    id_carona=1,
    defaults={'grupo': grupo, 'rota': rota,
              'data': date(2026, 10, 10), 'status': 'agendada'})
carona.passageiros.add(bruno)



print("--- PROCESSO CONCLUÍDO ---")