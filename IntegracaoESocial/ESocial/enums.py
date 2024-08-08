from enum import Enum, auto

class ESocialAmbiente(Enum):
    PRODUCAO = 1
    DESENVOLVIMENTO = 2

class ESocialWsdl(Enum):
    CONSULTAR_LOTE_EVENTOS = 'servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc?wsdl'
    ENVIAR_LOTE_EVENTOS = 'servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc?wsdl'

class ESocialTipoEvento(Enum):
    """
    Enum para os tipos de eventos do e-social suportados na Integração.
    """
    EVT_INFO_EMPREGADOR = ("evtInfoEmpregador", "evtInfoEmpregador")
    EVT_ADMISSAO_PRELIMINAR = ("evtAdmissaoPreliminar", "evtAdmPrelim")
    EVT_ENVIO_LOTE_EVENTOS = ("EnvioLoteEventos-v1_1_1", "envioLoteEventos")

from enum import Enum
from typing import Dict

class Environment(Enum):
    PRODUCTION = 1
    TESTS = 2

class Operation(Enum):
    # Envio de Lote de Eventos
    SEND_LOTE = 'send_lote'
    
    # Consulta ao Resultado do Processamento de um Lote de Eventos
    RETRIEVE_LOTE_RESULT = 'retrieve_lote_result'
    
    # Consulta aos Identificadores dos Eventos
    CONSULTAR_ID_EVENTOS_EMPREGADOR = 'consultar_identificadores_eventos_empregador'
    CONSULTAR_ID_EVENTOS_TABELA = 'consultar_identificadores_eventos_tabela'
    CONSULTAR_ID_EVENTOS_TRABALHADOR = 'consultar_identificadores_eventos_trabalhador'
    
    # Solicitação de Download dos Eventos
    SOLICITAR_DOWNLOAD_EVENTOS_POR_ID = 'solicitar_download_eventos_por_id'
    SOLICITAR_DOWNLOAD_EVENTOS_POR_RECIBO = 'solicitar_download_eventos_por_recibo'

# URLs dos serviços web, organizadas por ambiente e operação
_WS_URL: Dict[Environment, Dict[Operation, str]] = {
    Environment.TESTS: {
        Operation.SEND_LOTE: 'https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc?wsdl',
        Operation.RETRIEVE_LOTE_RESULT: 'https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc?wsdl',
    },
    Environment.PRODUCTION: {
        Operation.SEND_LOTE: 'https://webservices.envio.esocial.gov.br/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc?wsdl',
        Operation.RETRIEVE_LOTE_RESULT: 'https://webservices.consulta.esocial.gov.br/servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc?wsdl',
    },
}

def get_wsdl_url(env: Environment, operation: Operation) -> str:
    return _WS_URL[env][operation]
