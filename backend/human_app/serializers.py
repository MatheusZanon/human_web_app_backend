from rest_framework import serializers

from human_app.models import ClientesFinanceiro
from human_app.models import ClientesFinanceiroValores
from human_app.models import Funcionarios

class ClientesFinanceiroSerializer(serializers.ModelSerializer):
    class Meta:
       model = ClientesFinanceiro
       fields = '__all__' 

class ClientesFinanceiroValoresSerializer(serializers.ModelSerializer):
    class Meta:
       model = ClientesFinanceiroValores
       fields = '__all__' 


class FuncionariosSerializer(serializers.ModelSerializer):
    class Meta:
       model = Funcionarios
       fields = '__all__'