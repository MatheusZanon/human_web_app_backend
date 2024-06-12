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
import json


@permission_classes([IsAuthenticated])
class ClientesFinanceiroViewset(viewsets.ModelViewSet):
    queryset = ClientesFinanceiro.objects.all()    
    serializer_class = ClientesFinanceiroSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [SearchFilter]
    search_fields = ['nome_razao_social']

    def create(self, request, *args, **kwargs):
        try:
            cliente_serializer = ClientesFinanceiroSerializer(data=request.data)
            if cliente_serializer.is_valid():
                cliente_serializer.save()
                data = cliente_serializer.data
                return Response(data, status=status.HTTP_201_CREATED)
            else:
                return Response(cliente_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def list(self, request, *args, **kwargs):
        try:
            is_active = request.query_params.get('is_active')
            if is_active is None:
                queryset = ClientesFinanceiro.objects.all().order_by('nome_razao_social')
            else:
                is_active = True if is_active == 'true' else False
                queryset = ClientesFinanceiro.objects.filter(is_active=is_active).order_by('nome_razao_social')
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = ClientesFinanceiroSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = ClientesFinanceiroSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, *args, **kwargs):
        try:
            cliente = ClientesFinanceiro.objects.get(id=kwargs['pk'])

            # Atualizar campos do cliente
            cliente_data = {}
            if 'nome_razao_social' in request.data:
                cliente_data['nome_razao_social'] = request.data['nome_razao_social']
            if 'nome_fantasia' in request.data:
                cliente_data['nome_fantasia'] = request.data['nome_fantasia']
            if 'email' in request.data:
                cliente_data['email'] = request.data['email']
            if 'cnpj' in request.data:
                cliente_data['cnpj'] = request.data['cnpj']
            if 'cpf' in request.data:
                cliente_data['cpf'] = request.data['cpf']
            if 'phone' in request.data:
                cliente_data['phone'] = request.data['phone']
            if 'regiao' in request.data:
                cliente_data['regiao'] = request.data['regiao']

            # Validar e salvar Cliente
            cliente_serializer = ClientesFinanceiroSerializer(cliente, data=cliente_data, partial=True)
            if cliente_serializer.is_valid() and cliente_serializer.is_valid():
                cliente_serializer.save()
                data = cliente_serializer.data
                return Response(data, status=status.HTTP_200_OK)
            else:
                errors = cliente_serializer.errors
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        except cliente.DoesNotExist:
            return Response({"error": "Usuário não encontrado"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as error:
            return Response({"error": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['put'], url_path='ativar')
    def activate_cliente(self, request, pk=None):
        try:
            cliente = ClientesFinanceiro.objects.get(id=pk)
            cliente.is_active = True
            cliente.save()
            return Response(status=status.HTTP_200_OK)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['put'], url_path='desativar')
    def desactivate_cliente(self, request, pk=None):
        try:
            cliente = ClientesFinanceiro.objects.get(id=pk)
            cliente.is_active = False
            cliente.save()
            return Response(status=status.HTTP_200_OK)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['get'], url_path='folha_ponto')
    def listar_folha_ponto(self, request):
        try:
            nome_razao_social = request.query_params.get('nome_razao_social')
            cnpj = request.query_params.get('cnpj')
            cpf = request.query_params.get('cpf')

            if nome_razao_social and cnpj or nome_razao_social and cpf or cnpj and cpf or nome_razao_social and cnpj and cpf:
                return Response({"error": "Por favor, insira apenas um dos seguintes filtros 'nome_razao_social', 'cnpj', 'cpf'"}, status=status.HTTP_400_BAD_REQUEST)

            if nome_razao_social:
                folha_ponto = ClientesFinanceiroFolhaPonto.objects.get(cliente__is_active=True, cliente__nome_razao_social=nome_razao_social)

                serializer = ClienteFinanceiroFolhaPontoSerializer(folha_ponto)
                if serializer:
                    return Response(serializer.data, status=status.HTTP_200_OK)
            
            if cnpj:
                folha_ponto = ClientesFinanceiroFolhaPonto.objects.get(cliente__is_active=True, cliente__cnpj=cnpj)

                serializer = ClienteFinanceiroFolhaPontoSerializer(folha_ponto)
                if serializer:
                    return Response(serializer.data, status=status.HTTP_200_OK)

            if cpf:
                folha_ponto = ClientesFinanceiroFolhaPonto.objects.get(cliente__is_active=True, cliente__cpf=cpf)

                serializer = ClienteFinanceiroFolhaPontoSerializer(folha_ponto)
                if serializer:
                    return Response(serializer.data, status=status.HTTP_200_OK)
                        
            folha_ponto = ClientesFinanceiroFolhaPonto.objects.filter(cliente__is_active=True).order_by('cliente__nome_razao_social')
            
            page = self.paginate_queryset(folha_ponto)

            if page is not None:
                serializer = ClienteFinanceiroFolhaPontoSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = ClienteFinanceiroFolhaPontoSerializer(folha_ponto, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='folha_ponto')
    def folha_ponto(self, request, pk=None):
        try:
            folha_ponto = ClientesFinanceiroFolhaPonto.objects.filter(cliente_id=pk, cliente__is_active=True).order_by('cliente__nome_razao_social')

            if not folha_ponto:
                return Response({"error": "Cliente não possui registro para gerar folha"}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = ClienteFinanceiroFolhaPontoSerializer(folha_ponto, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='folha_ponto/criar')
    def create_folha_ponto(self, request, pk=None):
        try:
            data = {
                'cliente': pk,
            }

            if not 'registrado' in request.data:
                return Response({"error": "O campo 'registrado' é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
            data['registrado'] = request.data['registrado']
            
            if not 'colaborador' in request.data:
                return Response({"error": "O campo 'colaborador' é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
            data['colaborador'] = request.data['colaborador']

            folha_ponto_serializer = ClienteFinanceiroFolhaPontoSerializer(data=data)

            if ClientesFinanceiroFolhaPonto.objects.filter(cliente=pk).exists():
                return Response({"error": "O  já possui um registo de folha de ponto criada!"}, status=status.HTTP_400_BAD_REQUEST)

            if folha_ponto_serializer.is_valid():
                folha_ponto_serializer.save()
                return Response(folha_ponto_serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(folha_ponto_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['put'], url_path='folha_ponto/atualizar')
    def update_folha_ponto(self, request, pk=None):
        try:
            folha_ponto = ClientesFinanceiroFolhaPonto.objects.get(cliente=pk)
            folha_ponto_serializer = ClienteFinanceiroFolhaPontoSerializer(folha_ponto, data=request.data, partial=True)
            if folha_ponto_serializer.is_valid():
                folha_ponto_serializer.save()
                return Response(folha_ponto_serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(folha_ponto_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['delete'], url_path='folha_ponto/deletar')
    def delete_folha_ponto(self, request, pk=None):
        try:
            folha_ponto = ClientesFinanceiroFolhaPonto.objects.get(cliente=pk)
            folha_ponto.delete()
            return Response(status=status.HTTP_200_OK)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@permission_classes([IsAuthenticated])
class ClientesFinanceiroValoresViewset(viewsets.ModelViewSet):
    queryset = ClientesFinanceiroValores.objects.all()    
    serializer_class = ClientesFinanceiroValoresSerializer
    pagination_class = LimitOffsetPagination

    @action(detail=True, methods=['get'], url_path='profile')
    def profile(self, request, pk=None):
        try:
            print(request.user)
            cliente = ClientesFinanceiro.objects.get(id=pk)
            serializer = ClientesFinanceiroSerializer(cliente)
            if serializer.is_valid():
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
    
    @action(detail=False, methods=['put'], url_path='vales_sst/atualizar')
    def update_vales_sst(self, request):
        try:
            mes = request.data.get('mes')
            ano = request.data.get('ano')
            if mes == 'NaN':
                mes = None
            if ano == 'NaN':
                ano = None

            nome_razao_social = request.data.get('nome_razao_social')
            vale_transporte = request.data.get('vale_transporte')
            vale_refeicao = request.data.get('vale_refeicao')
            saude_seguranca_trabalho = request.data.get('saude_seguranca_trabalho')
            mensal_ponto_elet = request.data.get('mensal_ponto_elet')
            assinat_eletronica = request.data.get('assinat_eletronica')

            data = {
                'mes': mes,
                'ano': ano,
                'vale_transporte': vale_transporte,
                'vale_refeicao': vale_refeicao,
                'saude_seguranca_trabalho': saude_seguranca_trabalho,
                'mensal_ponto_elet': mensal_ponto_elet,
                'assinat_eletronica': assinat_eletronica,
            }

            if not nome_razao_social:
                return Response({'nome_razao_social': ['Este campo não pode ser vazio.']}, status=status.HTTP_400_BAD_REQUEST)

            try:
                cliente = ClientesFinanceiro.objects.get(nome_razao_social=nome_razao_social)
            except ClientesFinanceiro.DoesNotExist:
                return Response({'nome_razao_social': ['Cliente não encontrado.']}, status=status.HTTP_404_NOT_FOUND)

            vale = ClientesFinanceiroValores.objects.filter(
                mes=mes,
                ano=ano,
                cliente=cliente
            ).first()

            if vale:
                # Vale existe, atualiza-lo
                serializer = ClientesFinanceiroValoresSerializer(vale, data=data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Vale não existe, cria-lo
                serializer = ClientesFinanceiroValoresSerializer(data=data)
                if serializer.is_valid():
                    serializer.save(cliente=cliente)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
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
    
    @action(detail=False, methods=['post'], url_path='reembolsos/criar')
    def create_reembolsos(self, request):
        try:
            cliente_razao_social = request.data.get('nome_razao_social')
            if not cliente_razao_social:
                return Response({'nome_razao_social': ['Este campo não pode ser vazio.']}, status=status.HTTP_400_BAD_REQUEST)
            
            cliente = ClientesFinanceiro.objects.filter(nome_razao_social=cliente_razao_social).first()
            if cliente:
                data = {
                    'mes': request.data.get('mes'),
                    'ano': request.data.get('ano'),
                    'valor': request.data.get('valor'),
                    'descricao': request.data.get('descricao'),
                }
                reembolso = ClientesFinanceiroReembolsos.objects.create(cliente=cliente, **data)
                reembolso.save()
                return Response({'message': 'Reembolso criado com sucesso.'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'Cliente não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['put'], url_path='reembolsos/atualizar')
    def update_reembolsos(self, request):
        try:
            id = request.data.get('id')
            data = {
                'mes': request.data.get('mes'),
                'ano': request.data.get('ano'),
                'valor': request.data.get('valor'),
                'descricao': request.data.get('descricao'),
            }
            reembolso = ClientesFinanceiroReembolsos.objects.filter(pk=id).first()
            if reembolso:
                serializer = ClientesFinanceiroReembolsosSerializer(reembolso, data=data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'Reembolso não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['delete'], url_path='reembolsos/deletar/(?P<reembolso_pk>[^/.]+)')
    def delete_reembolsos(self, request, reembolso_pk=None):
        try:
            id = request.data.get('id')
            reembolso = ClientesFinanceiroReembolsos.objects.filter(pk=reembolso_pk).first()
            if reembolso:
                reembolso.delete()
                return Response({'message': 'Reembolso deletado com sucesso.'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Reembolso não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
