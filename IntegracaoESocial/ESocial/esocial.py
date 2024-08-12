from zeep import Client
from zeep.transports import Transport
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from contextlib import contextmanager
import tempfile
import os
import json
from typing import Dict, Any, Union, List, Optional
from lxml import etree
from datetime import datetime, UTC
from .errors import ESocialError, ESocialValidationError, ESocialConnectionError
from .enums import ESocialWsdl, ESocialTipoEvento, ESocialAmbiente, ESocialOperacao
from .constants import WS_URL, MAX_BATCH_SIZE, INTEGRATION_ROOT_PATH, EVENT_ID_PREFIX, LOGGING_PATH
from .services import EventLogService
from .xml.helper import XMLHelper, XSDHelper
from .xml.signer import XMLSigner
from .xml.validator import XMLValidator
import logging

class IntegracaoESocial:
    def __init__(self, cert_filename, cert_password, transmissorTpInsc, transmissorCpfCnpj, ambiente: ESocialAmbiente = ESocialAmbiente.PRODUCAO, event_logging_service: Optional[EventLogService] = None) -> None:
        previous_folder = os.path.normpath(INTEGRATION_ROOT_PATH + os.sep + os.pardir)
        cert_folder = os.path.join(previous_folder, 'certs')
        cert_path = os.path.join(cert_folder, cert_filename)
        self.cert_path = cert_path
        self.cert_password = cert_password
        self.transmissorTpInsc = transmissorTpInsc
        self.transmissorCpfCnpj = transmissorCpfCnpj
        self.ambiente = ambiente
        self.cert = self._load_cert()
        self.batch_to_send: List[etree._Element] = []
        self.event_logging_service = event_logging_service
    
    def _load_cert(self):
        with open(self.cert_path, 'rb') as cert_file:
            pfx_data = cert_file.read()
        private_key, certificate, _ = pkcs12.load_key_and_certificates(
            pfx_data, self.cert_password.encode(), None
        )
        return (certificate, private_key)
    
    def get_wsdl_url(self, operation: ESocialOperacao) -> str:
        return WS_URL[self.ambiente][operation]

    @contextmanager
    def _create_client(self, wsdl_url: str):
        session = requests.Session()
    
        # Desempacotar o certificado e a chave privada
        certificate, private_key = self.cert

        # Converter o certificado para PEM
        cert_pem = certificate.public_bytes(encoding=serialization.Encoding.PEM)

        # Converter a chave privada para PEM
        key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Criar arquivos temporários para o certificado e a chave
        cert_file = tempfile.NamedTemporaryFile(delete=False)
        key_file = tempfile.NamedTemporaryFile(delete=False)

        try:
            # Escrever o certificado e a chave nos arquivos temporários
            cert_file.write(cert_pem)
            key_file.write(key_pem)
            cert_file.close()
            key_file.close()

            # Configurar a sessão com os arquivos temporários
            session.cert = (cert_file.name, key_file.name)
            session.verify = False # False para teste local

            # Criar o cliente SOAP
            transport = Transport(session=session)
            client = Client(wsdl_url, transport=transport)
            if self.event_logging_service:
                self.event_logging_service.log(f"SOAP Client created: {wsdl_url}")
            yield client
        except Exception as e:
            if self.event_logging_service:
                self.event_logging_service.log(f"Error creating SOAP client: {e}", logging.ERROR)
            raise ESocialConnectionError(f"Error creating SOAP client: {e}")
        finally:
            # Limpar os arquivos temporários
            os.unlink(cert_file.name)
            os.unlink(key_file.name)
    
    def generate_event_id(self, cnpj_cpf: Union[str, int], ) -> str:
        """
        Gera um ID de evento baseado no CNPJ/CPF do emissor e timestamp atual.

        Args:
            cnpj_cpf (str | int): O CNPJ ou CPF a ser utilizado como base para o ID.

        Returns:
            str: Um identificador único para o evento, com no máximo 34 caracteres.
        """
        
        # Garantir que cnpj_cpf é uma string
        if isinstance(cnpj_cpf, int):
            cnpj_cpf = str(cnpj_cpf)
        
        # Sanitizar o CNPJ/CPF removendo caracteres não numéricos se necessário
        sanitized_cnpj_cpf = ''.join(filter(str.isdigit, cnpj_cpf))
        
        # Verificar o comprimento do CNPJ/CPF
        if len(sanitized_cnpj_cpf) > 14:
            raise ESocialValidationError("CNPJ/CPF inválido")
        
        if len(sanitized_cnpj_cpf) < 11:
            raise ESocialValidationError("CNPJ/CPF inválido")
        
        # Obter a data e hora atual no formato UTC
        current_time = datetime.now(UTC).strftime("%Y%m%d%H%M%S")

        # Gerar o número do ID com base no CNPJ/CPF e timestamp
        id_number = f"{sanitized_cnpj_cpf}{current_time}{len(self.batch_to_send) + 1}"
        
        # Completar com zeros caso o id_number não tenha 34 caracteres
        id_number = id_number.ljust(34, '0')
        
        # Criar o ID completo e garantir que tenha no máximo 34 caracteres
        full_id = f"{EVENT_ID_PREFIX}{id_number[:34]}"
        return full_id
    
    def sign(self, xml: etree._Element) -> etree._Element:
        signer = XMLSigner(self.cert)

        return signer.sign(xml)
    
    def create_s1000_envelope(self, event_data: Dict[str, Any], issuer_cnpj_cpf: str = None, user_id: int = None) -> etree._Element:
        nsmap = XSDHelper().get_namespace_from_xsd(ESocialTipoEvento.EVT_INFO_EMPREGADOR)

        s1000_xml = XMLHelper("eSocial", nsmap)

        evt_id = self.generate_event_id(issuer_cnpj_cpf)

        s1000_xml.add_element(None, "evtInfoEmpregador", Id=evt_id)

        s1000_xml.add_element("evtInfoEmpregador", "ideEvento")
        s1000_xml.add_element("evtInfoEmpregador/ideEvento", "tpAmb", text=str(self.ambiente.value))
        s1000_xml.add_element("evtInfoEmpregador/ideEvento", "procEmi", text="1")
        s1000_xml.add_element("evtInfoEmpregador/ideEvento", "verProc", text="1.0")

        s1000_xml.add_element("evtInfoEmpregador", "ideEmpregador")
        if len(str(issuer_cnpj_cpf)) == 14: # Se for cnpj o tipo de inscrição deve ser 1
            s1000_xml.add_element("evtInfoEmpregador/ideEmpregador", "tpInsc", text="1")
        elif len(str(issuer_cnpj_cpf)) == 11: # Se for cpf o tipo de inscrição deve ser 2
            s1000_xml.add_element("evtInfoEmpregador/ideEmpregador", "tpInsc", text="2")
        else:
            raise ESocialValidationError(f"O CNPJ ou CPF do emissor deve ter 14 ou 11 caracteres respectivamente.")
        
        s1000_xml.add_element("evtInfoEmpregador/ideEmpregador", "nrInsc", text=str(issuer_cnpj_cpf))

        s1000_xml.add_element("evtInfoEmpregador", "infoEmpregador")

        # Verifica e adiciona a tag correta dentro de infoEmpregador
        operations = {'inclusao', 'alteracao', 'exclusao'}
        present_operations = [op for op in operations if op in event_data['infoEmpregador']]

        if len(present_operations) != 1:
            print(present_operations)
            raise ESocialValidationError("Deve ser especificado exatamente um tipo de operação: 'inclusao', 'alteracao' ou 'exclusao'.")
        
        if present_operations[0] == 'inclusao':
            s1000_xml.add_element("evtInfoEmpregador/infoEmpregador", "inclusao")

            s1000_xml.add_element("evtInfoEmpregador/infoEmpregador/inclusao", "idePeriodo")
            s1000_xml.add_element("evtInfoEmpregador/infoEmpregador/inclusao/idePeriodo", "iniValid", text=event_data['infoEmpregador']['inclusao']['idePeriodo']['iniValid'])
            s1000_xml.add_element("evtInfoEmpregador/infoEmpregador/inclusao/idePeriodo", "fimValid", text=event_data['infoEmpregador']['inclusao']['idePeriodo']['fimValid'])
        elif present_operations[0] == 'alteracao':
            s1000_xml.add_element("evtInfoEmpregador/infoEmpregador", "alteracao")
        elif present_operations[0] == 'exclusao':
            s1000_xml.add_element("evtInfoEmpregador/infoEmpregador", "exclusao")
        else:
            raise ESocialValidationError("O tipo de operação S-1000 deve conter exatamente um tipo de operação: 'inclusao', 'alteracao' ou 'exclusao'.")
        
        if self.event_logging_service:
            self.event_logging_service.log(f"S-1000 Envelope created: ID: {evt_id}, XML: {s1000_xml.to_string()}")
        return s1000_xml.root
    
    def add_event_to_lote(self, event: etree._Element):
        if len(self.batch_to_send) < 50:
            evento_id = None
            for child in event.iterchildren():
                evento_id = child.get('Id')
                if evento_id:
                    break
            self.batch_to_send.append(event)
            if self.event_logging_service:
                self.event_logging_service.log(f"Event added to batch: {evento_id}")
        else:
            if self.event_logging_service:
                self.event_logging_service.log(f"Batch limit reached: {MAX_BATCH_SIZE} events allowed", logging.ERROR)
            raise ESocialValidationError(f"O lote de eventos não pode ter mais de {MAX_BATCH_SIZE} eventos")

    def _create_send_envelope(self, group_id: str):
        try:
            # Extrair informações do empregador do primeiro evento válido
            ide_empregador = None
            for evento in self.batch_to_send:
                for child in evento.iterchildren():
                    if child.tag == "ideEmpregador":
                        ide_empregador = child

                ns = {"ns": "*"}
                ide_empregador = evento.find(".//ns:ideEmpregador", namespaces=ns)
                if ide_empregador is not None:
                    break

            if ide_empregador is None:
                raise ESocialValidationError("Elemento ideEmpregador não encontrado em nenhum evento")

            tpInsc = ide_empregador.find("ns:tpInsc", namespaces=ns)
            nrInsc = ide_empregador.find("ns:nrInsc", namespaces=ns)

            if tpInsc is None or nrInsc is None:
                raise ESocialValidationError("Elementos tpInsc ou nrInsc não encontrados no elemento ideEmpregador")

            # Criar o elemento raiz do lote com prefixo de namespace
            nsmap = XSDHelper().get_namespace_from_xsd(ESocialTipoEvento.EVT_ENVIO_LOTE_EVENTOS)
            lote_eventos_xml = XMLHelper("eSocial", nsmap)
            lote_eventos_xml.add_element(None, "envioLoteEventos", grupo=group_id)

            lote_eventos_xml.add_element("envioLoteEventos", "ideEmpregador")
            lote_eventos_xml.add_element("envioLoteEventos/ideEmpregador", "tpInsc", text=tpInsc.text)
            lote_eventos_xml.add_element("envioLoteEventos/ideEmpregador", "nrInsc", text=nrInsc.text)

            lote_eventos_xml.add_element("envioLoteEventos", "ideTransmissor")
            lote_eventos_xml.add_element("envioLoteEventos/ideTransmissor", "tpInsc", text=self.transmissorTpInsc)
            lote_eventos_xml.add_element("envioLoteEventos/ideTransmissor", "nrInsc", text=self.transmissorCpfCnpj)

            lote_eventos_xml.add_element("envioLoteEventos", "eventos")
            
            for evento in self.batch_to_send:
                evento_id = None
                for child in evento.iterchildren():
                    evento_id = child.get('Id')
                    if evento_id:
                        break

                if not evento_id:
                    raise ESocialValidationError("Atributo 'Id' não encontrado em nenhum elemento do evento")
                
                event_root = lote_eventos_xml.add_element("envioLoteEventos/eventos", "evento", Id=evento_id)
                event_root.append(evento)
            
            return lote_eventos_xml.root
        except Exception as e:
            logging.error(f"Erro ao processar o lote: {str(e)}")
        
    def send(self, wsdl: str, group_id: str = 1, clear_batch: bool = True) -> Dict[str, Any]:
        try:
            with self._create_client(wsdl) as client:
                lote_eventos = self._create_send_envelope(group_id)

                # batch xml
                # print(etree.tostring(lote_eventos, pretty_print=True).decode('utf-8'))

                xsd_batch = XSDHelper().xsd_from_file(ESocialTipoEvento.EVT_ENVIO_LOTE_EVENTOS)
                XMLValidator(lote_eventos, xsd_batch).validate()
                if self.event_logging_service:
                    self.event_logging_service.log(f"Batch validated: Group ID: {group_id}")

                # client.wsdl.dump()

                BatchElement = client.get_element('ns1:EnviarLoteEventos')

                # Enviar o lote
                response = client.service.EnviarLoteEventos(BatchElement(loteEventos=lote_eventos))
                if self.event_logging_service:
                    self.event_logging_service.log(f"Batch sent: Group ID: {group_id}")
                
                # response xml
                # print(XMLHelper(response).to_string())

                xsd_response = XSDHelper().xsd_from_file(ESocialTipoEvento.EVT_ENVIO_LOTE_EVENTOS, 'retorno')
                XMLValidator(response, xsd_response).validate()
                if self.event_logging_service:
                    self.event_logging_service.log(f"Batch response validated: Group ID: {group_id}, XML: {XMLHelper(response).to_string()}")

                response_json = self.decode_response(response)

                if self.event_logging_service:
                    self.event_logging_service.log(f"Batch response decoded: Group ID: {group_id}, JSON: {json.dumps(response_json, indent=4, ensure_ascii=False)}")

                if clear_batch:
                    self.batch_to_send.clear()
                    if self.event_logging_service:
                        self.event_logging_service.log(f"Batch cleared: Group ID: {group_id}")

                return response_json
        except ESocialError as ee:
            if self.event_logging_service:
                self.event_logging_service.log(f"Batch failed: Group ID: {group_id}, Error: {str(ee)}", logging.ERROR)
            raise ee
        except Exception as e:
            if self.event_logging_service:
                self.event_logging_service.log(f"Batch failed: Group ID: {group_id}, Error: {str(e)}", logging.ERROR)
            raise e
    

    def decode_response(self, response: etree._Element) -> Dict[str, Any]:
        """Converte uma resposta XML do webservice eSocial para um dicionário JSON, removendo namespaces e indicando sucesso ou falha."""
        def get_status(el: etree._Element, tagname: str) -> Dict[str, Any]:
            """Extrai o status da resposta XML, ignorando namespaces."""
            # Removendo namespace da tag que estamos procurando
            status_element = el.find(f".//{{*}}{tagname}")
            cd_resposta = None
            desc_resposta = None

            if status_element is not None:
                # Busca os elementos cdResposta e descResposta sem utilizar //, pois já estamos no contexto de status_element
                cd_resposta_element = status_element.find("{*}cdResposta")
                if cd_resposta_element is not None:
                    cd_resposta = cd_resposta_element.text
                
                desc_resposta_element = status_element.find("{*}descResposta")
                if desc_resposta_element is not None:
                    desc_resposta = desc_resposta_element.text

            return {"code": cd_resposta, "message": desc_resposta}

        # Converte o XML para dicionário sem namespaces
        response_dict = XMLHelper(response).to_dict()
        
        # Extrai status da resposta
        status = get_status(response, 'status')
        
        # Verifica se a resposta indica sucesso ou falha
        if status['code'] is None or int(status['code']) != 201:
            return {
                "status": "failure",
                "code": status['code'],
                "message": status['message'],
                "details": response_dict
            }
        else:
            return {
                "status": "success",
                "code": status['code'],
                "message": status['message'],
                "data": response_dict
            }

    def consultar_lote(self, lote: str):
        try:
            with self._create_client(ESocialWsdl.CONSULTAR_LOTE_EVENTOS) as client:
                # Consultar o lote
                response = client.service.ConsultarLoteEventos(lote)
                return response
        except Exception as e:
            logging.error(f"Erro ao processar o lote: {str(e)}")
            return {"erro": "Erro ao processar o lote", "detalhes": str(e)}