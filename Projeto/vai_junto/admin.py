from django.contrib import admin
from vai_junto.models import (Instituicao, Usuario, Rota, Solicitacao,
                              Grupo, Mensagem, Carona, Avaliacao)

for modelo in (Instituicao, Usuario, Rota, Solicitacao,
               Grupo, Mensagem, Carona, Avaliacao):
    admin.site.register(modelo)