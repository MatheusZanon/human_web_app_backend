from django.db import models

# Create your models here.

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

class ClientesFinanceiroValores(models.Model):
    cliente = models.ForeignKey(to=ClientesFinanceiro, 
                                   on_delete=models.CASCADE, 
                                   related_name='valores',
                                   null=False, blank=False)
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
    relatorio_enviado = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clientes_financeiro_valores'


class ClientesFinanceiroReembolsos(models.Model):
    cliente = models.ForeignKey(to=ClientesFinanceiro, 
                                   on_delete=models.CASCADE,
                                   related_name='reembolsos',
                                   null=False, blank=False)
    descricao = models.CharField(max_length=255, blank=True, null=True)
    valor = models.FloatField(blank=True, null=True)
    mes = models.IntegerField()
    ano = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clientes_financeiro_reembolsos'


class Funcionarios(models.Model):
    nome = models.CharField(max_length=255)
    email = models.CharField(max_length=255, blank=True, null=True)
    senha = models.CharField(max_length=64)
    rg = models.CharField(max_length=8, blank=True, null=True)
    cpf = models.CharField(max_length=11, blank=True, null=True)
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
    execucoes = models.IntegerField(blank=True, null=True)
    ultima_execucao = models.DateField(blank=True, null=True)
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