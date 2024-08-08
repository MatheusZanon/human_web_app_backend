from zeep import Client
from zeep.transports import Transport
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from contextlib import contextmanager
import tempfile
import os
from typing import Dict, Any
import signxml
from signxml import XMLSigner
from lxml import etree
from .errors import ESocialConnectionError, ESocialError, ESocialValidationError
from .enums import Operation, ESocialWsdl, ESocialTipoEvento, Environment, ESocialAmbiente
from .constants import WS_URL
from .services import EventLogService
import logging

# Override signxml.XMLSigner.check_deprecated_methods() para ignorar os erros e poder utilizar o SHA1, remover quando o e-social aceitar assinaturas mais seguras
class XMLSignerWithSHA1(XMLSigner):
    def check_deprecated_methods(self):
        pass

class IntegracaoESocial:
    def __init__(self, cert_path, cert_password, batch_to_send, ambiente: ESocialAmbiente = ESocialAmbiente.PRODUCAO):
        self.cert_path = cert_path
        self.cert_password = cert_password
        self.ambiente = ambiente
        self.cert = self._load_cert()
        self.event_logging_service = EventLogService()
    
    def _load_cert(self):
        with open(self.cert_path, 'rb') as cert_file:
            pfx_data = cert_file.read()
        private_key, certificate, _ = pkcs12.load_key_and_certificates(
            pfx_data, self.cert_password.encode(), None
        )
        return (certificate, private_key)
    
    def get_wsdl_url(env: Environment, operation: Operation) -> str:
        return WS_URL[env][operation]

    @contextmanager
    def _create_client(self, service_path: ESocialWsdl):
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
            wsdl = self._get_wsdl_url(service_path)
            client = Client(wsdl, transport=transport)
            
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
        evt_filename = event.value[0]
        evt_key = event.value[1]

        # Obter o namespace do XSD
        ns = self.get_namespace_from_xsd(xsd_path)

        if not ns:
            raise ValueError(f"Não foi possível obter o namespace para o evento: {evt_filename}")
        
        nsmap = {None: ns}

        # Criar o elemento raiz
        root = etree.Element(f"{{{ns}}}eSocial", nsmap=nsmap)

        # Criar o elemento do evento
        evento = etree.SubElement(root, f"{{{ns}}}{evt_key}", Id=event_id, versao="2.0")

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

    def sign_xml(self, xml, evt_id):
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

        signed = signer.sign(xml, key=key_pem, cert=cert_pem, reference_uri=evt_id)

        return signed

    def create_event(self, event_data: Dict[str, Any], event_type: ESocialTipoEvento, issuer_cnpj_cpf: str = None, signer_cnpj_cpf: str = None, user_id: int = None):
        evt_filename = event_type.value[0]
        evt_key = event_type.value[1]
        
        # Obter o caminho do XSD
        xsd_path = os.path.join(os.path.dirname(__file__), 'config', 'xsd', f'{evt_filename}.xsd')

        evt_id_numeric = self.event_logging_service.get_next_event_id()
        evt_id = f"ID{evt_id_numeric}"

        xml_tree = self.generate_event_xml(event=event_type, event_data=event_data, event_id=evt_id, xsd_path=xsd_path)
        signed_xml = self.sign_xml(xml_tree.getroot(), evt_id)

        # Validar o XML assinado
        self.validate_event_xml(signed_xml, xsd_path)
        
        # Converter o XML assinado para string
        xml_string = etree.tostring(signed_xml, pretty_print=True, xml_declaration=True, encoding='UTF-8').decode()
        self.event_logging_service.log_event(event_id=evt_id_numeric, event_type=evt_key, event_data=event_data, event_issuer=issuer_cnpj_cpf, event_signer=signer_cnpj_cpf, user_id=user_id)

        print(xml_string)
        # return None
        return signed_xml

    def check_event_status(self, protocol):
        # Implemente a consulta de status do evento
        pass

    def enviar_lote(self, eventos, transmissor_tpInsc, transmissor_nrInsc):
        try:
            with self._create_client(ESocialWsdl.ENVIAR_LOTE_EVENTOS) as client:
                # Criar cliente do web service
                # client = self._create_client(ESocialWsdl.ENVIAR_LOTE_EVENTOS)

                # Garantir que eventos seja uma lista
                if not isinstance(eventos, list):
                    eventos = [eventos]

                # Criar o elemento raiz do lote com prefixo de namespace
                nsmap = {"esocial": "http://www.esocial.gov.br/schema/lote/eventos/envio/v1_1_1"}
                lote_eventos = etree.Element("{http://www.esocial.gov.br/schema/lote/eventos/envio/v1_1_1}eSocial", nsmap=nsmap)
                envio_lote = etree.SubElement(lote_eventos, "{http://www.esocial.gov.br/schema/lote/eventos/envio/v1_1_1}envioLoteEventos", grupo="1")

                # Extrair informações do empregador do primeiro evento válido
                ide_empregador = None
                for evento in eventos:
                    primeiro_evento = etree.fromstring(evento) if isinstance(evento, str) else evento
                    ns = {"ns": "http://www.esocial.gov.br/schema/evt/evtAdmissaoPreliminar/v02_00_00"}
                    ide_empregador = primeiro_evento.find(".//ns:ideEmpregador", namespaces=ns)
                    if ide_empregador is not None:
                        break

                if ide_empregador is None:
                    raise ValueError("Elemento ideEmpregador não encontrado em nenhum evento")

                tpInsc = ide_empregador.find("ns:tpInsc", namespaces=ns)
                nrInsc = ide_empregador.find("ns:nrInsc", namespaces=ns)

                if tpInsc is None or nrInsc is None:
                    raise ValueError("Elementos tpInsc ou nrInsc não encontrados no elemento ideEmpregador")

                # Adicionar ideEmpregador
                lote_ide_empregador = etree.SubElement(envio_lote, "{http://www.esocial.gov.br/schema/lote/eventos/envio/v1_1_1}ideEmpregador")
                etree.SubElement(lote_ide_empregador, "{http://www.esocial.gov.br/schema/lote/eventos/envio/v1_1_1}tpInsc").text = tpInsc.text
                etree.SubElement(lote_ide_empregador, "{http://www.esocial.gov.br/schema/lote/eventos/envio/v1_1_1}nrInsc").text = nrInsc.text

                # Adicionar ideTransmissor
                ide_transmissor = etree.SubElement(envio_lote, "{http://www.esocial.gov.br/schema/lote/eventos/envio/v1_1_1}ideTransmissor")
                etree.SubElement(ide_transmissor, "{http://www.esocial.gov.br/schema/lote/eventos/envio/v1_1_1}tpInsc").text = transmissor_tpInsc
                etree.SubElement(ide_transmissor, "{http://www.esocial.gov.br/schema/lote/eventos/envio/v1_1_1}nrInsc").text = transmissor_nrInsc

                # Adicionar eventos
                eventos_element = etree.SubElement(envio_lote, "{http://www.esocial.gov.br/schema/lote/eventos/envio/v1_1_1}eventos")

                for evento in eventos:
                    if isinstance(evento, str):
                        try:
                            evento_xml = etree.fromstring(evento)
                        except etree.XMLSyntaxError as e:
                            logging.error(f"XML inválido: {str(e)}")
                            continue
                    elif isinstance(evento, etree._Element):
                        evento_xml = evento
                    else:
                        logging.warning(f"Tipo de evento não suportado: {type(evento)}")
                        continue
                    
                    # Encontrar o Id do evento interno
                evento_id = evento_xml.find(".//*[@Id]")
                if evento_id is not None:
                    id_value = evento_id.get("Id")
                    
                    # Criar o elemento evento com o atributo Id
                    evento_element = etree.SubElement(eventos_element, "{http://www.esocial.gov.br/schema/lote/eventos/envio/v1_1_1}evento", Id=id_value)
                    
                    # Adicionar o conteúdo do evento
                    evento_element.append(evento_xml)
                else:
                    logging.warning("Evento sem atributo Id encontrado")

                # Converter o lote para string
                lote_eventos_str = etree.tostring(lote_eventos, encoding='unicode', pretty_print=True)
                print(lote_eventos_str)

                # Validar o lote
                logging.info(f"Lote XML gerado:\n{lote_eventos_str}")
                xsd_path = os.path.join(os.path.dirname(__file__), 'config', 'xsd', f'{ESocialTipoEvento.EVT_ENVIO_LOTE_EVENTOS.value[0]}.xsd')
                self.validate_event_xml(lote_eventos, xsd_path)

                client.wsdl.dump()
                BatchElement = client.get_element('ns1:EnviarLoteEventos')

                # Enviar o lote
                response = client.service.EnviarLoteEventos(BatchElement(loteEventos=lote_eventos))

                response_json = self.decode_response(response)
                return response_json
        except Exception as e:
            logging.error(f"Erro ao processar o lote: {str(e)}")
            return {"erro": "Erro ao processar o lote", "detalhes": str(e)}
    
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
                child_dict[child_tag] = recursive_dict(child)
            
            return {tag: child_dict}

        return recursive_dict(element)

    def decode_response(self, response: etree._Element) -> Dict[str, Any]:
        """Converte uma resposta XML do webservice eSocial para um dicionário JSON, removendo namespaces e indicando sucesso ou falha."""
        def get_status(el: etree._Element) -> Dict[str, Any]:
            """Extrai o status da resposta XML."""
            status_element = el.find(".//status")
            if status_element is not None:
                cd_resposta = status_element.findtext("cdResposta")
                desc_resposta = status_element.findtext("descResposta")
                return {"code": cd_resposta, "message": desc_resposta}
            return {"code": None, "message": None}

        # Converte o XML para dicionário sem namespaces
        response_dict = self.xml_to_dict(response)
        
        # Extrai status da resposta
        status = get_status(response, 'status')
        
        # Verifica se a resposta indica sucesso ou falha
        if status['code'] and int(status['code']) != 200:
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