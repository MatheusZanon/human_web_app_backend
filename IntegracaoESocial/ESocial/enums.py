from enum import Enum, auto
from typing import Dict

class ESocialAmbiente(Enum):
    PRODUCAO = 1
    DESENVOLVIMENTO = 2

class ESocialWsdl(Enum):
    CONSULTAR_LOTE_EVENTOS = 'servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc?wsdl'
    ENVIAR_LOTE_EVENTOS = 'servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc?wsdl'

class ESocialTipoEvento(Enum):
    """
    Enum para os tipos de eventos do e-social suportados na Integração.

    Cada tupla contém o nome do elemento raiz do evento, o nome do XSD e o nome do xsd do retorno do evento (opcional) respectivamente.
    Exemplo: ("evtInfoEmpregador", "evtInfoEmpregador", "")
    """
    EVT_INFO_EMPREGADOR = ("evtInfoEmpregador", "evtInfoEmpregador", "")
    EVT_ADMISSAO_PRELIMINAR = ("evtAdmPrelim", "evtAdmissaoPreliminar", "")
    EVT_REMUNERACAO_TRABALHADOR_RGPS = ("evtRemun", "evtRemun", "")
    EVT_ENVIO_LOTE_EVENTOS = ("envioLoteEventos", "EnvioLoteEventos-v1_1_1", "RetornoEnvioLoteEventos-v1_1_0")
    EVT_CONSULTAR_LOTE_EVENTOS = ("consultaLoteEventos", "consultaLoteEventos-v1_0_0", "retornoProcessamentoLote-v1_3_0")

class ESocialOperacao(Enum):
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
