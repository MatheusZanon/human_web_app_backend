from rest_framework import status, viewsets
from rest_framework.views import APIView, Response
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.filters import SearchFilter
from django.contrib.auth.models import User, Group, Permission
from django.shortcuts import get_object_or_404, get_list_or_404
from human_app.models import *
from human_app.serializers import *
from faker import Faker
import subprocess
from datetime import datetime
from time import sleep
import requests
import json

# Create your views and viewsets here.
class UserView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        email = request.data.get('email')
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Esse nome de usuário já existe.'}, status=status.HTTP_400_BAD_REQUEST)
        elif User.objects.filter(email=email).exists():
            return Response({'error': 'Esse email já existe.'}, status=status.HTTP_400_BAD_REQUEST) 
        try:
            user = None
            user_serializer = UserSerializer(data=request.data)
            if user_serializer.is_valid():
                user = user_serializer.save()
                funcionario_data = {
                    'rg': request.data.get('rg'),
                    'cpf': request.data.get('cpf'),
                    'telefone_celular': request.data.get('telefone_celular'),
                }
                funcionario = Funcionarios.objects.create(user=user, **funcionario_data)
                funcionario.save()
                return Response(user_serializer.data, status=status.HTTP_201_CREATED)
            else:
                print("USER SERIALIZER INVALIDO")
                return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response({'error': str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class VerifyToken(APIView):
    def get(self, request, format=None):
        token = request.META.get('HTTP_AUTHORIZATION', None)
        if token is None:
            return Response({"error": "Token não fornecido."}, status=status.HTTP_400_BAD_REQUEST)

        token = token.split(" ")[1]  # Remove "Bearer" do token
        try:
            UntypedToken(token)
            return Response({"token": "Válido"}, status=status.HTTP_200_OK)
        except (InvalidToken, TokenError) as e:
            return Response({"error": "Token inválido."}, status=status.HTTP_401_UNAUTHORIZED)
        
@permission_classes([IsAuthenticated])
class GroupsViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

@permission_classes([IsAuthenticated])
class FuncionarioViewset(viewsets.ModelViewSet):
    queryset = Funcionarios.objects.all()    
    serializer_class = FuncionariosSerializer
    
    def retrieve(self, request, pk=None):
        try:
            user = Funcionarios.objects.get(user=pk)
            serializer = FuncionariosSerializer(user)
            if serializer:
                user_data = serializer.data
                groups = [group.name for group in Group.objects.filter(user=user.user.id).all()]

                permissionsQuery = [group.permissions.all() for group in Group.objects.filter(pk=user.user.id).all()]
                permissions: list
                for permission in permissionsQuery:
                    permissions = [permission.name for permission in permission]

                user_data['groups'] = groups
                user_data['permissions'] = permissions
                del user_data['user_permissions']
                return Response(user_data, status=status.HTTP_200_OK)
        except Funcionarios.DoesNotExist:
            return Response({'error': 'Funcionário não encontrado'}, status=status.HTTP_404_NOT_FOUND)
    
    def list(self, request, *args, **kwargs):
        try:
            funcionarios = Funcionarios.objects.all()
            serializer = FuncionariosSerializer(funcionarios, many=True)
            if serializer:
                funcionarios_data = serializer.data
                index = 0
                for funcionario in funcionarios_data:
                    groups = [group.name for group in Group.objects.filter(user=funcionario.get('id')).all()]
                    funcionario['groups'] = groups
                    del funcionario['user_permissions']
                    funcionarios_data[index] = funcionario
                    index += 1
                return Response(funcionarios_data, status=status.HTTP_200_OK)
        except Funcionarios.DoesNotExist:
            return Response({'error': 'Funcionários não encontrado'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], url_path='auth')
    def auth_user(self, request, *args, **kwargs):
        try:
            user = Funcionarios.objects.get(user=request.user)
            serializer = FuncionariosSerializer(user)
            if serializer:
                user_data = serializer.data
                groups = [group.name for group in Group.objects.filter(user=request.user).all()]
                user_data['groups'] = groups
                del user_data['user_permissions']
                return Response(user_data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response({'error': str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['put'], url_path='activate')
    def activate_user(self, request, pk=None):
        try:
            user = User.objects.filter(id=pk).get()

            ids = request.data['id']
            for id in ids:
                group = Group.objects.get(id=id)
                user.groups.add(group)
                user.is_active = True
                if group.name == 'ADMIN':
                    user.is_staff = True
                user.save()
            return Response(f"O usuário {user.username} foi ativado com sucesso", status=status.HTTP_204_NO_CONTENT)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['put'], url_path='deactivate')
    def desactivate_user(self, request, pk=None):
        try:
            user = User.objects.filter(id=pk).get()
            user.is_active = False
            user.save()
            return Response(f"O usuário {user.username} foi desativado com sucesso", status=status.HTTP_204_NO_CONTENT)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@permission_classes([IsAuthenticated])
class ClientesFinanceiroViewset(viewsets.ModelViewSet):
    queryset = ClientesFinanceiro.objects.all()    
    serializer_class = ClientesFinanceiroSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [SearchFilter]
    search_fields = ['nome_razao_social']


@permission_classes([IsAuthenticated])
class ClientesFinanceiroValoresViewset(viewsets.ModelViewSet):
    queryset = ClientesFinanceiroValores.objects.all()    
    serializer_class = ClientesFinanceiroValoresSerializer
    pagination_class = LimitOffsetPagination

    @action(detail=False, methods=['get'], url_path='vales_sst')
    def vales_sst(self, request):
        try:
            vales_sst = ClientesFinanceiroValores.objects.all()
            page = self.paginate_queryset(vales_sst)
            if page is not None:
                serializer = ClientesFinanceiroValesSSTSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='reembolsos')
    def reembolsos(self, request):
        try:
            reembolsos = ClientesFinanceiroReembolsos.objects.all().order_by('cliente_id')
            page = self.paginate_queryset(reembolsos)
            if page is not None:    
                serializer = ClientesFinanceiroReembolsosSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@permission_classes([IsAuthenticated])
class RobosViewset(viewsets.ModelViewSet):
    queryset = Robos.objects.all()    
    serializer_class = RobosSerializer

    def destroy(self, request, pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        
        try:
            robo_parametros = RobosParametros.objects.filter(robo=pk)
            if robo_parametros:
                parametro = None
                for param in robo_parametros:
                    print(param.pk)
                    parametro = Parametros.objects.get(pk=param.parametro.pk)
                    if parametro:
                        param.delete()
                        parametro.delete()

            robo.delete()
            return Response(f"Robo excluído com sucesso", status=status.HTTP_200_OK)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='parametros/criar')
    def criar_parametro(self, request, pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            if Parametros.objects.filter(nome=request.data['nome']).exists():
                return Response("Este parâmetro já foi criado", status=status.HTTP_400_BAD_REQUEST)
            
            parametro_serializer = ParametrosSerializer(data=request.data)

            if parametro_serializer.is_valid():                
                parametro_serializer.save()

                robo_parametro_serializer = RobosParametrosSerializer(data={'robo': robo.id, 'parametro': parametro_serializer.data['id']})
                if robo_parametro_serializer.is_valid():
                    robo_parametro_serializer.save()
                    return Response(f"Parâmetro criado com sucesso", status=status.HTTP_201_CREATED)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True, methods=['get'], url_path='parametros/listar')
    def listar_parametros(self, request, pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            robo_parametros = RobosParametros.objects.filter(robo=pk)

            if not robo_parametros:
                return Response("O robo não possui parâmetros definidos", status=status.HTTP_204_NO_CONTENT)
            serializer = RobosParametrosSerializer(robo_parametros, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['put'], url_path='parametros/atualizar')
    def atualizar_parametros(self, request, pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)

        try:
            robo_parametros = RobosParametros.objects.filter(robo=pk)

            if not robo_parametros:
                return Response("O robo não possui parâmetros definidos", status=status.HTTP_204_NO_CONTENT)
                
            parametros_testados = []
            for key, value in request.data.items():
                for param in robo_parametros:
                    parametro = Parametros.objects.get(pk=param.parametro.pk)
                    if not parametro:
                        return Response("Os parâmetros do robo não foram encontrados", status=status.HTTP_404_NOT_FOUND)
                    parametros_testados.append(parametro.nome)
                    if parametro.nome == key:
                        param.valor = value
                        param.save()
                        return Response("Parâmetros atualizados com sucesso", status=status.HTTP_204_NO_CONTENT)
                if not parametros_testados:
                    return Response("Os parâmetros do robo não foram encontrados", status=status.HTTP_404_NOT_FOUND)
            return Response(f"Os parâmetros do robo são diferentes do enviado. Esperado: {', '.join(parametros_testados)}, Enviado: {key}", status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['put'], url_path='parametros/atualizar/(?P<param_pk>[^/.]+)')
    def atualizar_parametro(self, request, pk=None, param_pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            robo_parametros = RobosParametros.objects.filter(robo=pk)
            if not robo_parametros:
                return Response("O parâmetro do robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
            parametro = None
            for param in robo_parametros:
                if param.parametro.pk == int(param_pk):
                    parametro = Parametros.objects.get(pk=param.parametro.pk)
                    break

            if not parametro:
                return Response("O parâmetro do robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)

            parametro_serializer = ParametrosSerializer(parametro, data=request.data)

            if parametro_serializer.is_valid():
                parametro_serializer.save()
                return Response("Parâmetro atualizado com sucesso", status=status.HTTP_204_NO_CONTENT)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['delete'], url_path='parametros/excluir/(?P<param_pk>[^/.]+)')
    def excluir_parametro(self, request, pk=None, param_pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            robo_parametros = RobosParametros.objects.filter(robo=pk)
            if not robo_parametros:
                return Response("O parâmetro do robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
            
            parametro = None
            for param in robo_parametros:
                print(param.pk == int(param_pk))
                if param.pk == int(param_pk):
                    parametro = Parametros.objects.get(pk=param.parametro.pk)
                    print(parametro.nome)
                    break

            if not parametro:
                return Response("O parâmetro do robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)

            parametro.delete()
            param.delete()
            return Response("Parâmetro excluído com sucesso", status=status.HTTP_204_NO_CONTENT)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='rotinas')
    def rotinas(self, request, pk=None):
        rotinas = get_list_or_404(Rotinas, robo=pk)
        serializer = RotinasSerializer(rotinas, many=True)
        if serializer:
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='rotinas/criar')
    def criar_rotina(self, request, pk=None):
        request_data = request.data
        request_data['robo'] = pk
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            if Rotinas.objects.filter(robo=pk, nome=request_data['nome']).exists():
                return Response("Esta rotina já foi criada", status=status.HTTP_400_BAD_REQUEST)
            
            print(request_data)

            serializer = RotinasSerializer(data=request_data)

            if serializer.is_valid():
                serializer.save(robo=robo)
                return Response(f"Rotina criada com sucesso", status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='rotinas/listar')
    def listar_rotinas(self, request, pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            robo_rotinas = Rotinas.objects.filter(robo=pk)

            if not robo_rotinas:
                return Response("O robo não possui rotinas definidas", status=status.HTTP_204_NO_CONTENT)
            
            serializer = RotinasSerializer(robo_rotinas, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['put'], url_path='rotinas/atualizar/(?P<rotina_pk>[^/.]+)')
    def editar_rotina(self, request, pk=None, rotina_pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            robo_rotinas = Rotinas.objects.filter(robo=pk)
            if not robo_rotinas:
                return Response("O robo não possui rotinas definidas", status=status.HTTP_404_NOT_FOUND)
            
            robo_rotina = None
            for rotina in robo_rotinas:
                if rotina.pk == int(rotina_pk):
                    robo_rotina = rotina
                    break

            if not robo_rotina:
                return Response("A rotina do robo não foi encontrada", status=status.HTTP_404_NOT_FOUND)

            request.data['robo'] = pk
            robo_rotina_serializer = RotinasSerializer(robo_rotina, data=request.data)
            if robo_rotina_serializer.is_valid():
                robo_rotina_serializer.save()
                return Response("Rotina atualizada com sucesso", status=status.HTTP_204_NO_CONTENT)

            return Response(robo_rotina_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['delete'], url_path='rotinas/excluir/(?P<rotina_pk>[^/.]+)')
    def excluir_rotina(self, request, pk=None, rotina_pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            robo_rotinas = Rotinas.objects.filter(robo=pk)
            if not robo_rotinas:
                return Response("O robo não possui rotinas definidas", status=status.HTTP_404_NOT_FOUND)
            
            robo_rotina = None
            for rotina in robo_rotinas:
                if rotina.pk == int(rotina_pk):
                    robo_rotina = rotina
                    break

            if not robo_rotina:
                return Response("A rotina do robo não foi encontrada", status=status.HTTP_404_NOT_FOUND)

            robo_rotina.delete()
            return Response("Rotina excluída com sucesso", status=status.HTTP_204_NO_CONTENT)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True, methods=['post'], url_path='executar')
    def executar_robo(self, request, pk=None):
        try:
            robo = Robos.objects.get(id=pk)
            if not robo:
                return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
            
            parametros = {}
            for key, value in request.data.items():
                parametros[key] = value

            robo_parametros = RobosParametros.objects.filter(robo=pk).all()

            if not robo_parametros:
                return Response("O robo não possui parâmetros definidos", status=status.HTTP_404_NOT_FOUND)
            
            parametros_testados = []
            for key, value in parametros.items():
                for param in robo_parametros:
                    parametro = Parametros.objects.get(pk=param.parametro.pk)
                    if not parametro:
                        return Response("Os parâmetros do robo não foram encontrados", status=status.HTTP_404_NOT_FOUND)
                    parametros_testados.append(parametro.nome)
                    if parametro.nome == key:
                        param.valor = value
                        param.save()
                        print(f"Parametro {key} atualizado")
                if not parametros_testados:
                    return Response("Os parâmetros do robo não foram encontrados", status=status.HTTP_404_NOT_FOUND)
            if param in parametros_testados != request.data.keys():
                print(f"Os parâmetros do robo são diferentes do enviado. Esperado: {', '.join(parametros_testados)}, Enviado: {key}")

            nome_robo = robo.nome.lower().replace(" ", "_")
            script_path = f"C:/Users/ACP/projetos/robo_{nome_robo}"
            robo_processo = subprocess.Popen(['powershell', '-Command', f"& cd '{script_path}'; ./.venv/Scripts/Activate.ps1; python robo_{nome_robo}.py"], shell=True, creationflags=subprocess.DETACHED_PROCESS, start_new_session=True)
            print("Robo em execução")
            sleep(2)
            parametros_json = json.dumps(parametros)
            resultado_request = requests.post(f"http://127.0.0.1:5000/", data=parametros_json, headers={'Content-Type': 'application/json'})
 
            if resultado_request.status_code == 200:
                print(f"Req concluída")
                robo.execucoes = robo.execucoes + 1 if robo.execucoes else 1
                robo.ultima_execucao = datetime.now()
                robo.save()
                print(f"{resultado_request.text}")
                requests.post(f"http://127.0.0.1:5000/shutdown")
                return Response("Robo executado com sucesso", status=status.HTTP_200_OK)
            else:
                print(f"{resultado_request.text}")
                requests.post(f"http://127.0.0.1:5000/shutdown")
                return Response("Erro ao executar o robo", status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        