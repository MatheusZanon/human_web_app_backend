from .enums import Operation, Environment
from typing import Dict

# URLs dos serviços web, organizadas por ambiente e operação
WS_URL: Dict[Environment, Dict[Operation, str]] = {
    Environment.TESTS: {
        Operation.SEND_LOTE: 'https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc?wsdl',
        Operation.RETRIEVE_LOTE_RESULT: 'https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc?wsdl',
    },
    Environment.PRODUCTION: {
        Operation.SEND_LOTE: 'https://webservices.envio.esocial.gov.br/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc?wsdl',
        Operation.RETRIEVE_LOTE_RESULT: 'https://webservices.consulta.esocial.gov.br/servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc?wsdl',
    },
}

