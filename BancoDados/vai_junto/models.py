from django.db import models

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

    class Meta:
        managed = True
        db_table = 'usuario'
        verbose_name_plural = "Usuários"

    def __str__(self):
        return self.nome


class Rota(models.Model):
    id_rota = models.AutoField(primary_key=True, db_column='id_rota')
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='id_usuario')
    id_instituicao = models.ForeignKey(Instituicao, on_delete=models.CASCADE, db_column='id_instituicao')
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