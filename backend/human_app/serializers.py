from rest_framework import serializers
from human_app.models import *
from django.contrib.auth.models import User

# Create your serializers here.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
       model = User
       fields = '__all__'
       extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            email=validated_data['email'],
            is_active=False
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class SolicitacoesCadastroSerializer(serializers.ModelSerializer):
    class Meta:
       model = SolicitacoesCadastro
       fields = '__all__'

class FuncionariosSerializer(serializers.ModelSerializer):
    class Meta:
       model = Funcionarios
       fields = '__all__'

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