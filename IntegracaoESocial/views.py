from django.shortcuts import render
from rest_framework.views import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from IntegracaoESocial.ESocial.esocial import IntegracaoESocial
from IntegracaoESocial.ESocial.enums import ESocialAmbiente, ESocialTipoEvento, ESocialWsdl
import os
from lxml import etree
# Create your views here.

# @permission_classes([IsAuthenticated])
class EmpregadorViewSet(viewsets.ViewSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicialize a integração com o eSocial
        # Nota: Você pode querer mover essa inicialização para um lugar mais apropriado,
        # como um middleware ou uma configuração global
        self.esocial = IntegracaoESocial(
            cert_path="C:\\Users\\ACP\\projetos\\human_web_app\\human_web_app_backend\\IntegracaoESocial\\HUMAN_SOLUCOES_E_DESENVOLVIMENTOS_EM_RECURSOS_HUM_SENHA 123456.pfx",
            cert_password='123456',
            ambiente=ESocialAmbiente.DESENVOLVIMENTO  # ou o ambiente desejado
        )

    @action(detail=False, methods=['post'])
    def consultar_empregador(self, request):
        try:
            # Extrair ideEmpregador
            ide_empregador = request.data.pop('ideTransmissor')
            transmissor_tpInsc = ide_empregador['tpInsc']
            transmissor_nrInsc = ide_empregador['nrInsc']

            xml = self.esocial.create_event(request.data, ESocialTipoEvento.EVT_ADMISSAO_PRELIMINAR, 12345678912345, 12345678912345, 0)
            response = self.esocial.enviar_lote(xml, transmissor_tpInsc, transmissor_nrInsc)

            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'erro': 'Erro ao processar a consulta',
                'detalhes': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def consultar_lote(self, request):
        try:
            protocolo = request.query_params.get('protocolo')
            id_lote = request.query_params.get('id_lote')

            resposta = self.esocial.consultar_lote(id_lote)

            # Processar a resposta
            resposta_json = self.esocial.xml_to_dict(resposta)
            print(resposta_json)
            # Nota: Adapte isso com base na estrutura real da resposta do eSocial
            return Response(resposta_json, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'erro': 'Erro ao consultar lote',
                'detalhes': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)