from rest_framework.views import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from ..serializers.clientes_financeiro_serial import *
from django.db.models import Case, When, Sum, Value, FloatField, IntegerField, F
from django.db.models.functions import Coalesce, Round
from django_filters import rest_framework as filters
from ..filters import IntervaloDeTempoFilter
from human_app.models import ClientesFinanceiro, ClientesFinanceiroValores


@permission_classes([IsAuthenticated])
class DashboardViewset(viewsets.ModelViewSet):
    queryset = ClientesFinanceiroValores.objects.all()
    serializer_class = ClientesFinanceiroValoresSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = IntervaloDeTempoFilter

    @action(detail=False, methods=['get'], url_path='anos')
    def anos(self, request):
        try:
            anos = ClientesFinanceiroValores.objects.values('ano').distinct()
            return Response(anos, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='clientes_financeiro')
    def clientesFinanceiro(self, request):
        try:
            clientes_financeiro = ClientesFinanceiro.objects.all()
            serializer = ClientesFinanceiroSerializer(clientes_financeiro, many=True)
            
            if serializer:
                return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='provisoes_direitos_trabalhistas_3487')
    def provisoesDireitosTrabalhistas3487(self, request):
        try:
            has_nome_razao_social = 'nome_razao_social' in request.query_params and request.query_params['nome_razao_social'] != ''
            has_ano = 'ano' in request.query_params and request.query_params['ano'] != '' and request.query_params['ano'] != '0'

            if not has_nome_razao_social or not has_ano:
                return Response("O cliente financeiro não foi encontrado", status=status.HTTP_404_NOT_FOUND)
            
            if has_nome_razao_social and has_ano:
                valores = ClientesFinanceiro.objects.filter(nome_razao_social=request.query_params['nome_razao_social']).select_related('valores').annotate(
                    mes=Case(
                        When(valores__ano=request.query_params['ano'], then='valores__mes'),
                        output_field=IntegerField()
                    ),
                    valor=Round(
                        Coalesce(
                            F('valores__soma_salarios_provdt') * 0.3487,
                            Value(0, output_field=FloatField())
                        ),
                        2
                    ),
                ).values('mes', 'valor')

                if not valores:
                    return Response("O cliente financeiro não foi encontrado", status=status.HTTP_404_NOT_FOUND)

                provisoes = list(valores)
                provisoes.sort(key=lambda x: x['mes'])
                
                serializer = ClientesFinanceiroProvisao3487Serializer(data=provisoes, many=True)
                
                if serializer.is_valid():
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='provisoes_direitos_trabalhistas_0926')
    def provisoesDireitosTrabalhistas0926(self, request):
        try:
            has_nome_razao_social = 'nome_razao_social' in request.query_params and request.query_params['nome_razao_social'] != ''
            has_ano = 'ano' in request.query_params and request.query_params['ano'] != '' and request.query_params['ano'] != '0'

            if not has_nome_razao_social or not has_ano:
                return Response("O cliente financeiro não foi encontrado", status=status.HTTP_404_NOT_FOUND)
            
            if has_nome_razao_social and has_ano:
                valores = ClientesFinanceiro.objects.filter(nome_razao_social=request.query_params['nome_razao_social']).select_related('valores').annotate(
                    mes=Case(
                        When(valores__ano=request.query_params['ano'], then='valores__mes'),
                        output_field=IntegerField()
                    ),
                    valor=Round(
                        Coalesce(
                            F('valores__soma_salarios_provdt') * 0.0926,
                            Value(0, output_field=FloatField())
                        ),
                        2
                    ),
                ).values('mes', 'valor')

                if not valores:
                    return Response("O cliente financeiro não foi encontrado", status=status.HTTP_404_NOT_FOUND)

                provisoes = list(valores)
                provisoes.sort(key=lambda x: x['mes'])
                
                serializer = ClientesFinanceiroProvisao0926Serializer(data=provisoes, many=True)
                
                if serializer.is_valid():
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='taxa_administracao')
    def taxaAdministracao(self, request):
        try:
            has_nome_razao_social = 'nome_razao_social' in request.query_params and request.query_params['nome_razao_social'] != ''
            has_ano = 'ano' in request.query_params and request.query_params['ano'] != '' and request.query_params['ano'] != '0'

            if not has_nome_razao_social or not has_ano:
                return Response("O cliente financeiro não foi encontrado", status=status.HTTP_404_NOT_FOUND)
            
            if has_nome_razao_social and has_ano:
            
                # Selecione todas as colunas da tabela ClientesFinanceiro e faça um join com ClientesFinanceiroValores
                taxa_adm = ClientesFinanceiro.objects.filter(nome_razao_social=request.query_params['nome_razao_social']).select_related('valores').annotate(
                    taxa_administracao=Coalesce(
                        Case(When(
                            valores__ano=request.query_params['ano'], then='valores__percentual_human'),
                            output_field=FloatField(),
                        ),
                        Value(0, output_field=FloatField()),
                    ),
                    mes=Case(
                        When(valores__ano=request.query_params['ano'], then='valores__mes'),
                        output_field=IntegerField()
                    )
                ).values('nome_razao_social', 'taxa_administracao', 'mes')

                if not taxa_adm:
                    return Response("O cliente financeiro não foi encontrado", status=status.HTTP_404_NOT_FOUND)
                
                jsonData = list(taxa_adm)
                jsonData.sort(key=lambda x: x['mes'])
                print(jsonData)
                serializer = ClientesFinanceiroTaxaAdmSerializer(data=jsonData, many=True)

                if serializer.is_valid():
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print(error)
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['get'], url_path='economia_liquida')
    def economiaLiquida(self, request):
        try:
            economia_liquida = []
            # Verifique se ao menos um parâmetro é fornecido
            has_nome = 'nome_razao_social' in request.query_params and request.query_params['nome_razao_social'] != ''
            has_mes = 'mes' in request.query_params and request.query_params['mes'] != '' and request.query_params['mes'] != '0'
            has_ano = 'ano' in request.query_params and request.query_params['ano'] != '' and request.query_params['ano'] != '0'

            if not has_nome and not has_mes and not has_ano:
                # Se nenhum parâmetro for fornecido, retorne um erro
                return Response("Ao menos o mês e o ano devem ser informado", status=status.HTTP_400_BAD_REQUEST)

            # Filtrar com base nos parâmetros opcionais
            if has_nome and has_ano and not has_mes:
                cliente = ClientesFinanceiro.objects.filter(nome_razao_social=request.query_params['nome_razao_social']).first()

                if not cliente:
                    return Response("O cliente financeiro não foi encontrado", status=status.HTTP_404_NOT_FOUND)

                valores_cliente = ClientesFinanceiroValores.objects.filter(cliente=cliente.pk, ano=request.query_params['ano']).all()

                for valor in valores_cliente:
                    economia_liquida.append({
                        'nome_razao_social': valor.cliente.nome_razao_social,
                        'economia_liquida': valor.economia_liquida,
                        'regiao': valor.cliente.regiao,
                        'mes': valor.mes,
                        'ano': valor.ano
                    })

                economia_liquida.sort(key=lambda x: x['mes'])
                return Response(economia_liquida, status=status.HTTP_200_OK)

            # Caso o mes e o ano sejam fornecidos, mas não o nome_razao_social
            if has_mes and has_ano and not has_nome:
                clientes = ClientesFinanceiro.objects.filter().all()
                valores_clientes = ClientesFinanceiroValores.objects.filter(mes=request.query_params['mes'], ano=request.query_params['ano'], cliente__in=clientes).all()

                for valor in valores_clientes:
                    economia_liquida.append({
                        'nome_razao_social': valor.cliente.nome_razao_social,
                        'economia_liquida': valor.economia_liquida,
                        'regiao': valor.cliente.regiao,
                        'mes': valor.mes,
                        'ano': valor.ano
                    })

                economia_liquida.sort(key=lambda x: x['nome_razao_social'])
                return Response(economia_liquida, status=status.HTTP_200_OK)

            return Response("Uma combinação não esperada de parâmetros foi recebida", status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print(error)
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='economia_liquida/total')
    def economiaLiquidaTotal(self, request):
        try:
            economia_liquida = []
            has_ano = 'ano' in request.query_params and request.query_params['ano'] != '' and request.query_params['ano'] != '0'
            is_regional = 'regional' in request.query_params and request.query_params['regional'] != ''

            if not has_ano:
                return Response("O ano deve ser informado", status=status.HTTP_400_BAD_REQUEST)
            
            if not is_regional:
                clientes = ClientesFinanceiro.objects.filter().all()
                valores_clientes = ClientesFinanceiroValores.objects.filter(ano=request.query_params['ano'], cliente__in=clientes).all()
                
                total_economia_mensal = valores_clientes.values('mes').annotate(Sum('economia_liquida'))

                for item in total_economia_mensal:
                    economia_liquida.append({
                        'economia_liquida': round(item['economia_liquida__sum'], 2),
                        'mes': item['mes'],
                        'ano': request.query_params['ano'],
                    })

                economia_liquida.sort(key=lambda x: x['mes'])

                return Response(economia_liquida, status=status.HTTP_200_OK)
            
            if request.query_params['regional'] == 'true':
                eco_liquida_regional = (
                    ClientesFinanceiro.objects
                    .prefetch_related('valores')  # Use prefetch_related para pegar campos de ClientesFinanceiroValores
                    .filter(valores__mes=request.query_params.get('mes'), valores__ano=request.query_params.get('ano'))
                    .values('regiao')  # Agrupar por região
                    .annotate(
                        economia_liquida=Round(Coalesce(
                            Sum('valores__economia_liquida'),
                            Value(0.0, output_field=FloatField())
                        ), 2)
                    )
                    .order_by('regiao')  # Ordenar por região
                )

                economia_liquida = list(eco_liquida_regional)

                return Response(economia_liquida, status=status.HTTP_200_OK)
            
            return Response("Uma combinação não esperada de parâmetros foi recebida", status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print(error)
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='vales_sst')
    def vales_sst(self, request):
        try:
            vales_sst = self.filter_queryset(self.get_queryset())
            filtered_vales_sst = self.filterset_class(request.query_params, queryset=vales_sst).qs
            serializer = ClientesFinanceiroValesSSTSerializer(filtered_vales_sst, many=True)

            if serializer:
                data = serializer.data
                totalDict = {}
                for item in data:
                    nome_razao_social = item['nome_razao_social']
                    if nome_razao_social not in totalDict:
                        totalDict[nome_razao_social] = {'name': nome_razao_social}
                    total = totalDict[nome_razao_social]
                    for key, value in item.items():
                        if key != 'mes' and key != 'ano' and key != 'id' and key != 'nome_razao_social':
                            if key not in total:
                                total[key] = 0.0
                            total[key] += value

                result = list(totalDict.values())
                return Response(result, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)