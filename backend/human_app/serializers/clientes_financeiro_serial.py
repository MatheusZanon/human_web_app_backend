from rest_framework import serializers
from human_app.models import ClientesFinanceiro, ClientesFinanceiroValores, ClientesFinanceiroReembolsos, ClientesFinanceiroFolhaPonto

class ClientesFinanceiroSerializer(serializers.ModelSerializer):
    class Meta:
       model = ClientesFinanceiro
       fields = '__all__' 

class ClientesFinanceiroValoresSerializer(serializers.ModelSerializer):
    class Meta:
       model = ClientesFinanceiroValores
       fields = '__all__' 

class ClientesFinanceiroValesSSTSerializer(serializers.ModelSerializer):
    vale_transporte = serializers.FloatField()
    assinat_eletronica = serializers.FloatField()
    vale_refeicao = serializers.FloatField()
    mensal_ponto_elet = serializers.FloatField()
    saude_seguranca_trabalho = serializers.FloatField()

    class Meta:
        model = ClientesFinanceiro
        fields = [
            'id',
            'nome_razao_social',
            'vale_transporte',
            'assinat_eletronica',
            'vale_refeicao',
            'mensal_ponto_elet',
            'saude_seguranca_trabalho'
        ]

class ClientesFinanceiroProvisao3487Serializer(serializers.ModelSerializer):
    mes=serializers.IntegerField()
    valor=serializers.FloatField()

    class Meta:
        model = ClientesFinanceiro
        fields = [
            'mes',
            'valor'
        ]

class ClientesFinanceiroProvisao0926Serializer(serializers.ModelSerializer):
    mes=serializers.IntegerField()
    valor=serializers.FloatField()

    class Meta:
        model = ClientesFinanceiro
        fields = [
            'mes',
            'valor'
        ]

class ClientesFinanceiroTaxaAdmSerializer(serializers.ModelSerializer):
    taxa_administracao = serializers.FloatField()
    mes = serializers.IntegerField()

    class Meta:
        model = ClientesFinanceiro
        fields = [
            'taxa_administracao',
            'mes'
        ]

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

class ClienteFinanceiroFolhaPontoSerializer(serializers.ModelSerializer):
    cliente = ClientesFinanceiroSerializer()
    class Meta:
       model = ClientesFinanceiroFolhaPonto
       fields = '__all__'