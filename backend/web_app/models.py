# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Cargos(models.Model):
    nome = models.CharField(max_length=25)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cargos'


class ClientesFinanceiro(models.Model):
    nome_razao_social = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=25, blank=True, null=True)
    cpf = models.CharField(max_length=25, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    telefone_celular = models.CharField(max_length=25, blank=True, null=True)
    regiao = models.CharField(max_length=45)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clientes_financeiro'


class ClientesFinanceiroReembolsos(models.Model):
    cliente = models.ForeignKey(ClientesFinanceiro, models.CASCADE)
    descricao = models.CharField(max_length=255, blank=True, null=True)
    valor = models.FloatField(blank=True, null=True)
    mes = models.IntegerField()
    ano = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clientes_financeiro_reembolsos'


class ClientesFinanceiroValores(models.Model):
    cliente = models.ForeignKey(ClientesFinanceiro, models.CASCADE)
    cod_empresa = models.IntegerField(blank=True, null=True)
    convenio_farmacia = models.FloatField(blank=True, null=True)
    adiant_salarial = models.FloatField(blank=True, null=True)
    numero_empregados = models.IntegerField(blank=True, null=True)
    numero_estagiarios = models.IntegerField(blank=True, null=True)
    trabalhando = models.IntegerField(blank=True, null=True)
    salario_contri_empregados = models.FloatField(blank=True, null=True)
    salario_contri_contribuintes = models.FloatField(blank=True, null=True)
    soma_salarios_provdt = models.FloatField(blank=True, null=True)
    inss = models.FloatField(blank=True, null=True)
    fgts = models.FloatField(blank=True, null=True)
    irrf = models.FloatField(blank=True, null=True)
    salarios_pagar = models.FloatField(blank=True, null=True)
    vale_transporte = models.FloatField(blank=True, null=True)
    assinat_eletronica = models.FloatField(blank=True, null=True)
    vale_refeicao = models.FloatField(blank=True, null=True)
    mensal_ponto_elet = models.FloatField(blank=True, null=True)
    saude_seguranca_trabalho = models.FloatField(blank=True, null=True)
    percentual_human = models.FloatField(blank=True, null=True)
    economia_mensal = models.FloatField(blank=True, null=True)
    economia_formal = models.FloatField(blank=True, null=True)
    total_fatura = models.FloatField(blank=True, null=True)
    mes = models.IntegerField()
    ano = models.IntegerField()
    anexo_enviado = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clientes_financeiro_valores'


class Funcionarios(models.Model):
    nome = models.CharField(max_length=255)
    email = models.CharField(max_length=255, blank=True, null=True)
    senha = models.CharField(max_length=64)
    telefone_celular = models.CharField(max_length=25, blank=True, null=True)
    setor = models.CharField(max_length=55)
    cargo = models.ForeignKey(Cargos, models.DO_NOTHING)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'funcionarios'


class Robos(models.Model):
    nome = models.CharField(max_length=50, blank=True, null=True)
    categoria = models.CharField(max_length=50, blank=True, null=True)
    descricao = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'robos'


class SolicitacoesCadastro(models.Model):
    nome = models.CharField(max_length=255)
    email = models.CharField(max_length=255, blank=True, null=True)
    senha = models.CharField(max_length=64)
    telefone_celular = models.CharField(max_length=25, blank=True, null=True)
    setor = models.CharField(max_length=55)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'solicitacoes_cadastro'
