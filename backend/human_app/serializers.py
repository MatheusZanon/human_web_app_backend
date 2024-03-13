from rest_framework import serializers

from human_app.models import ClientesFinanceiro
from human_app.models import ClientesFinanceiroValores
from human_app.models import Robos

class ClientesFinanceiroSerializer(serializers.ModelSerializer):
    class Meta:
       model = ClientesFinanceiro
       fields = '__all__' 

class ClientesFinanceiroValoresSerializer(serializers.ModelSerializer):
    class Meta:
       model = ClientesFinanceiroValores
       fields = '__all__' 

class RobosSerializer(serializers.ModelSerializer):
    class Meta:
       model = Robos
       fields = '__all__'