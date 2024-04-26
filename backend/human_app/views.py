from rest_framework import status, viewsets
from rest_framework.views import APIView, Response
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.filters import SearchFilter
from django.db.models import Case, When, Sum, Value, FloatField, IntegerField, F
from django.db.models.functions import Coalesce
from django.contrib.auth.models import User, Group
from .filters import IntervaloDeTempoFilter
from django_filters import rest_framework as filters
from django.shortcuts import get_object_or_404, get_list_or_404
from django.http import JsonResponse
from django.db.models import Sum
from human_app.models import *
from human_app.serializers import *
import subprocess
from datetime import datetime
from time import sleep
import requests
import json
import logging

logger = logging.getLogger('django')  # Usando o logger configurado para o Django

# Create your views and viewsets here.
class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        try:
            if response.status_code == 200:
                access_token = response.data.get('access')
                refresh_token = response.data.get('refresh')
                response.set_cookie(
                    key='access_token',
                    value=access_token,
                    httponly=True,
                    samesite='Lax',
                    path='/',
                    secure=False  # True em produção
                )
                del response.data['refresh']  # Remova o refresh token da resposta
            return response
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class UserViewset(viewsets.ModelViewSet):
    queryset = User.objects.all()    
    serializer_class = UserSerializer

    @action(detail=False, methods=['get'], url_path='login')
    def login(self, request, *args, **kwargs):
        try:
            user = Funcionarios.objects.get(user=request.user)
            serializer = FuncionariosSerializer(user)
            if serializer:
                user_data = serializer.data
                groups = [group.name for group in Group.objects.filter(user=request.user).all()]
                user_data['groups'] = groups
                del user_data['user_permissions']
                return Response(user_data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response({'error': str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # CADASTRO  
    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        email = request.data.get('email')
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Esse nome de usuário já existe.'}, status=status.HTTP_400_BAD_REQUEST)
        elif User.objects.filter(email=email).exists():
            return Response({'error': 'Esse email já existe.'}, status=status.HTTP_400_BAD_REQUEST) 
        try:
            user = None
            user_serializer = UserSerializer(data=request.data)
            if user_serializer.is_valid():
                user = user_serializer.save()
                funcionario_data = {
                    'rg': request.data.get('rg'),
                    'cpf': request.data.get('cpf'),
                    'telefone_celular': request.data.get('telefone_celular'),
                }
                funcionario = Funcionarios.objects.create(user=user, **funcionario_data)
                funcionario.save()
                return Response(user_serializer.data, status=status.HTTP_201_CREATED)
            else:
                print("USER SERIALIZER INVALIDO")
                return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response({'error': str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@permission_classes([IsAuthenticated])
class SessionVerifyToken(APIView):
    def get(self, request, format=None):
        return Response({"Token: Válido"}, status=status.HTTP_200_OK)
    
class SessionLogout(APIView):
    def post(self, request):
        response = JsonResponse({"detail": "Logout realizado com sucesso."}, status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
        
@permission_classes([IsAuthenticated])
class GroupsViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

@permission_classes([IsAuthenticated])
class FuncionarioViewset(viewsets.ModelViewSet):
    queryset = Funcionarios.objects.all()    
    serializer_class = FuncionariosSerializer
    
    def retrieve(self, request, pk=None):
        try:
            user = Funcionarios.objects.get(user=pk)
            serializer = FuncionariosSerializer(user)
            if serializer:
                user_data = serializer.data
                groups = [group.name for group in Group.objects.filter(user=user.user.id).all()]
                user_data['groups'] = groups
                del user_data['user_permissions']
                return Response(user_data, status=status.HTTP_200_OK)
        except Funcionarios.DoesNotExist:
            return Response({'error': 'Funcionário não encontrado'}, status=status.HTTP_404_NOT_FOUND)
    
    def list(self, request, *args, **kwargs):
        try:
            funcionarios = Funcionarios.objects.all()
            serializer = FuncionariosSerializer(funcionarios, many=True)
            if serializer:
                funcionarios_data = serializer.data
                index = 0
                for funcionario in funcionarios_data:
                    groups = [group.name for group in Group.objects.filter(user=funcionario.get('id')).all()]
                    funcionario['groups'] = groups
                    del funcionario['user_permissions']
                    funcionarios_data[index] = funcionario
                    index += 1
                return Response(funcionarios_data, status=status.HTTP_200_OK)
        except Funcionarios.DoesNotExist:
            return Response({'error': 'Funcionários não encontrado'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['put'], url_path='activate')
    def activate_user(self, request, pk=None):
        try:
            user = User.objects.filter(id=pk).get()

            ids = request.data['id']
            for id in ids:
                group = Group.objects.get(id=id)
                user.groups.add(group)
                user.is_active = True
                if group.name == 'ADMIN':
                    user.is_staff = True
                user.save()
            return Response(f"O usuário {user.username} foi ativado com sucesso", status=status.HTTP_204_NO_CONTENT)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['put'], url_path='deactivate')
    def desactivate_user(self, request, pk=None):
        try:
            user = User.objects.filter(id=pk).get()
            user.is_active = False
            user.save()
            return Response(f"O usuário {user.username} foi desativado com sucesso", status=status.HTTP_204_NO_CONTENT)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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
                    valor=Coalesce(
                        Case(
                            When(valores__ano=request.query_params['ano'], then='valores__soma_salarios_provdt'),
                            output_field=FloatField()
                        ),
                        Value(0, output_field=FloatField())
                    )
                ).values('mes', 'valor')

                if not valores:
                    return Response("O cliente financeiro não foi encontrado", status=status.HTTP_404_NOT_FOUND)

                provisoes = list(valores)
                provisoes = list(map(lambda x: {'mes': x['mes'], 'valor': round(x['valor'] * 0.3487, 2)}, provisoes))
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
                    valor=Coalesce(
                        Case(
                            When(valores__ano=request.query_params['ano'], then='valores__soma_salarios_provdt'),
                            output_field=FloatField()
                        ),
                        Value(0, output_field=FloatField())
                    )
                ).values('mes', 'valor')

                if not valores:
                    return Response("O cliente financeiro não foi encontrado", status=status.HTTP_404_NOT_FOUND)

                provisoes = list(valores)
                provisoes = list(map(lambda x: {'mes': x['mes'], 'valor': round(x['valor'] * 0.0926, 2)}, provisoes))
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
                serializer = ClientesFinanceiroTaxaAdmSerializer(data=jsonData, many=True)

                if serializer.is_valid():
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print(error)
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['get'], url_path='economia_formal')
    def economiaFormal(self, request):
        try:
            economia_formal = []
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
                    economia_formal.append({
                        'nome_razao_social': valor.cliente.nome_razao_social,
                        'economia_formal': valor.economia_formal,
                        'regiao': valor.cliente.regiao,
                        'mes': valor.mes,
                        'ano': valor.ano
                    })

                economia_formal.sort(key=lambda x: x['mes'])
                return Response(economia_formal, status=status.HTTP_200_OK)

            # Caso o mes e o ano sejam fornecidos, mas não o nome_razao_social
            if has_mes and has_ano and not has_nome:
                clientes = ClientesFinanceiro.objects.filter(regiao="MANAUS").all()
                valores_clientes = ClientesFinanceiroValores.objects.filter(mes=request.query_params['mes'], ano=request.query_params['ano'], cliente__in=clientes).all()

                for valor in valores_clientes:
                    economia_formal.append({
                        'nome_razao_social': valor.cliente.nome_razao_social,
                        'economia_formal': valor.economia_formal,
                        'regiao': valor.cliente.regiao,
                        'mes': valor.mes,
                        'ano': valor.ano
                    })

                economia_formal.sort(key=lambda x: x['nome_razao_social'])
                return Response(economia_formal, status=status.HTTP_200_OK)

            return Response("Uma combinação não esperada de parâmetros foi recebida", status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='economia_formal/total')
    def economiaFormalTotal(self, request):
        try:
            economia_formal = []
            has_ano = 'ano' in request.query_params and request.query_params['ano'] != '' and request.query_params['ano'] != '0'

            if not has_ano:
                return Response("O ano deve ser informado", status=status.HTTP_400_BAD_REQUEST)
            
            clientes = ClientesFinanceiro.objects.filter(regiao="MANAUS").all()
            valores_clientes = ClientesFinanceiroValores.objects.filter(ano=request.query_params['ano'], cliente__in=clientes).all()
            
            total_economia_mensal = valores_clientes.values('mes').annotate(Sum('economia_formal'))

            for item in total_economia_mensal:
                economia_formal.append({
                    'economia_formal': round(item['economia_formal__sum'], 2),
                    'mes': item['mes'],
                    'ano': request.query_params['ano']
                })

            economia_formal.sort(key=lambda x: x['mes'])

            return Response(economia_formal, status=status.HTTP_200_OK)
        except Exception as error:
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
@permission_classes([IsAuthenticated])
class RobosViewset(viewsets.ModelViewSet):
    queryset = Robos.objects.all()    
    serializer_class = RobosSerializer

    def destroy(self, request, pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        
        try:
            robo_parametros = RobosParametros.objects.filter(robo=pk)
            if robo_parametros:
                parametro = None
                for param in robo_parametros:
                    print(param.pk)
                    parametro = Parametros.objects.get(pk=param.parametro.pk)
                    if parametro:
                        param.delete()
                        parametro.delete()

            robo.delete()
            return Response(f"Robo excluído com sucesso", status=status.HTTP_200_OK)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='executar')
    def executar_robo(self, request, pk=None):
        try:
            robo = Robos.objects.get(id=pk)
            if not robo:
                return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
            
            parametros = {}
            for key, value in request.data.items():
                parametros[key] = value

            robo_parametros = RobosParametros.objects.filter(robo=pk).all()

            if not robo_parametros:
                return Response("O robo não possui parâmetros definidos", status=status.HTTP_404_NOT_FOUND)
            
            parametros_testados = []
            for key, value in parametros.items():
                for param in robo_parametros:
                    parametro = Parametros.objects.get(pk=param.parametro.pk)
                    if not parametro:
                        return Response("Os parâmetros do robo não foram encontrados", status=status.HTTP_404_NOT_FOUND)
                    parametros_testados.append(parametro.nome)
                    if parametro.nome == key:
                        param.valor = value
                        param.save()
                        print(f"Parametro {key} atualizado")
                if not parametros_testados:
                    return Response("Os parâmetros do robo não foram encontrados", status=status.HTTP_404_NOT_FOUND)
            if param in parametros_testados != request.data.keys():
                print(f"Os parâmetros do robo são diferentes do enviado. Esperado: {', '.join(parametros_testados)}, Enviado: {key}")

            nome_robo = robo.nome.lower().replace(" ", "_")
            script_path = f"C:/Users/ACP/projetos/robo_{nome_robo}"
            robo_processo = subprocess.Popen(['powershell', '-Command', f"& cd '{script_path}'; ./.venv/Scripts/Activate.ps1; python robo_{nome_robo}.py"], shell=True, creationflags=subprocess.DETACHED_PROCESS, start_new_session=True)
            print("Robo em execução")
            sleep(2)
            parametros_json = json.dumps(parametros)
            resultado_request = requests.post(f"http://127.0.0.1:5000/", data=parametros_json, headers={'Content-Type': 'application/json'})
 
            if resultado_request.status_code == 200:
                print(f"Req concluída")
                robo.execucoes = robo.execucoes + 1 if robo.execucoes else 1
                robo.ultima_execucao = datetime.now()
                robo.save()
                print(f"{resultado_request.text}")
                requests.post(f"http://127.0.0.1:5000/shutdown")
                return Response("Robo executado com sucesso", status=status.HTTP_200_OK)
            else:
                print(f"{resultado_request.text}")
                requests.post(f"http://127.0.0.1:5000/shutdown")
                return Response("Erro ao executar o robo", status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True, methods=['post'], url_path='parametros/criar')
    def criar_parametro(self, request, pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            if Parametros.objects.filter(nome=request.data['nome']).exists():
                return Response("Este parâmetro já foi criado", status=status.HTTP_400_BAD_REQUEST)
            
            parametro_serializer = ParametrosSerializer(data=request.data)

            if parametro_serializer.is_valid():                
                parametro_serializer.save()

                robo_parametro_serializer = RobosParametrosSerializer(data={'robo': robo.id, 'parametro': parametro_serializer.data['id']})
                if robo_parametro_serializer.is_valid():
                    robo_parametro_serializer.save()
                    return Response(f"Parâmetro criado com sucesso", status=status.HTTP_201_CREATED)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True, methods=['get'], url_path='parametros/listar')
    def listar_parametros(self, request, pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            robo_parametros = RobosParametros.objects.filter(robo=pk)

            if not robo_parametros:
                return Response("O robo não possui parâmetros definidos", status=status.HTTP_204_NO_CONTENT)
            serializer = RobosParametrosSerializer(robo_parametros, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['put'], url_path='parametros/atualizar')
    def atualizar_parametros(self, request, pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)

        try:
            robo_parametros = RobosParametros.objects.filter(robo=pk)

            if not robo_parametros:
                return Response("O robo não possui parâmetros definidos", status=status.HTTP_204_NO_CONTENT)
                
            parametros_testados = []
            for key, value in request.data.items():
                for param in robo_parametros:
                    parametro = Parametros.objects.get(pk=param.parametro.pk)
                    if not parametro:
                        return Response("Os parâmetros do robo não foram encontrados", status=status.HTTP_404_NOT_FOUND)
                    parametros_testados.append(parametro.nome)
                    if parametro.nome == key:
                        param.valor = value
                        param.save()
                        return Response("Parâmetros atualizados com sucesso", status=status.HTTP_204_NO_CONTENT)
                if not parametros_testados:
                    return Response("Os parâmetros do robo não foram encontrados", status=status.HTTP_404_NOT_FOUND)
            return Response(f"Os parâmetros do robo são diferentes do enviado. Esperado: {', '.join(parametros_testados)}, Enviado: {key}", status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['put'], url_path='parametros/atualizar/(?P<param_pk>[^/.]+)')
    def atualizar_parametro(self, request, pk=None, param_pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            robo_parametros = RobosParametros.objects.filter(robo=pk)
            if not robo_parametros:
                return Response("O parâmetro do robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
            parametro = None
            for param in robo_parametros:
                if param.parametro.pk == int(param_pk):
                    parametro = Parametros.objects.get(pk=param.parametro.pk)
                    break

            if not parametro:
                return Response("O parâmetro do robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)

            parametro_serializer = ParametrosSerializer(parametro, data=request.data)

            if parametro_serializer.is_valid():
                parametro_serializer.save()
                return Response("Parâmetro atualizado com sucesso", status=status.HTTP_204_NO_CONTENT)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['delete'], url_path='parametros/excluir/(?P<param_pk>[^/.]+)')
    def excluir_parametro(self, request, pk=None, param_pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            robo_parametros = RobosParametros.objects.filter(robo=pk)
            if not robo_parametros:
                return Response("O parâmetro do robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
            
            parametro = None
            for param in robo_parametros:
                print(param.pk == int(param_pk))
                if param.pk == int(param_pk):
                    parametro = Parametros.objects.get(pk=param.parametro.pk)
                    print(parametro.nome)
                    break

            if not parametro:
                return Response("O parâmetro do robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)

            parametro.delete()
            param.delete()
            return Response("Parâmetro excluído com sucesso", status=status.HTTP_204_NO_CONTENT)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='rotinas')
    def rotinas(self, request, pk=None):
        rotinas = Rotinas.objects.filter(robo=pk)
        serializer = RotinasSerializer(rotinas, many=True)
        if serializer:
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], url_path='rotinas/criar')
    def criar_rotina(self, request, pk=None):
        request_data = request.data
        request_data['robo'] = pk
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            if Rotinas.objects.filter(robo=pk, nome=request_data['nome']).exists():
                return Response("Esta rotina já foi criada", status=status.HTTP_400_BAD_REQUEST)
            
            print(request_data)

            serializer = RotinasSerializer(data=request_data)

            if serializer.is_valid():
                serializer.save(robo=robo)
                return Response(f"Rotina criada com sucesso", status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='rotinas/listar')
    def listar_rotinas(self, request, pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            robo_rotinas = Rotinas.objects.filter(robo=pk)

            if not robo_rotinas:
                return Response("O robo não possui rotinas definidas", status=status.HTTP_204_NO_CONTENT)
            
            serializer = RotinasSerializer(robo_rotinas, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['put'], url_path='rotinas/atualizar/(?P<rotina_pk>[^/.]+)')
    def editar_rotina(self, request, pk=None, rotina_pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            robo_rotinas = Rotinas.objects.filter(robo=pk)
            if not robo_rotinas:
                return Response("O robo não possui rotinas definidas", status=status.HTTP_404_NOT_FOUND)
            
            robo_rotina = None
            for rotina in robo_rotinas:
                if rotina.pk == int(rotina_pk):
                    robo_rotina = rotina
                    break

            if not robo_rotina:
                return Response("A rotina do robo não foi encontrada", status=status.HTTP_404_NOT_FOUND)

            request.data['robo'] = pk
            robo_rotina_serializer = RotinasSerializer(robo_rotina, data=request.data)
            if robo_rotina_serializer.is_valid():
                robo_rotina_serializer.save()
                return Response("Rotina atualizada com sucesso", status=status.HTTP_204_NO_CONTENT)

            return Response(robo_rotina_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['delete'], url_path='rotinas/excluir/(?P<rotina_pk>[^/.]+)')
    def excluir_rotina(self, request, pk=None, rotina_pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            robo_rotinas = Rotinas.objects.filter(robo=pk)
            if not robo_rotinas:
                return Response("O robo não possui rotinas definidas", status=status.HTTP_404_NOT_FOUND)
            
            robo_rotina = None
            for rotina in robo_rotinas:
                if rotina.pk == int(rotina_pk):
                    robo_rotina = rotina
                    break

            if not robo_rotina:
                return Response("A rotina do robo não foi encontrada", status=status.HTTP_404_NOT_FOUND)

            robo_rotina.delete()
            return Response("Rotina excluída com sucesso", status=status.HTTP_204_NO_CONTENT)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        