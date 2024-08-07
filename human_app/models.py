from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class Funcionarios(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='funcionarios', blank=False, null=False)
    rg = models.CharField(max_length=8, blank=True, null=True)
    cpf = models.CharField(max_length=11, blank=True, null=True)
    telefone_celular = models.CharField(max_length=25, blank=True, null=True)
    situacao = models.CharField(max_length=100, default='INATIVO')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'funcionarios'

class PasswordResetTokens(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset', blank=False, null=False)
    token = models.CharField(max_length=255, blank=False, null=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_in = models.DateTimeField(null=False, blank=False)

    def __str__(self):
        return self.token
    
    def is_valid(self):
        return timezone.now() < self.expires_in

    class Meta:
        db_table = 'password_reset'

class ClientesFinanceiro(models.Model):
    nome_razao_social = models.CharField(max_length=255, blank=False, null=False)
    nome_fantasia = models.CharField(max_length=255, blank=True, null=True)
    cnpj = models.CharField(max_length=25, blank=True, null=True)
    cpf = models.CharField(max_length=25, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    telefone_celular = models.CharField(max_length=25, blank=True, null=True)
    regiao = models.CharField(max_length=45)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clientes_financeiro'

class ClientesFinanceiroValores(models.Model):
    cliente = models.ForeignKey(to=ClientesFinanceiro, 
                                   on_delete=models.CASCADE, 
                                   related_name='valores', blank=False, null=False)
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
    seguro_estagio = models.FloatField(blank=True, null=True)
    percentual_human = models.FloatField(blank=True, null=True)
    economia_mensal = models.FloatField(blank=True, null=True)
    economia_liquida = models.FloatField(blank=True, null=True)
    total_fatura = models.FloatField(blank=True, null=True)
    mes = models.IntegerField()
    ano = models.IntegerField()
    anexo_enviado = models.IntegerField(default=0)
    relatorio_enviado = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clientes_financeiro_valores'

class ClientesFinanceiroReembolsos(models.Model):
    cliente = models.ForeignKey(to=ClientesFinanceiro, 
                                   on_delete=models.CASCADE,
                                   related_name='reembolsos', blank=False, null=False)
    descricao = models.CharField(max_length=255, blank=True, null=True)
    valor = models.FloatField(blank=True, null=True)
    mes = models.IntegerField()
    ano = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clientes_financeiro_reembolsos'

class ClientesFinanceiroFolhaPonto(models.Model):
    cliente = models.ForeignKey(to=ClientesFinanceiro, 
                                   on_delete=models.CASCADE,
                                   related_name='folha_ponto', blank=False, null=False)
    registrado = models.BooleanField(default=False)
    colaborador = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clientes_financeiro_folha_ponto'

class Robos(models.Model):
    nome = models.CharField(max_length=50, unique=True, blank=False, null=False)
    categoria = models.CharField(max_length=50, blank=True, null=True)
    descricao = models.CharField(max_length=255, blank=True, null=True)
    execucoes = models.IntegerField(default=0)
    ultima_execucao = models.DateField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'robos'

class Parametros(models.Model):
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    TEXT = "TEXT"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"

    TIPOS = {
        (INTEGER, "INTEGER"),
        (FLOAT, "FLOAT"),
        (TEXT, "TEXT"),
        (BOOLEAN, "BOOLEAN"),
        (DATE, "DATE"),
    }

    nome = models.CharField(max_length=255, unique=True)
    tipo = models.CharField(max_length=255, choices=TIPOS, default=TEXT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'parametros'

class RobosParametros(models.Model):
    robo = models.ForeignKey(to=Robos,
                                   on_delete=models.CASCADE,
                                   related_name='parametros', blank=False, null=False)
    parametro = models.ForeignKey(to=Parametros,
                                   on_delete=models.CASCADE,
                                   related_name='robos',
                                   null=False, blank=False)
    valor = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'robos_parametros'

class Rotinas(models.Model):
    nome = models.CharField(max_length=255)
    robo = models.ForeignKey(to=Robos,
                            on_delete=models.CASCADE,
                            related_name='rotinas', blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rotinas'