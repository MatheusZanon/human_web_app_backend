from rest_framework import serializers

from .models import *


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

class ParametrosSerializer(serializers.ModelSerializer):
    class Meta:
       model = Parametros
       fields = '__all__'

class RobosParametrosSerializer(serializers.ModelSerializer):
    parametro_info = ParametrosSerializer(source='parametro', read_only=True)
    class Meta:
       model = RobosParametros
       fields = '__all__'

class ExecutarRoboSerializer(serializers.ModelSerializer):
    class Meta:
       model = RobosParametros
       fields = '__all__'

class FuncionariosSerializer(serializers.ModelSerializer):
    class Meta:
       model = Funcionarios
       fields = '__all__'
