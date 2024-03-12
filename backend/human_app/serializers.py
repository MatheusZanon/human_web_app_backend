from rest_framework import serializers
from human_app.models import ClientesFinanceiro

class ClientesFinanceiroSerializer(serializers.ModelSerializer):
    class Meta:
       model = ClientesFinanceiro
       fields = '__all__' 
