from rest_framework import status, viewsets
from rest_framework.views import Response
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.filters import SearchFilter
from django.db.models import Case, When, Sum, Value, FloatField
from django.db.models.functions import Coalesce
from human_app.models import ClientesFinanceiro, ClientesFinanceiroReembolsos
from ..serializers.clientes_financeiro_serial import *


@permission_classes([IsAuthenticated])
class ClientesFinanceiroViewset(viewsets.ModelViewSet):
    queryset = ClientesFinanceiro.objects.all()    
    serializer_class = ClientesFinanceiroSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [SearchFilter]
    search_fields = ['nome_razao_social']

@permission_classes([IsAuthenticated])
class ClientesFinanceiroValoresViewset(viewsets.ModelViewSet):
    queryset = ClientesFinanceiroValores.objects.all()    
    serializer_class = ClientesFinanceiroValoresSerializer
    pagination_class = LimitOffsetPagination

    @action(detail=False, methods=['get'], url_path='vales_sst')
    def vales_sst(self, request):
        try:
            mes = request.query_params.get('mes')
            ano = request.query_params.get('ano')
            if mes == 'NaN':
                mes = None
            if ano == 'NaN':
                ano = None

            clientes = ClientesFinanceiro.objects.annotate(
                vale_transporte=Coalesce(Sum(Case(
                    When(valores__mes=mes, valores__ano=ano, then='valores__vale_transporte'),
                    default=Value(0, output_field=FloatField()),
                    output_field=FloatField()
                    )), Value(0, output_field=FloatField())),
                assinat_eletronica=Coalesce(Sum(Case(
                    When(valores__mes=mes, valores__ano=ano, then='valores__assinat_eletronica'),
                    default=Value(0, output_field=FloatField()),
                    output_field=FloatField()
                )), Value(0, output_field=FloatField())),
                vale_refeicao=Coalesce(Sum(Case(
                    When(valores__mes=mes, valores__ano=ano, then='valores__vale_refeicao'),
                    default=Value(0, output_field=FloatField()),
                    output_field=FloatField()
                )), Value(0, output_field=FloatField())),
                mensal_ponto_elet=Coalesce(Sum(Case(
                    When(valores__mes=mes, valores__ano=ano, then='valores__mensal_ponto_elet'),
                    default=Value(0, output_field=FloatField()),
                    output_field=FloatField()
                )), Value(0, output_field=FloatField())),
                saude_seguranca_trabalho=Coalesce(Sum(Case(
                    When(valores__mes=mes, valores__ano=ano, then='valores__saude_seguranca_trabalho'),
                    default=Value(0, output_field=FloatField()),
                    output_field=FloatField()
                )), Value(0, output_field=FloatField()))
            )

            page = self.paginate_queryset(clientes)
            if page is not None:
                serializer = ClientesFinanceiroValesSSTSerializer(page, many=True)
                vales_data = self.get_paginated_response(serializer.data) 
                return Response(vales_data.data, status=status.HTTP_200_OK)
        except Exception as error:
            print(error)
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='reembolsos')
    def reembolsos(self, request):
        try:
            mes = request.query_params.get('mes')
            ano = request.query_params.get('ano')
            if mes == 'NaN':
                mes = None
            if ano == 'NaN':
                ano = None
            reembolsos = ClientesFinanceiroReembolsos.objects.filter(mes=mes).order_by('mes', 'ano')
            page = self.paginate_queryset(reembolsos)
            if page is not None:    
                serializer = ClientesFinanceiroReembolsosSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)