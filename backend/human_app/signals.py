from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ObjectDoesNotExist
from time import sleep

@receiver(post_migrate)
def create_groups(sender, **kwargs):
    # Lista de grupos a serem criados e suas permissões associadas
    groups_permissions = {
        'ADMIN': ['add_user', 'change_user', 'view_user',
                  'add_funcionarios', 'change_funcionarios', 'view_funcionarios',
                  'add_clientesfinanceiro', 'change_clientesfinanceiro', 'view_clientesfinanceiro',
                  'add_clientesfinanceirovalores', 'change_clientesfinanceirovalores', 
                  'delete_clientesfinanceirovalores', 'view_clientesfinanceirovalores',
                  'add_clientesfinanceiroreembolsos', 'change_clientesfinanceiroreembolsos', 
                  'delete_clientesfinanceiroreembolsos', 'view_clientesfinanceiroreembolsos',
                  'change_robos', 'view_robos', 'add_parametros', 'change_parametros', 
                  'delete_parametros', 'view_parametros', 'add_robosparametros', 'change_robosparametros', 
                  'delete_robosparametros', 'view_robosparametros',],


        'TI': ['add_user', 'change_user', 'view_user',
               'add_funcionarios', 'change_funcionarios', 'view_funcionarios',
               'add_clientesfinanceiro', 'change_clientesfinanceiro', 'view_clientesfinanceiro',
               'add_clientesfinanceirovalores', 'change_clientesfinanceirovalores', 
                'delete_clientesfinanceirovalores', 'view_clientesfinanceirovalores',
                'add_clientesfinanceiroreembolsos', 'change_clientesfinanceiroreembolsos', 
                'delete_clientesfinanceiroreembolsos', 'view_clientesfinanceiroreembolsos',
                'add_robos', 'change_robos', 'delete_robos', 'view_robos',
                'add_parametros', 'change_parametros', 'delete_parametros', 'view_parametros', 
                'add_robosparametros', 'change_robosparametros', 
                'delete_robosparametros', 'view_robosparametros',],


        'FINANCEIRO_OPERACAO': ['view_clientesfinanceiro', 'add_clientesfinanceirovalores', 
                                'change_clientesfinanceirovalores', 'view_clientesfinanceirovalores',
                                'add_clientesfinanceiroreembolsos', 'change_clientesfinanceiroreembolsos', 
                                'view_clientesfinanceiroreembolsos', 'change_robos', 'view_robos',],

        'RH_GERENCIA': ['add_user', 'change_user', 'view_user',
                        'add_funcionarios', 'change_funcionarios', 'view_funcionarios',
                        'change_robos', 'view_robos',],


        'RG_OPERACAO': ['change_user', 'view_user',
                        'change_funcionarios', 'view_funcionarios',
                        'change_robos', 'view_robos',],
    }

    for group_name, permissions_codenames in groups_permissions.items():
        if not Group.objects.filter(name=group_name).exists():   
            # Cria o grupo, se não existir
            group, created = Group.objects.get_or_create(name=group_name)

            # Limpa todas as permissões existentes para evitar duplicatas
            group.permissions.clear()

            # Adiciona as permissões especificadas ao grupo
            for codename in permissions_codenames:
                try:
                    # Encontra a permissão pelo seu codename
                    permission = Permission.objects.get(codename=codename)
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    print(f"A permissão com codename '{codename}' não existe.")
        else:
            print(f"O grupo '{group_name}' já existe. Nenhuma permissão foi adicionada.")