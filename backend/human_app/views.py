from django.shortcuts import render
from rest_framework.views import APIView, Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from human_app.models import ClientesFinanceiro
from human_app.models import ClientesFinanceiroValores
from human_app.serializers import ClientesFinanceiroSerializer
from human_app.serializers import ClientesFinanceiroValoresSerializer

# Create your views here.
class ClientesFinanceiroAPI(APIView):
    def get(self, request, format=None):
        clientes = ClientesFinanceiro.objects.all()
        serializer = ClientesFinanceiroSerializer(clientes, many=True)
        return Response(serializer.data, status=HTTP_200_OK)
    
class ClientesFinanceiroValoresAPI(APIView):
    def get(self, request, format=None):
        clientes = ClientesFinanceiroValores.objects.all()
        serializer = ClientesFinanceiroValoresSerializer(clientes, many=True)
        return Response(serializer.data, status=HTTP_200_OK)