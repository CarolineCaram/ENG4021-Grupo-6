from django.db import models
from django.utils import timezone



class Instituicao(models.Model):
    id_instituicao = models.AutoField(primary_key=True, db_column='id_instituicao')
    nome = models.CharField(max_length=255, db_column='nome')
    sigla = models.CharField(max_length=50, db_column='sigla')

    class Meta:
        managed = True
        db_table = 'instituicao'
        verbose_name_plural = "Instituições"

    def __str__(self):
        return self.sigla


class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True, db_column='id_usuario')
    nome = models.CharField(max_length=255, db_column='nome')
    email = models.EmailField(unique=True, db_column='email')
    matricula = models.CharField(max_length=50, db_column='matricula')
    senha = models.CharField(max_length=255, db_column='senha')
    # pegar = só passageiro | dar = só motorista | ambos = os dois
    papel = models.CharField(max_length=10, default='ambos', db_column='papel')
    foto = models.FileField(upload_to='fotos/', null=True, blank=True, db_column='foto')

    class Meta:
        managed = True
        db_table = 'usuario'
        verbose_name_plural = "Usuários"

    def __str__(self):
        return self.nome


class Rota(models.Model):
    id_rota = models.AutoField(primary_key=True, db_column='id_rota')
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE,
                                   db_column='id_usuario', related_name='rotas')
    id_instituicao = models.ForeignKey(Instituicao, on_delete=models.CASCADE,
                                       db_column='id_instituicao', related_name='rotas')
    origem = models.CharField(max_length=255, db_column='origem')
    referencia = models.CharField(max_length=255, db_column='referencia', blank=True, null=True)
    horario = models.TimeField(db_column='horario')
    transporte = models.CharField(max_length=100, db_column='transporte')
    vagas = models.IntegerField(db_column='vagas')

    class Meta:
        managed = True
        db_table = 'rota'
        verbose_name_plural = "Rotas"

    def __str__(self):
        return f"{self.origem} -> {self.id_instituicao.sigla} ({self.horario})"



class Veiculo(models.Model):
    '''Veículo de quem dá carona (com vagas) ou preferência de veículo de
    quem só pega carona (vagas = 0). Um usuário pode ter vários.'''
    id_veiculo = models.AutoField(primary_key=True, db_column='id_veiculo')
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE,
                                   db_column='id_usuario', related_name='veiculos')
    tipo = models.CharField(max_length=20, db_column='tipo')   # Carro, Moto, Bicicleta, Van
    vagas = models.IntegerField(default=0, db_column='vagas')  # 0 = preferência de passageiro

    class Meta:
        managed = True
        db_table = 'veiculo'
        # sem unique_together: quem é "os dois" pode dirigir Carro (vagas>0)
        # e também aceitar carona de Carro (vagas=0)

    def __str__(self):
        return f'{self.tipo} ({self.id_usuario.nome})'


class HorarioRota(models.Model):
    """Horário de saída de uma rota em cada dia da semana (0=Seg ... 6=Dom)."""
    DIAS = [(0, 'Seg'), (1, 'Ter'), (2, 'Qua'), (3, 'Qui'), (4, 'Sex'), (5, 'Sáb'), (6, 'Dom')]

    rota = models.ForeignKey(Rota, on_delete=models.CASCADE,
                             db_column='id_rota', related_name='horarios')
    dia = models.PositiveSmallIntegerField(choices=DIAS)
    horario = models.TimeField()

    class Meta:
        managed = True
        db_table = 'horario_rota'
        ordering = ['dia']
        unique_together = ('rota', 'dia')
        verbose_name_plural = "Horários das rotas"

    def __str__(self):
        return f"{self.get_dia_display()} {self.horario:%H:%M}"


