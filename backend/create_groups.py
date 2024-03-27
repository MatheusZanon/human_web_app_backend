import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'human_project.settings')
django.setup()

from django.contrib.auth.models import Group, Permission

def create_groups():
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
                  'delete_robosparametros', 'view_robosparametros', 'add_rotinas', 'change_rotinas',
                  'delete_rotinas', 'view_rotinas',],


        'TI': ['add_user', 'change_user', 'view_user',
               'add_funcionarios', 'change_funcionarios', 'view_funcionarios',
               'add_clientesfinanceiro', 'change_clientesfinanceiro', 'view_clientesfinanceiro',
               'add_clientesfinanceirovalores', 'change_clientesfinanceirovalores', 
                'delete_clientesfinanceirovalores', 'view_clientesfinanceirovalores',
                'add_clientesfinanceiroreembolsos', 'change_clientesfinanceiroreembolsos', 
                'delete_clientesfinanceiroreembolsos', 'view_clientesfinanceiroreembolsos',
                'add_robos', 'change_robos', 'delete_robos', 'view_robos',
                'add_parametros', 'change_parametros', 'delete_parametros', 'view_parametros', 
                'add_robosparametros', 'change_robosparametros', 'delete_robosparametros', 
                'view_robosparametros', 'add_rotinas', 'change_rotinas', 'delete_rotinas', 'view_rotinas',],


        'FINANCEIRO_OPERACAO': ['view_clientesfinanceiro', 'add_clientesfinanceirovalores', 
                                'change_clientesfinanceirovalores', 'view_clientesfinanceirovalores',
                                'add_clientesfinanceiroreembolsos', 'change_clientesfinanceiroreembolsos', 
                                'view_clientesfinanceiroreembolsos', 'change_robos', 'view_robos', 
                                'add_parametros', 'change_parametros', 'delete_parametros', 'view_parametros', 
                                'add_robosparametros', 'change_robosparametros', 'delete_robosparametros', 
                                'view_robosparametros',
                                'add_rotinas', 'change_rotinas', 'delete_rotinas', 'view_rotinas',],
                                

        'RH_GERENCIA': ['add_user', 'change_user', 'view_user',
                        'add_funcionarios', 'change_funcionarios', 'view_funcionarios',
                        'change_robos', 'view_robos', 'add_parametros', 'change_parametros', 'delete_parametros', 
                        'view_parametros', 'add_robosparametros', 'change_robosparametros', 'delete_robosparametros', 
                        'view_robosparametros', 'add_rotinas', 'change_rotinas', 'delete_rotinas', 'view_rotinas',],


        'RG_OPERACAO': ['change_user', 'view_user',
                        'change_funcionarios', 'view_funcionarios',
                        'change_robos', 'view_robos', 'add_parametros', 'change_parametros', 'delete_parametros', 
                        'view_parametros', 'add_robosparametros', 'change_robosparametros', 'delete_robosparametros', 
                        'view_robosparametros', 'add_rotinas', 'change_rotinas', 'delete_rotinas', 'view_rotinas',],
    }

    for group_name, permissions_codenames in groups_permissions.items():
        if not Group.objects.filter(name=group_name).exists():   
            group, created = Group.objects.get_or_create(name=group_name)
            group.permissions.clear()

            # Adiciona as permissões especificadas ao grupo
            for codename in permissions_codenames:
                try:
                    # Encontra a permissão pelo seu codename
                    permission = Permission.objects.get(codename=codename)
                    if not group.permissions.filter(id=permission.id).exists():
                        group.permissions.add(permission)
                except Permission.DoesNotExist:
                    print(f"A permissão com codename '{codename}' não existe.")
        print(f"Grupo '{group_name}' e permissões criados com sucesso.")


if __name__ == '__main__':
    create_groups()