<<<<<<< HEAD
# Generated by Django 5.0.3 on 2024-03-14 11:31
=======
# Generated by Django 5.0.3 on 2024-03-15 12:52
>>>>>>> main

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientesFinanceiro',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_razao_social', models.CharField(max_length=255)),
                ('cnpj', models.CharField(blank=True, max_length=25, null=True)),
                ('cpf', models.CharField(blank=True, max_length=25, null=True)),
                ('email', models.CharField(blank=True, max_length=255, null=True)),
                ('telefone_celular', models.CharField(blank=True, max_length=25, null=True)),
                ('regiao', models.CharField(max_length=45)),
                ('created_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'clientes_financeiro',
            },
        ),
        migrations.CreateModel(
            name='Parametros',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=255)),
                ('valor', models.CharField(max_length=255)),
                ('tipo', models.CharField(choices=[('BOOLEAN', 'BOOLEAN'), ('STRING', 'STRING'), ('FLOAT', 'FLOAT'), ('INTEGER', 'INTEGER')], default='STRING', max_length=255)),
                ('created_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'parametros',
            },
        ),
        migrations.CreateModel(
            name='Parametros',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=255)),
                ('tipo', models.CharField(choices=[('DATE', 'DATE'), ('INTEGER', 'INTEGER'), ('BOOLEAN', 'BOOLEAN'), ('STRING', 'STRING'), ('FLOAT', 'FLOAT')], default='STRING', max_length=255)),
                ('created_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'parametros',
            },
        ),
        migrations.CreateModel(
            name='Robos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(blank=True, max_length=50, null=True)),
                ('categoria', models.CharField(blank=True, max_length=50, null=True)),
                ('descricao', models.CharField(blank=True, max_length=255, null=True)),
                ('execucoes', models.IntegerField(blank=True, null=True)),
                ('ultima_execucao', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'robos',
            },
        ),
        migrations.CreateModel(
            name='SolicitacoesCadastro',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=255)),
                ('firstname', models.CharField(max_length=255)),
                ('lastname', models.CharField(max_length=255)),
                ('cpf', models.CharField(blank=True, max_length=25, null=True)),
                ('email', models.CharField(blank=True, max_length=255, null=True)),
                ('senha', models.CharField(max_length=64)),
                ('telefone_celular', models.CharField(blank=True, max_length=25, null=True)),
                ('setor', models.CharField(max_length=55)),
                ('created_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'solicitacoes_cadastro',
            },
        ),
        migrations.CreateModel(
            name='ClientesFinanceiroReembolsos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cliente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reembolsos', to='human_app.clientesfinanceiro')),
                ('descricao', models.CharField(blank=True, max_length=255, null=True)),
                ('valor', models.FloatField(blank=True, null=True)),
                ('mes', models.IntegerField()),
                ('ano', models.IntegerField()),
                ('created_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'clientes_financeiro_reembolsos',
            },
        ),
        migrations.CreateModel(
            name='ClientesFinanceiroValores',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cliente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='valores', to='human_app.clientesfinanceiro')),
                ('cod_empresa', models.IntegerField(blank=True, null=True)),
                ('convenio_farmacia', models.FloatField(blank=True, null=True)),
                ('adiant_salarial', models.FloatField(blank=True, null=True)),
                ('numero_empregados', models.IntegerField(blank=True, null=True)),
                ('numero_estagiarios', models.IntegerField(blank=True, null=True)),
                ('trabalhando', models.IntegerField(blank=True, null=True)),
                ('salario_contri_empregados', models.FloatField(blank=True, null=True)),
                ('salario_contri_contribuintes', models.FloatField(blank=True, null=True)),
                ('soma_salarios_provdt', models.FloatField(blank=True, null=True)),
                ('inss', models.FloatField(blank=True, null=True)),
                ('fgts', models.FloatField(blank=True, null=True)),
                ('irrf', models.FloatField(blank=True, null=True)),
                ('salarios_pagar', models.FloatField(blank=True, null=True)),
                ('vale_transporte', models.FloatField(blank=True, null=True)),
                ('assinat_eletronica', models.FloatField(blank=True, null=True)),
                ('vale_refeicao', models.FloatField(blank=True, null=True)),
                ('mensal_ponto_elet', models.FloatField(blank=True, null=True)),
                ('saude_seguranca_trabalho', models.FloatField(blank=True, null=True)),
                ('percentual_human', models.FloatField(blank=True, null=True)),
                ('economia_mensal', models.FloatField(blank=True, null=True)),
                ('economia_formal', models.FloatField(blank=True, null=True)),
                ('total_fatura', models.FloatField(blank=True, null=True)),
                ('mes', models.IntegerField()),
                ('ano', models.IntegerField()),
                ('anexo_enviado', models.IntegerField()),
                ('relatorio_enviado', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'clientes_financeiro_valores',
            },
        ),
        migrations.CreateModel(
<<<<<<< HEAD
            name='RobosParametros',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parametro', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='robos', to='human_app.parametros')),
                ('robo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parametros', to='human_app.robos')),
                ('valor', models.CharField(max_length=255)),
=======
            name='Funcionarios',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rg', models.CharField(blank=True, max_length=8, null=True)),
                ('cpf', models.CharField(blank=True, max_length=11, null=True)),
                ('telefone_celular', models.CharField(blank=True, max_length=25, null=True)),
                ('setor', models.CharField(max_length=55)),
                ('created_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('usuario', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'funcionarios',
            },
        ),
        migrations.CreateModel(
            name='RobosParametros',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_parametros', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='robos', to='human_app.parametros')),
                ('id_robos', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parametros', to='human_app.robos')),
>>>>>>> main
                ('created_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'robos_parametros',
            },
        ),
    ]
