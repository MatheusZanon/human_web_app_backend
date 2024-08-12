from zeep import Client
from zeep.transports import Transport
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from contextlib import contextmanager
import tempfile
import os
from typing import Dict, Any, Union, List
import signxml
from signxml import XMLSigner
from lxml import etree
from datetime import datetime, UTC
from .errors import ESocialError, ESocialValidationError
from .enums import ESocialWsdl, ESocialTipoEvento, ESocialAmbiente, ESocialOperacao
from .constants import WS_URL, MAX_BATCH_SIZE, INTEGRATION_ROOT_PATH, EVENT_ID_PREFIX
from .services import EventLogService
from .xml import XMLHelper, XMLValidator, XSDHelper
import logging

# Override signxml.XMLSigner.check_deprecated_methods() para ignorar os erros e poder utilizar o SHA1, remover quando o e-social aceitar assinaturas mais seguras
class XMLSignerWithSHA1(XMLSigner):
    def check_deprecated_methods(self):
        pass

class IntegracaoESocial:
    def __init__(self, cert_filename, cert_password, transmissorTpInsc, transmissorCpfCnpj, ambiente: ESocialAmbiente = ESocialAmbiente.PRODUCAO):
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
        self.event_logging_service = EventLogService()
    
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
            
            yield client
        finally:
            # Limpar os arquivos temporários
            os.unlink(cert_file.name)
            os.unlink(key_file.name)
    
    def xml_to_dict(element: etree._Element) -> Dict[str, Any]:
        """Converte um elemento XML em um dicionário Python."""
        
        def parse_element(elem: etree._Element) -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
            """Função auxiliar para processar cada elemento XML recursivamente."""
            # Se o elemento não tem filhos, retorna o texto do elemento
            if len(elem) == 0:
                return elem.text.strip() if elem.text else ''
            
            # Dicionário para armazenar os dados do elemento atual
            result = {}
            
            # Processa os atributos do elemento
            if elem.attrib:
                result.update({f'@{k}': v for k, v in elem.attrib.items()})
            
            # Processa os filhos do elemento
            for child in elem:
                child_data = parse_element(child)
                # Se já existe um item com o mesmo nome, transforma em lista
                if child.tag in result:
                    if not isinstance(result[child.tag], list):
                        result[child.tag] = [result[child.tag]]
                    result[child.tag].append(child_data)
                else:
                    result[child.tag] = child_data
            
            return result

        # Converte o elemento raiz para dicionário e retorna
        return {element.tag: parse_element(element)}
    
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
        print(full_id)
        return full_id
    
    def _get_wsdl_url(self, service_path: ESocialWsdl):
        if self.ambiente == ESocialAmbiente.PRODUCAO:
            return f"https://webservices.envio.esocial.gov.br/{service_path.value}"
        else:
            return f"https://webservices.producaorestrita.esocial.gov.br/{service_path.value}"

    def get_namespace_from_xsd(self, xsd_path: str) -> str:
        try:
            tree = etree.parse(xsd_path)
            root = tree.getroot()
            return root.get('targetNamespace')
        except Exception as e:
            raise ValueError(f"Erro ao ler o namespace do XSD: {e}")

    def generate_event_xml(self, event: ESocialTipoEvento, event_data: Dict[str, Any], event_id: str, xsd_path: str) -> etree.ElementTree:
        evt_key = event.value[0]
        evt_filename = event.value[1]

        # Obter o namespace do XSD
        ns = self.get_namespace_from_xsd(xsd_path)

        if not ns:
            raise ValueError(f"Não foi possível obter o namespace para o evento: {evt_filename}")
        
        nsmap = {None: ns}

        # Criar o elemento raiz
        root = etree.Element(f"{{{ns}}}eSocial", nsmap=nsmap)

        # Criar o elemento do evento
        evento = etree.SubElement(root, f"{{{ns}}}{evt_key}", Id=event_id)

        # Função recursiva para adicionar elementos
        def add_elements(parent: etree.Element, data: Dict[str, Any]) -> None:
            for key, value in data.items():
                if isinstance(value, dict):
                    sub_element = etree.SubElement(parent, f"{{{ns}}}{key}")
                    add_elements(sub_element, value)
                else:
                    element = etree.SubElement(parent, f"{{{ns}}}{key}")
                    element.text = str(value)

        # Adicionar os dados do evento
        add_elements(evento, event_data)

        # Criar a árvore XML
        tree = etree.ElementTree(root)

        # Retornar a árvore XML assinada
        return tree
    
    def validate_event_xml(self, event_xml: etree.ElementTree, event_xsd_path: str) -> None:
        # Validar o XML contra o esquema XSD
        xmlschema_doc = etree.parse(event_xsd_path)
        xmlschema = etree.XMLSchema(xmlschema_doc)

        if not xmlschema.validate(event_xml):
            log = xmlschema.error_log
            print(log)
            raise ValueError(f"XML inválido: {log.last_error}")

    def sign(self, xml: etree._Element) -> etree._Element:
        # Pegar o id do evento
        evento_id = None
        for child in xml.iterchildren():
            evento_id = child.get('Id')
            if evento_id:
                break

        # Converter o certificado para o formato PEM
        cert_pem = self.cert[0].public_bytes(encoding=serialization.Encoding.PEM)
        
        # Converter a chave privada para o formato PEM
        key_pem = self.cert[1].private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        signer = XMLSignerWithSHA1(
            method=signxml.methods.enveloped,
            signature_algorithm=signxml.algorithms.SignatureMethod.RSA_SHA1,
            digest_algorithm=signxml.algorithms.DigestAlgorithm.SHA1,
            c14n_algorithm=signxml.algorithms.CanonicalizationMethod.CANONICAL_XML_1_0,
        )

        signed = signer.sign(xml, key=key_pem, cert=cert_pem, reference_uri=evento_id)

        return signed

    def create_event(self, event_data: Dict[str, Any], event_type: ESocialTipoEvento, issuer_cnpj_cpf: str = None, signer_cnpj_cpf: str = None, user_id: int = None):
        evt_key = event_type.value[0]
        evt_filename = event_type.value[1]
        
        # Obter o caminho do XSD
        xsd_path = os.path.join(INTEGRATION_ROOT_PATH, 'config', 'xsd', f'{evt_filename}.xsd')

        evt_id = self.generate_event_id(issuer_cnpj_cpf)

        xml_tree = self.generate_event_xml(event=event_type, event_data=event_data, event_id=evt_id, xsd_path=xsd_path)
        signed_xml = self.sign_xml(xml_tree.getroot(), evt_id)

        # Validar o XML assinado
        self.validate_event_xml(signed_xml, xsd_path)
        
        # Converter o XML assinado para string
        xml_string = etree.tostring(signed_xml, pretty_print=True, xml_declaration=True, encoding='UTF-8').decode()
        # self.event_logging_service.log_event(event_id=evt_id, event_type=evt_key, event_data=event_data, event_issuer=issuer_cnpj_cpf, event_signer=signer_cnpj_cpf, user_id=user_id)

        print(xml_string)
        # return None
        return signed_xml
    
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
        
        return s1000_xml.root
    
    def add_event_to_lote(self, event: etree._Element):
        if len(self.batch_to_send) < 50:
            self.batch_to_send.append(event)
        else:
            raise ESocialValidationError(f"O lote de eventos não pode ter mais de {MAX_BATCH_SIZE} eventos")

    def check_event_status(self, protocol):
        # Implemente a consulta de status do evento
        pass

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

                # client.wsdl.dump()

                BatchElement = client.get_element('ns1:EnviarLoteEventos')

                # Enviar o lote
                response = client.service.EnviarLoteEventos(BatchElement(loteEventos=lote_eventos))
                
                # response xml
                # print(etree.tostring(response, pretty_print=True).decode('utf-8'))

                xsd_response = XSDHelper().xsd_from_file(ESocialTipoEvento.EVT_ENVIO_LOTE_EVENTOS, 'retorno')
                XMLValidator(response, xsd_response).validate()

                response_json = self.decode_response(response)

                if clear_batch:
                    self.batch_to_send.clear()

                return response_json
        except ESocialError as ee:
            print(f"Erro E-social: {ee.message}")
        except Exception as e:
            print(f"Erro ao enviar lote: {str(e)}")
    def xml_to_dict(self, element: etree._Element) -> Dict[str, Any]:
        """Converte um elemento XML e seus filhos em um dicionário, removendo namespaces das tags."""
        def recursive_dict(el: etree._Element) -> Dict[str, Any]:
            # Remove o namespace da tag
            tag = el.tag.split('}', 1)[-1] if '}' in el.tag else el.tag
            
            # Se o elemento possui texto e não está vazio
            if el.text and el.text.strip():
                return {tag: el.text.strip()}
            
            # Cria um dicionário para os filhos do elemento
            child_dict = {}
            for child in el:
                child_tag = child.tag.split('}', 1)[-1] if '}' in child.tag else child.tag
                child_value = recursive_dict(child)

                if child_tag in child_dict:
                    # Se a tag já existe no dicionário, converte para lista
                    if not isinstance(child_dict[child_tag], list):
                        child_dict[child_tag] = [child_dict[child_tag]]
                    child_dict[child_tag].append(child_value[child_tag])
                else:
                    child_dict[child_tag] = child_value[child_tag]
            
            return {tag: child_dict}

        return recursive_dict(element)

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
        response_dict = self.xml_to_dict(response)
        
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

    def consultar_lote(self, lote):
        try:
            with self._create_client(ESocialWsdl.CONSULTAR_LOTE_EVENTOS) as client:
                # Consultar o lote
                response = client.service.ConsultarLoteEventos(lote)
                return response
        except Exception as e:
            logging.error(f"Erro ao processar o lote: {str(e)}")
            return {"erro": "Erro ao processar o lote", "detalhes": str(e)}