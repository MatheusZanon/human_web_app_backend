from rest_framework import status, viewsets
from rest_framework.views import APIView, Response
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import User
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
        
class FuncionarioViewset(viewsets.ModelViewSet):
    queryset = Funcionarios.objects.all()    
    serializer_class = FuncionariosSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='auth')
    def auth_user(self, request, *args, **kwargs):
        try:
            user = Funcionarios.objects.get(user=request.user)
            serializer = FuncionariosSerializer(user)
            if serializer:
                return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response({'error': str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
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

class ClientesFinanceiroViewset(viewsets.ModelViewSet):
    queryset = ClientesFinanceiro.objects.all()    
    serializer_class = ClientesFinanceiroSerializer

class ClientesFinanceiroValoresViewset(viewsets.ModelViewSet):
    queryset = ClientesFinanceiroValores.objects.all()    
    serializer_class = ClientesFinanceiroValoresSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='vales_sst')
    def vales_sst(self, request):
        try:
            vales_sst = ClientesFinanceiroValores.objects.all()
            serializer = ClientesFinanceiroValesSSTSerializer(vales_sst, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='reembolsos')
    def reembolsos(self, request):
        try:
            reembolsos = ClientesFinanceiroReembolsos.objects.all()
            serializer = ClientesFinanceiroReembolsosSerializer(reembolsos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_404_NOT_FOUND)

class RobosViewset(viewsets.ModelViewSet):
    queryset = Robos.objects.all()    
    serializer_class = RobosSerializer

    @action(detail=True, methods=['get'], url_path='parametros')
    def parametros(self, request, pk=None):
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
            return Response(f"{error}", status=status.HTTP_404_NOT_FOUND)
        
    @action(detail=True, methods=['post'], url_path='parametros')
    def salvar_parametros(self, request, pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)

        try:
            robo_parametros = RobosParametros.objects.filter(robo=pk)

            if not robo_parametros:
                raise Exception("Os parâmetros do robo não foram encontrados")
                
            parametros_testados = []
            for key, value in request.data.items():
                for param in robo_parametros:
                    parametro = Parametros.objects.get(pk=param.parametro.pk)
                    if not parametro:
                        raise Exception("Os parâmetros do robo não foram encontrados")
                    parametros_testados.append(parametro.nome)
                    if parametro.nome == key:
                        param.valor = value
                        param.save()
                        return Response("Parâmetros atualizados com sucesso", status=status.HTTP_204_NO_CONTENT)
                if not parametros_testados:
                    raise Exception(f"Os parâmetros do robo não foram encontrados. Parâmetros enviados: {request.data.keys()}")
            raise Exception(f"Os parâmetros do robo são diferentes do enviado. Esperado: {', '.join(parametros_testados)}, Enviado: {key}")
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path='rotinas')
    def rotinas(self, request, pk=None):
        rotinas = get_list_or_404(Rotinas, robo=pk)
        serializer = RotinasSerializer(rotinas, many=True)
        if serializer:
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=True, methods=['post'], url_path='executar')
    def executar_robo(self, request, pk=None):
        try:
            robo = Robos.objects.get(id=pk)
            if not robo:
                raise Exception("O robo não foi encontrado")
            
            parametros = {}
            for key, value in request.data.items():
                parametros[key] = value

            robo_parametros = RobosParametros.objects.filter(robo=pk)

            if not robo_parametros:
                raise Exception("O robo não possui parâmetros definidos")
            
            parametros_testados = []
            for key, value in request.data.items():
                for param in robo_parametros:
                    parametro = Parametros.objects.get(pk=param.parametro.pk)
                    if not parametro:
                        raise Exception("Os parâmetros do robo não foram encontrados")
                    parametros_testados.append(parametro.nome)
                    if parametro.nome == key:
                        param.valor = value
                        param.save()
                        print(f"Parametro {key} atualizado")
                if not parametros_testados:
                    raise Exception(f"Os parâmetros do robo não foram encontrados. Parâmetros enviados: {request.data.keys()}")
            if param in parametros_testados != request.data.keys():
                print(f"Os parâmetros do robo são diferentes do enviado. Esperado: {', '.join(parametros_testados)}, Enviado: {key}")

            nome_robo = robo.nome.lower().replace(" ", "_")
            script_path = f"D:/workspace/Python/human/robo_folha_ponto/robo_{nome_robo}"
            robo_processo = subprocess.Popen(['powershell', '-Command', f"& cd '{script_path}'; ./.venv/Scripts/Activate.ps1; python robo_{nome_robo}.py"], shell=True, creationflags=subprocess.DETACHED_PROCESS, start_new_session=True)
            print("Robo em execução")
            sleep(3)
            parametros_json = json.dumps(parametros)
            resultado_request = requests.post(f"http://127.0.0.1:5000/", data=parametros_json, headers={'Content-Type': 'application/json'})
 
            if resultado_request.status_code == 200:
                robo.execucoes += 1
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
            return Response(f"{error}", status=status.HTTP_404_NOT_FOUND)
        