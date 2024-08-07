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