from django.shortcuts import render
from rest_framework.views import APIView, Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from django.shortcuts import get_object_or_404
from human_app.models import ClientesFinanceiro, ClientesFinanceiroValores, Robos
from human_app.serializers import ClientesFinanceiroSerializer, ClientesFinanceiroValoresSerializer, RobosSerializer
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
        
class RobosAPI(APIView):
    def get(self, request, format=None):
        robos = Robos.objects.all()
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
        return Response("Seeding dos robos feito com sucesso", status=HTTP_200_OK)
    
    def delete(self, request, format=None):
        Robos.objects.all().delete()
        return Response("Robos excluídos com sucesso", status=HTTP_200_OK)