from django.shortcuts import render
from rest_framework.views import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from IntegracaoESocial.ESocial.esocial import IntegracaoESocial
from IntegracaoESocial.ESocial.enums import ESocialAmbiente, ESocialTipoEvento, ESocialOperacao
from IntegracaoESocial.ESocial.xml.validator import XMLValidator
from IntegracaoESocial.ESocial.xml.helper import XSDHelper, XMLHelper
from IntegracaoESocial.ESocial.services import EventLogService
from IntegracaoESocial.ESocial.constants import LOGGING_PATH
# Create your views here.

# @permission_classes([IsAuthenticated])
class EmpregadorViewSet(viewsets.ViewSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Inicialize o serviço de log
        event_logging_service = EventLogService(log_dir=LOGGING_PATH)

        # Inicialize a integração com o eSocial
        # Nota: Você pode querer mover essa inicialização para um lugar mais apropriado,
        # como um middleware ou uma configuração global
        self.esocial = IntegracaoESocial(
            cert_filename="HUMAN_SOLUCOES_E_DESENVOLVIMENTOS_EM_RECURSOS_HUM_SENHA 123456.pfx",
            cert_password='123456',
            transmissorTpInsc='1',
            transmissorCpfCnpj='27480830000110',
            ambiente=ESocialAmbiente.DESENVOLVIMENTO,  # ou o ambiente desejado
            event_logging_service=event_logging_service
        )

    @action(detail=False, methods=['post'])
    def consultar_empregador(self, request):
        try:
            wsdl = self.esocial.get_wsdl_url(ESocialOperacao.SEND_LOTE)

            xml = self.esocial.create_s1000_envelope(request.data, request.data['ideEmpregador']['nrInsc'], 0)
            # print(xml.to_string('utf-8', pretty_print=True))
            xml = self.esocial.sign(xml)
            xsd = XSDHelper().xsd_from_file(ESocialTipoEvento.EVT_INFO_EMPREGADOR)
            XMLValidator(xml, xsd).validate()
            self.esocial.add_event_to_lote(xml)
            
            response = self.esocial.send(wsdl)

            if response['status'] == 'failure':
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'erro': 'Erro ao processar a consulta',
                'detalhes': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def consultar_lote(self, request):
        try:
            wsdl = self.esocial.get_wsdl_url(ESocialOperacao.RETRIEVE_LOTE_RESULT)
            protocolo = request.query_params.get('protocoloEnvio')

            resposta = self.esocial.retrieve(wsdl, protocolo)

            return Response(resposta, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'erro': 'Erro ao consultar lote',
                'detalhes': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)