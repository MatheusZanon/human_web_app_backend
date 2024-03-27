from rest_framework import status
from rest_framework.views import APIView, Response
from rest_framework.decorators import permission_classes
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

# Create your views here.
class UserAPI(APIView):
    def get(self, request, format=None):
        try:
            user = Funcionarios.objects.get(user=request.user)
            serializer = FuncionariosSerializer(user)
            if serializer:
                return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response({'error': str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request, format=None):
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
class FuncionariosAPI(APIView):
    def get(self, request, format=None):
        try:
            funcionarios = Funcionarios.objects.all()
            serializer = FuncionariosSerializer(funcionarios, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Funcionarios.DoesNotExist:
            return Response({'error': 'Funcionário não encontrado'}, status=status.HTTP_404_NOT_FOUND)


class ClientesFinanceiroAPI(APIView):
    def get(self, request, format=None):
        clientes = ClientesFinanceiro.objects.all()
        serializer = ClientesFinanceiroSerializer(clientes, many=True)
        if serializer:
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
              
class ClientesFinanceiroValoresAPI(APIView):
    def get(self, request, format=None):
        clientes = ClientesFinanceiroValores.objects.all()
        serializer = ClientesFinanceiroValoresSerializer(clientes, many=True)
        if serializer:
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoboAPI(APIView):
    def get(self, request, id_robo, format=None):
        try:
            robo = Robos.objects.get(id=id_robo)

            serializer = RobosSerializer(robo)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, id_robo, format=None):
        robo = Robos.objects.get(id=id_robo)
        serializer = RobosSerializer(robo, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RobosAPI(APIView):
    def get(self, request, format=None):
        robos = get_list_or_404(Robos)
        serializer = RobosSerializer(robos, many=True)

        if serializer:
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def post(self, request, format=None):
        faker = Faker()

        for _ in range(10):
            serializer = RobosSerializer(
                data={
                    'nome': faker.name(),
                    'categoria': faker.word(),
                    'descricao': faker.text(),
                    'execucoes': faker.random_int(),
                    'ultima_execucao': faker.date(),
                }
            )

            if serializer.is_valid():
                serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response("Seeding dos robos feito com sucesso", status=status.HTTP_201_CREATED)
    
    def delete(self, request, format=None):
        Robos.objects.all().delete()
        return Response("Robos excluídos com sucesso", status=status.HTTP_200_OK)


class ParametrosAPI(APIView):
    def get(self, request, format=None):
        parametros = get_list_or_404(Parametros)
        serializer = ParametrosSerializer(parametros, many=True)
        if serializer:
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request, format=None):
        serializer = ParametrosSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, format=None):
        parametro = get_object_or_404(Parametros, pk=request.data['id'])
        parametro.delete()
        return Response(f"Parametro {parametro.nome} excluídos com sucesso", status=status.HTTP_200_OK)
    
class RobosParametrosAPI(APIView):
    def get(self, request, id_robo, format=None):
        try:
            robo = Robos.objects.get(id=id_robo)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        
        try:
            robo_parametros = RobosParametros.objects.filter(robo=id_robo)

            if not robo_parametros:
                return Response("O robo não possui parâmetros definidos", status=status.HTTP_204_NO_CONTENT)

            serializer = RobosParametrosSerializer(robo_parametros, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request, id_robo, format=None):
        try:
            robo = Robos.objects.get(id=id_robo)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)

        try:
            robo_parametros = RobosParametros.objects.filter(robo=id_robo)

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
        
    def delete(self, request, format=None):
        parametro = get_object_or_404(RobosParametros, pk=request.data['id'])
        parametro.delete()
        return Response(f"Parametro {parametro.nome} excluído com sucesso", status=status.HTTP_200_OK)

class RotinasAPI(APIView):
    def get(self, request, id_robo, format=None):
        rotinas = get_list_or_404(Rotinas, robo=id_robo)
        serializer = RotinasSerializer(rotinas, many=True)
        if serializer:
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, format=None):
        serializer = RotinasSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ExecutarRoboAPI(APIView):
    def post(self, request, id_robo, format=None):
        try:
            robo = Robos.objects.get(id=id_robo)
            if not robo:
                raise Exception("O robo não foi encontrado")
            
            parametros = {}
            for key, value in request.data.items():
                parametros[key] = value

            robo_parametros = RobosParametros.objects.filter(robo=id_robo)

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

            script_path = f"c:/Users/ACP/projetos/robo_{nome_robo}"
            robo_processo = subprocess.Popen(['powershell', '-Command', f"& cd '{script_path}'; ./.venv/Scripts/Activate.ps1; python robo_{nome_robo}.py"], shell=True, creationflags=subprocess.DETACHED_PROCESS, start_new_session=True)

            sleep(3)
            parametros_json = json.dumps(parametros)
            print(f"Req realizada")
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


