from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.views import APIView, Response
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from human_app.models import *
from human_app.serializers import *
from faker import Faker

# Create your views here.
class User(APIView):
    def post(self, request, format=None):
        try:
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response({'error': str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserAuthToken(APIView):
    def post(self, request, format=None):
        try:
            username = request.data.get("username")
            password = request.data.get("password")
            user = authenticate(username=username, password=password)
            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response({"token": token.key}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Credenciais inválidas'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as error:
            return Response({'error': str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
         

class SolicitacoesCadastroAPI(APIView):
    def get(self, request, format=None):
        try:
            solicitacoes = SolicitacoesCadastro.objects.all()
            serializer = SolicitacoesCadastroSerializer(solicitacoes, many=True)
            if serializer:
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response({'error': str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, format=None):
        try:
            serializer = SolicitacoesCadastroSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response({'error': str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FuncionariosAPI(APIView):
    def get(self, request, format=None):
        funcionarios = Funcionarios.objects.all()
        serializer = FuncionariosSerializer(funcionarios, many=True)
        if serializer:
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
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
        
class RobosAPI(APIView):
    def get(self, request, format=None):
        robos = Robos.objects.all()
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