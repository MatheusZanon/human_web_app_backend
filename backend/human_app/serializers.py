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

class FuncionariosSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
       model = Funcionarios
       fields = ['user', 'rg', 'cpf', 'telefone_celular']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user_representation = representation.pop('user')
        for key in user_representation:
            representation[key] = user_representation[key]
        return representation

class ClientesFinanceiroSerializer(serializers.ModelSerializer):
    class Meta:
       model = ClientesFinanceiro
       fields = '__all__' 

class ClientesFinanceiroValoresSerializer(serializers.ModelSerializer):
    class Meta:
       model = ClientesFinanceiroValores
       fields = '__all__' 

class ClientesFinanceiroValesSSTSerializer(serializers.ModelSerializer):
    cliente = ClientesFinanceiroSerializer()
    
    class Meta:
       model = ClientesFinanceiroValores
       fields = ['id', 'cliente', 'vale_transporte', 'assinat_eletronica', 'vale_refeicao', 'mensal_ponto_elet', 'saude_seguranca_trabalho']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        cliente_representation = representation.pop('cliente')
        cliente_nome = f"{cliente_representation['nome_razao_social']}"
        representation['nome_razao_social'] = cliente_nome
        return representation


class ClientesFinanceiroReembolsosSerializer(serializers.ModelSerializer):
    cliente = ClientesFinanceiroSerializer()
    
    class Meta:
       model = ClientesFinanceiroReembolsos
       fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        cliente_representation = representation.pop('cliente')
        cliente_nome = f"{cliente_representation['nome_razao_social']}"
        representation['nome_razao_social'] = cliente_nome
        return representation

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

class RotinasSerializer(serializers.ModelSerializer):
    class Meta:
       model = Rotinas
       fields = '__all__'