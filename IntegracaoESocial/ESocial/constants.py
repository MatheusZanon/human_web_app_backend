from .enums import ESocialOperacao, ESocialAmbiente
from typing import Dict
import os

INTEGRATION_ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
"""
    Caminho da raiz da integração. Usado para encontrar certificados, XSDs e WSDLs.
"""

LOGGING_PATH = os.path.join(INTEGRATION_ROOT_PATH, 'logs')

EVENT_ID_PREFIX = 'ID'
"""
    Prefixo dos IDs dos eventos. Usado para identificar eventos na integração.
"""

# URLs dos serviços web, organizadas por ambiente e operação
WS_URL: Dict[ESocialAmbiente, Dict[ESocialOperacao, str]] = {
    ESocialAmbiente.DESENVOLVIMENTO: {
        ESocialOperacao.SEND_LOTE: 'https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc?wsdl',
        ESocialOperacao.RETRIEVE_LOTE_RESULT: 'https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc?wsdl',
    },
    ESocialAmbiente.PRODUCAO: {
        ESocialOperacao.SEND_LOTE: 'https://webservices.envio.esocial.gov.br/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc?wsdl',
        ESocialOperacao.RETRIEVE_LOTE_RESULT: 'https://webservices.consulta.esocial.gov.br/servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc?wsdl',
    },
}
"""
    URLs dos serviços web, organizadas por ambiente e operação

    Exemplo:

    WS_URL[Environment.TESTS][Operation.SEND_LOTE]

    'https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc?wsdl'
"""

MAX_BATCH_SIZE = 50
"""
    Tamanho maximo de eventos por lote enviados ao E-Social
"""