class Solicitacao(models.Model):
    rota = models.ForeignKey(Rota, on_delete=models.CASCADE,
                             db_column='id_rota', related_name='solicitacoes')
    solicitante = models.ForeignKey(Usuario, on_delete=models.CASCADE,
                                    db_column='id_solicitante', related_name='solicitacoes')
    # tipo: 'pedido' = passageiro pede carona ao motorista
    #       'oferta' = motorista oferece carona a um passageiro (destinatario)
    tipo = models.CharField(max_length=10, default='pedido', db_column='tipo')
    destinatario = models.ForeignKey(Usuario, on_delete=models.CASCADE,
                                     db_column='id_destinatario',
                                     related_name='ofertas_recebidas',
                                     null=True, blank=True)
    status = models.CharField(max_length=20, default='pendente')
    criada_em = models.DateTimeField(default=timezone.now)
    respondida_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'solicitacao'
        verbose_name_plural = "Solicitações"

    def __str__(self):
        return f"{self.solicitante} -> {self.rota} ({self.status})"


class Grupo(models.Model):
    id_grupo = models.AutoField(primary_key=True)
    rota = models.OneToOneField(Rota, on_delete=models.CASCADE,
                                db_column='id_rota', related_name='grupo')
    nome = models.CharField(max_length=255)
    usuarios = models.ManyToManyField(Usuario, db_table='grupo_usuario',
                                      related_name='grupos')

    class Meta:
        managed = True
        db_table = 'grupo'
        verbose_name_plural = "Grupos"

    def __str__(self):
        return self.nome


class Mensagem(models.Model):
    id_mensagem = models.AutoField(primary_key=True)
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE,
                              db_column='id_grupo', related_name='mensagens')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE,
                                db_column='id_usuario')
    texto = models.TextField()
    enviada_em = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = True
        db_table = 'mensagem'
        ordering = ['enviada_em']
        verbose_name_plural = "Mensagens"

    def __str__(self):
        return f"{self.usuario}: {self.texto[:30]}"


class Carona(models.Model):
    id_carona = models.AutoField(primary_key=True)
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE,
                              db_column='id_grupo', related_name='caronas')
    rota = models.ForeignKey(Rota, on_delete=models.CASCADE,
                             db_column='id_rota', related_name='caronas')
    data = models.DateField()
    status = models.CharField(max_length=20, default='agendada')
    passageiros = models.ManyToManyField(Usuario, db_table='carona_passageiro',
                                         related_name='caronas_como_passageiro')

    class Meta:
        managed = True
        db_table = 'carona'
        verbose_name_plural = "Caronas"

    def __str__(self):
        return f"Carona {self.data} - {self.rota}"


class Avaliacao(models.Model):
    '''Avaliação de um usuário por outro, num papel específico: como o
    avaliado foi COMO MOTORISTA ou COMO PASSAGEIRO. Uma por par/papel —
    avaliar de novo atualiza o voto. A carona é opcional (a avaliação é
    da pessoa, não de uma viagem específica).'''
    PAPEIS = [('motorista', 'Como motorista'), ('passageiro', 'Como passageiro')]

    id_avaliacao = models.AutoField(primary_key=True)
    carona = models.ForeignKey(Carona, on_delete=models.CASCADE,
                               db_column='id_carona', related_name='avaliacoes',
                               null=True, blank=True)
    avaliador = models.ForeignKey(Usuario, on_delete=models.CASCADE,
                                  db_column='id_avaliador', related_name='avaliacoes_feitas')
    avaliado = models.ForeignKey(Usuario, on_delete=models.CASCADE,
                                 db_column='id_avaliado', related_name='avaliacoes_recebidas')
    papel = models.CharField(max_length=10, choices=PAPEIS, default='motorista',
                             db_column='papel')
    aprovou = models.BooleanField()
    criada_em = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = True
        db_table = 'avaliacao'
        unique_together = ('avaliador', 'avaliado', 'papel')
        verbose_name_plural = "Avaliações"

    def __str__(self):
        return f"{self.avaliador} avaliou {self.avaliado} ({self.papel})"