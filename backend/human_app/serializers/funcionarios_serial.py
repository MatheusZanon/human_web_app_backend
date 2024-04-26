from rest_framework import serializers
from human_app.models import Funcionarios
from ..serializers.user_serial import UserSerializer

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