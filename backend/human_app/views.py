from django.shortcuts import render
from rest_framework.views import APIView, Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_201_CREATED
from django.shortcuts import get_object_or_404, get_list_or_404
from human_app.models import *
from human_app.serializers import *
from faker import Faker

# Create your views here.
class ClientesFinanceiroAPI(APIView):
    def get(self, request, format=None):
        clientes = ClientesFinanceiro.objects.all()
        serializer = ClientesFinanceiroSerializer(clientes, many=True)
        if serializer:
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        
class ClientesFinanceiroValoresAPI(APIView):
    def get(self, request, format=None):
        clientes = ClientesFinanceiroValores.objects.all()
        serializer = ClientesFinanceiroValoresSerializer(clientes, many=True)
        if serializer:
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

class RoboAPI(APIView):
    def get(self, request, id_robo, format=None):
        try:
            robo = Robos.objects.get(id=id_robo)

            serializer = RobosSerializer(robo)

            robo_data = serializer.data

            robo_parametros = RobosParametros.objects.filter(robo=id_robo)
            if not robo_parametros:
                raise Exception("Os parâmetros do robo não foram encontrados")
            
            parametros_serializer = RobosParametrosSerializer(robo_parametros, many=True)
            
            if not parametros_serializer:
                raise Exception("Os parâmetros do robo não foram encontrados")
            
            parametros_data = parametros_serializer.data

            robo_data["parametros"] = parametros_data

            return Response(robo_data, status=HTTP_200_OK)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=HTTP_404_NOT_FOUND)

class RobosAPI(APIView):
    def get(self, request, format=None):
        robos = get_list_or_404(Robos)
        serializer = RobosSerializer(robos, many=True)

        if serializer:
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
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
                return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        return Response("Seeding dos robos feito com sucesso", status=HTTP_201_CREATED)
    
    def delete(self, request, format=None):
        Robos.objects.all().delete()
        return Response("Robos excluídos com sucesso", status=HTTP_200_OK)

class ParametrosAPI(APIView):
    def get(self, request, format=None):
        parametros = get_list_or_404(Parametros)
        serializer = ParametrosSerializer(parametros, many=True)
        if serializer:
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
    
    def post(self, request, format=None):
        serializer = ParametrosSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
    
    def delete(self, request, format=None):
        parametro = get_object_or_404(Parametros, pk=request.data['id'])
        parametro.delete()
        return Response(f"Parametro {parametro.nome} excluídos com sucesso", status=HTTP_200_OK)
    
class RobosParametrosAPI(APIView):
    def get(self, request, id_robo, format=None):
        try:
            robo = Robos.objects.get(id=id_robo)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=HTTP_404_NOT_FOUND)
        
        try:
            robo_parametros = RobosParametros.objects.filter(robo=id_robo)

            if not robo_parametros:
                raise Exception("Os parâmetros do robo não foram encontrados")

            serializer = RobosParametrosSerializer(robo_parametros, many=True)
            return Response(serializer.data, status=HTTP_200_OK)
        except Exception as error:
            return Response(f"{error}", status=HTTP_404_NOT_FOUND)
    
    def post(self, request, format=None):
        serializer = RobosParametrosSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
    def delete(self, request, format=None):
        parametro = get_object_or_404(RobosParametros, pk=request.data['id'])
        parametro.delete()
        return Response(f"Parametro {parametro.nome} excluído com sucesso", status=HTTP_200_OK)

class FuncionariosAPI(APIView):
    def get(self, request, format=None):
        funcionarios = Funcionarios.objects.all()
        serializer = FuncionariosSerializer(funcionarios, many=True)
        if serializer:
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
