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
from .xml.helper import XMLHelper, XSDHelper, ESocialEventIDGenerator
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
        cert_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pem')
        key_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pem')

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
                cert_info = "Certificado configurado" if session.cert else "Certificado não configurado"
            yield client
        except Exception as e:
            if self.event_logging_service:
                self.event_logging_service.log(f"Error creating SOAP client: {e}", logging.ERROR)
            raise ESocialConnectionError(f"Error creating SOAP client: {e}")
        finally:
            # Limpar os arquivos temporários
            os.unlink(cert_file.name)
            os.unlink(key_file.name)
    
    def generate_event_id(self, cnpj_cpf: Union[str, int]) -> str:
        """
        Gera um ID de evento baseado no CNPJ/CPF do emissor e timestamp atual.

        Args:
            cnpj_cpf (str | int): O CNPJ ou CPF a ser utilizado como base para o ID.

        Returns:
            str: Um identificador único para o evento, com 36 caracteres.
        """
        
        # Garantir que cnpj_cpf é uma string
        if isinstance(cnpj_cpf, int):
            cnpj_cpf = str(cnpj_cpf)
        
        # Sanitizar o CNPJ/CPF removendo caracteres não numéricos se necessário
        sanitized_cnpj_cpf = ''.join(filter(str.isdigit, cnpj_cpf))
        
        # Verificar o comprimento do CNPJ/CPF
        if len(sanitized_cnpj_cpf) == 14:
            type_of_insc = "1"  # CNPJ
            sanitized_cnpj_cpf = sanitized_cnpj_cpf.ljust(14, '0')
        elif len(sanitized_cnpj_cpf) == 11:
            type_of_insc = "2"  # CPF
            sanitized_cnpj_cpf = sanitized_cnpj_cpf.ljust(11, '0')
        else:
            raise ESocialValidationError("CNPJ/CPF inválido")
        
        # Obter a data e hora atual no formato UTC
        current_time = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        
        # Gerar o número sequencial com 5 dígitos
        sequence_number = f"{len(self.batch_to_send) + 1:05}"

        # Construir o ID completo
        full_id = f"ID{type_of_insc}{sanitized_cnpj_cpf}{current_time}{sequence_number}"

        # Verificar se o ID resultante tem exatamente 36 caracteres
        if len(full_id) != 36:
            raise ESocialValidationError("ID gerado inválido")

        return full_id
    
    def sign(self, xml: etree._Element) -> etree._Element:
        signer = XMLSigner(self.cert)

        return signer.sign(xml)
    
    def create_s1000_envelope(self, event_data: Dict[str, Any], issuer_cnpj_cpf: str = None, user_id: int = None) -> etree._Element:
        nsmap = XSDHelper().get_namespace_from_xsd(ESocialTipoEvento.EVT_INFO_EMPREGADOR)

        s1000_xml = XMLHelper("eSocial", nsmap)

        # evt_id = self.generate_event_id(issuer_cnpj_cpf)
        evt_id = ESocialEventIDGenerator(self.batch_to_send).generate_event_id(issuer_cnpj_cpf[:8].ljust(14, '0'))

        s1000_xml.add_element(None, "evtInfoEmpregador", Id=evt_id)

        s1000_xml.add_element("evtInfoEmpregador", "ideEvento")
        s1000_xml.add_element("evtInfoEmpregador/ideEvento", "tpAmb", text=str(self.ambiente.value))
        s1000_xml.add_element("evtInfoEmpregador/ideEvento", "procEmi", text="1")
        s1000_xml.add_element("evtInfoEmpregador/ideEvento", "verProc", text="1.0")

        s1000_xml.add_element("evtInfoEmpregador", "ideEmpregador")
        if len(str(issuer_cnpj_cpf)) == 14: # Se for cnpj o tipo de inscrição deve ser 1
            s1000_xml.add_element("evtInfoEmpregador/ideEmpregador", "tpInsc", text="1")
            s1000_xml.add_element("evtInfoEmpregador/ideEmpregador", "nrInsc", text=str(issuer_cnpj_cpf)[0:8])
        elif len(str(issuer_cnpj_cpf)) == 11: # Se for cpf o tipo de inscrição deve ser 2
            s1000_xml.add_element("evtInfoEmpregador/ideEmpregador", "tpInsc", text="2")
            s1000_xml.add_element("evtInfoEmpregador/ideEmpregador", "nrInsc", text=str(issuer_cnpj_cpf))
        else:
            raise ESocialValidationError(f"O CNPJ ou CPF do emissor deve ter 14 ou 11 caracteres respectivamente.")
        

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

            if event_data['infoEmpregador']['inclusao']['infoCadastro']:
                s1000_xml.add_element("evtInfoEmpregador/infoEmpregador/inclusao", "infoCadastro")

                if event_data['infoEmpregador']['inclusao']['infoCadastro'].get('classTrib'):
                    s1000_xml.add_element("evtInfoEmpregador/infoEmpregador/inclusao/infoCadastro", "classTrib", text=event_data['infoEmpregador']['inclusao']['infoCadastro']['classTrib'])

                if event_data['infoEmpregador']['inclusao']['infoCadastro'].get('indCoop'):
                    s1000_xml.add_element("evtInfoEmpregador/infoEmpregador/inclusao/infoCadastro", "indCoop", text=event_data['infoEmpregador']['inclusao']['infoCadastro']['indCoop'])

                if event_data['infoEmpregador']['inclusao']['infoCadastro'].get('indConstr'):
                    s1000_xml.add_element("evtInfoEmpregador/infoEmpregador/inclusao/infoCadastro", "indConstr", text=event_data['infoEmpregador']['inclusao']['infoCadastro']['indConstr'])

                if event_data['infoEmpregador']['inclusao']['infoCadastro'].get('indDesFolha'):
                    s1000_xml.add_element("evtInfoEmpregador/infoEmpregador/inclusao/infoCadastro", "indDesFolha", text=event_data['infoEmpregador']['inclusao']['infoCadastro']['indDesFolha'])

                if event_data['infoEmpregador']['inclusao']['infoCadastro'].get('indOpcCP'):
                    s1000_xml.add_element("evtInfoEmpregador/infoEmpregador/inclusao/infoCadastro", "indOpcCP", text=event_data['infoEmpregador']['inclusao']['infoCadastro']['indOpcCP'])

                if event_data['infoEmpregador']['inclusao']['infoCadastro'].get('indPorte'):
                    s1000_xml.add_element("evtInfoEmpregador/infoEmpregador/inclusao/infoCadastro", "indPorte", text=event_data['infoEmpregador']['inclusao']['infoCadastro']['indPorte'])

                if event_data['infoEmpregador']['inclusao']['infoCadastro'].get('indOptRegEletron'):
                    s1000_xml.add_element("evtInfoEmpregador/infoEmpregador/inclusao/infoCadastro", "indOptRegEletron", text=event_data['infoEmpregador']['inclusao']['infoCadastro']['indOptRegEletron'])

                if event_data['infoEmpregador']['inclusao']['infoCadastro'].get('cnpjEFR'):
                    s1000_xml.add_element("evtInfoEmpregador/infoEmpregador/inclusao/infoCadastro", "cnpjEFR", text=event_data['infoEmpregador']['inclusao']['infoCadastro']['cnpjEFR'])

                if event_data['infoEmpregador']['inclusao']['infoCadastro'].get('dtTrans11096'):
                    s1000_xml.add_element("evtInfoEmpregador/infoEmpregador/inclusao/infoCadastro", "dtTrans11096", text=event_data['infoEmpregador']['inclusao']['infoCadastro']['dtTrans11096'])

                if event_data['infoEmpregador']['inclusao']['infoCadastro'].get('indTribFolhaPisCofins'):
                    s1000_xml.add_element("evtInfoEmpregador/infoEmpregador/inclusao/infoCadastro", "indTribFolhaPisCofins", text=event_data['infoEmpregador']['inclusao']['infoCadastro']['indTribFolhaPisCofins'])
        elif present_operations[0] == 'alteracao':
            s1000_xml.add_element("evtInfoEmpregador/infoEmpregador", "alteracao")
        elif present_operations[0] == 'exclusao':
            s1000_xml.add_element("evtInfoEmpregador/infoEmpregador", "exclusao")
        else:
            raise ESocialValidationError("O tipo de operação S-1000 deve conter exatamente um tipo de operação: 'inclusao', 'alteracao' ou 'exclusao'.")
        
        if self.event_logging_service:
            self.event_logging_service.log(f"S-1000 Envelope created: ID: {evt_id}, XML: {s1000_xml.to_string()}")
        return s1000_xml.root
    
    def create_s1200_envelope(self, evt_data: Dict[str, Any], issuer_cnpj_cpf: str = None, user_id: int = None):
        """
        Cria o envelope do evento S-1200. (Remuneração de trabalhador vinculado ao Regime Geral de Previdência Social)

        Deve ser utilizado para informar rubricas de natureza remuneratória ou não para todos os seus trabalhadores, estagiários e bolsistas, exceto àqueles vinculados ao RPPS (Regime Próprio de Previdência Social) cuja informação deve ser prestada em evento próprio (S-1202).
        """
        nsmap = XSDHelper().get_namespace_from_xsd(ESocialTipoEvento.EVT_REMUNERACAO_TRABALHADOR_RGPS)

        evt_id = ESocialEventIDGenerator(self.batch_to_send).generate_event_id(issuer_cnpj_cpf[:8].ljust(14, '0'))

        s1200_xml = XMLHelper("eSocial", nsmap)

        s1200_xml.add_element(None, ESocialTipoEvento.EVT_REMUNERACAO_TRABALHADOR_RGPS.value[0], Id=evt_id)

        s1200_xml.add_element("evtRemun", "ideEvento")
        s1200_xml.add_element("evtRemun/ideEvento", "indRetif", text=evt_data['ideEvento']['indRetif'])
        if evt_data['ideEvento']['indRetif'] == '2':
            s1200_xml.add_element("evtRemun/ideEvento", "nrRecibo", text=evt_data['ideEvento']['nrRecibo'])
        s1200_xml.add_element("evtRemun/ideEvento", "indApuracao", text=evt_data['ideEvento']['indApuracao'])
        if evt_data['ideEvento']['indApuracao'] == '1':
            mes_ano_ref = datetime.strptime(evt_data['ideEvento']['perApur'], '%m%Y').strftime('%Y%m')
            s1200_xml.add_element("evtRemun/ideEvento", "perApur", text=mes_ano_ref)
        elif evt_data['ideEvento']['indApuracao'] == '2':
            mes_ano_ref = datetime.strptime(evt_data['ideEvento']['perApur'], '%Y%m').strftime('%Y')
            s1200_xml.add_element("evtRemun/ideEvento", "perApur", text=mes_ano_ref)
        s1200_xml.add_element("evtRemun/ideEvento", "indGuia", text="1") # Só existe 1 tipo de guia, deveria criar um parametro para ser enviado da mesma forma?
        s1200_xml.add_element("evtRemun/ideEvento", "tpAmb", text=evt_data['ideEvento']['tpAmb'])
        s1200_xml.add_element("evtRemun/ideEvento", "procEmi", text=evt_data['ideEvento']['procEmi'])
        s1200_xml.add_element("evtRemun/ideEvento", "verProc", text=evt_data['ideEvento']['verProc'])

        s1200_xml.add_element("evtRemun", "ideEmpregador")
        s1200_xml.add_element("evtRemun/ideEmpregador", "tpInsc", text=evt_data['ideEmpregador']['tpInsc'])
        s1200_xml.add_element("evtRemun/ideEmpregador", "nrInsc", text=evt_data['ideEmpregador']['nrInsc'])

        s1200_xml.add_element("evtRemun", "ideTransmissor")
        s1200_xml.add_element("evtRemun/ideTransmissor", "tpInsc", text=evt_data['ideTransmissor']['tpInsc'])
        s1200_xml.add_element("evtRemun/ideTransmissor", "nrInsc", text=evt_data['ideTransmissor']['nrInsc'])

        s1200_xml.add_element("evtRemun", "ideTrabalhador")
        s1200_xml.add_element("evtRemun/ideTrabalhador", "cpfTrab", text=evt_data['ideTrabalhador']['cpfTrab'])

        if evt_data['ideTrabalhador']['infoMV']:
            s1200_xml.add_element("evtRemun/ideTrabalhador", "infoMV")
            s1200_xml.add_element("evtRemun/ideTrabalhador/infoMV", "indMV", text=evt_data['ideTrabalhador']['infoMV']['indMV'])

            s1200_xml.add_element("evtRemun/ideTrabalhador", "remunOutrEmpr")
            s1200_xml.add_element("evtRemun/ideTrabalhador/remunOutrEmpr", "tpInsc", text=evt_data['ideTrabalhador']['remunOutrEmpr']['tpInsc'])
            s1200_xml.add_element("evtRemun/ideTrabalhador/remunOutrEmpr", "nrInsc", text=evt_data['ideTrabalhador']['remunOutrEmpr']['nrInsc'])
            s1200_xml.add_element("evtRemun/ideTrabalhador/remunOutrEmpr", "codCateg", text=evt_data['ideTrabalhador']['remunOutrEmpr']['codCateg'])
            s1200_xml.add_element("evtRemun/ideTrabalhador/remunOutrEmpr", "vlrRemunOE", text=evt_data['ideTrabalhador']['remunOutrEmpr']['vlrRemunOE'])
        
        if evt_data['ideTrabalhador']['infoComplem']:
            s1200_xml.add_element("evtRemun/ideTrabalhador", "infoComplem")
            s1200_xml.add_element("evtRemun/ideTrabalhador/infoComplem", "nmTrab", text=evt_data['ideTrabalhador']['infoComplem']['nmTrab'])
            s1200_xml.add_element("evtRemun/ideTrabalhador/infoComplem", "dtNascto", text=evt_data['ideTrabalhador']['infoComplem']['dtNascto'])

            if evt_data['ideTrabalhador']['infoComplem']['sucessaoVinc']:
                s1200_xml.add_element("evtRemun/ideTrabalhador/infoComplem", "sucessaoVinc")
                s1200_xml.add_element("evtRemun/ideTrabalhador/infoComplem/sucessaoVinc", "tpInsc", text=evt_data['ideTrabalhador']['infoComplem']['sucessaoVinc']['tpInsc'])
                s1200_xml.add_element("evtRemun/ideTrabalhador/infoComplem/sucessaoVinc", "nrInsc", text=evt_data['ideTrabalhador']['infoComplem']['sucessaoVinc']['nrInsc'])
                s1200_xml.add_element("evtRemun/ideTrabalhador/infoComplem/sucessaoVinc", "matricAnt", text=evt_data['ideTrabalhador']['infoComplem']['sucessaoVinc']['matricAnt'])
                s1200_xml.add_element("evtRemun/ideTrabalhador/infoComplem/sucessaoVinc", "dtAdm", text=evt_data['ideTrabalhador']['infoComplem']['sucessaoVinc']['dtAdm'])

                if evt_data['ideTrabalhador']['infoComplem']['sucessaoVinc']['observacao']:
                    s1200_xml.add_element("evtRemun/ideTrabalhador/infoComplem/sucessaoVinc", "observacao", text=evt_data['ideTrabalhador']['infoComplem']['sucessaoVinc']['observacao'])
        
        if evt_data['ideTrabalhador']['procJudTrab']:
            s1200_xml.add_element("evtRemun/ideTrabalhor", "procJudTrab")
            s1200_xml.add_element("evtRemun/ideTrabalhador/procJudTrab", "tpTrib", text=evt_data['ideTrabalhador']['procJudTrab']['tpTrib'])
            s1200_xml.add_element("evtRemun/ideTrabalhador/procJudTrab", "nrProcJud", text=evt_data['ideTrabalhador']['procJudTrab']['nrProcJud'])
            s1200_xml.add_element("evtRemun/ideTrabalhador/procJudTrab", "codSusp", text=evt_data['ideTrabalhador']['procJudTrab']['codSusp'])
        
        if evt_data['ideTrabalhador']['infoInterm']:
            s1200_xml.add_element("evtRemun/ideTrabalhador", "infoInterm")
            s1200_xml.add_element("evtRemun/ideTrabalhador/infoInterm", "dia", text=evt_data['ideTrabalhador']['infoInterm']['dia'])
        
        s1200_xml.add_element("evtRemun", "dmDev")

        for dmDev in evt_data['dmDev']:
            s1200_xml.add_element("evtRemun/dmDev", "ideDmDev", text=evt_data['dmDev']['ideDmDev'])
            s1200_xml.add_element("evtRemun/dmDev", "codCateg", text=evt_data['dmDev']['codCateg'])

            if evt_data['dmDev']['indRRA']
                s1200_xml.add_element("evtRemun/dmDev", "indRRA", text=evt_data['dmDev']['indRRA'])

                if evt_data['dmDev']['indRRA']['infoRRA']:
                    s1200_xml.add_element("evtRemun/dmDev/indRRA", "infoRRA")
                    s1200_xml.add_element("evtRemun/dmDev/indRRA/infoRRA", "tpProcRRA", text=evt_data['dmDev']['indRRA']['infoRRA']['tpProcRRA'])
                    s1200_xml.add_element("evtRemun/dmDev/indRRA/infoRRA", "nrProcRRA", text=evt_data['dmDev']['indRRA']['infoRRA']['nrProcRRA'])
                    s1200_xml.add_element("evtRemun/dmDev/indRRA/infoRRA", "descRRA", text=evt_data['dmDev']['indRRA']['infoRRA']['descRRA'])
                    s1200_xml.add_element("evtRemun/dmDev/indRRA/infoRRA", "qtdMesesRRA", text=evt_data['dmDev']['indRRA']['infoRRA']['qtdMesesRRA'])

                    if evt_data['dmDev']['indRRA']['infoRRA']['despProcJud']:
                        s1200_xml.add_element("evtRemun/dmDev/indRRA/infoRRA", "despProcJud")
                        s1200_xml.add_element("evtRemun/dmDev/indRRA/infoRRA/despProcJud", "vlrDespCustas", text=evt_data['dmDev']['indRRA']['infoRRA']['despProcJud']['vlrDespCustas'])
                        s1200_xml.add_element("evtRemun/dmDev/indRRA/infoRRA/despProcJud", "vlrDespAdvogados", text=evt_data['dmDev']['indRRA']['infoRRA']['despProcJud']['vlrDespAdvogados'])
            
                if evt_data['dmDev']['indRRA']['ideAdv']:
                    s1200_xml.add_element("evtRemun/dmDev/indRRA", "ideAdv")
                    s1200_xml.add_element("evtRemun/dmDev/indRRA/ideAdv", "tpInsc", text=evt_data['dmDev']['indRRA']['ideAdv']['tpInsc'])
                    s1200_xml.add_element("evtRemun/dmDev/indRRA/ideAdv", "nrInsc", text=evt_data['dmDev']['indRRA']['ideAdv']['nrInsc'])

                    if evt_data['dmDev']['indRRA']['ideAdv']['vlrAdv']:
                        s1200_xml.add_element("evtRemun/dmDev/indRRA/ideAdv", "vlrAdv", text=evt_data['dmDev']['indRRA']['ideAdv']['vlrAdv'])
        
            if evt_data['dmDev']['infoPerApur']:
                s1200_xml.add_element("evtRemun/dmDev", "infoPerApur")
                for ideEstabLot in evt_data['dmDev']['infoPerApur']['ideEstabLot']:
                    s1200_xml.add_element("evtRemun/dmDev/infoPerApur", "ideEstabLot")
                    s1200_xml.add_element("evtRemun/dmDev/infoPerApur/ideEstabLot", "tpInsc", text=ideEstabLot['tpInsc'])
                    s1200_xml.add_element("evtRemun/dmDev/infoPerApur/ideEstabLot", "nrInsc", text=ideEstabLot['nrInsc'])
                    s1200_xml.add_element("evtRemun/dmDev/infoPerApur/ideEstabLot", "codLotacao", text=ideEstabLot['codLotacao'])
                    s1200_xml.add_element("evtRemun/dmDev/infoPerApur/ideEstabLot", "qtdDiasAv", text=ideEstabLot['qtdDiasAv'])

        
        return s1200_xml.root

    
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
            
            print(lote_eventos_xml.to_string())
            
            return lote_eventos_xml.root
        except Exception as e:
            logging.error(f"Erro ao processar o lote: {str(e)}")
    
    def _create_retrive_envelope(self, protocol_number: str):
        try:
            if not protocol_number:
                raise ESocialValidationError("O 'protocoloEnvio' não pode ser vazio")
            if not self.transmissorCpfCnpj:
                raise ESocialValidationError("Cpf ou Cnpj do transmissor não informado")

            # Criar o elemento raiz do lote com prefixo de namespace
            nsmap = XSDHelper().get_namespace_from_xsd(ESocialTipoEvento.EVT_CONSULTAR_LOTE_EVENTOS)
            retrieve_envelope = XMLHelper("eSocial", nsmap)
            retrieve_envelope.add_element(None, "consultaLoteEventos")
            retrieve_envelope.add_element("consultaLoteEventos", "protocoloEnvio", text=str(protocol_number))

            return retrieve_envelope.root
        except Exception as e:
            logging.error(f"Erro ao processar a consulta do lote: {str(e)}")
        
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
                XMLHelper(lote_eventos).to_file()

                BatchElement = client.get_element('ns1:EnviarLoteEventos')

                # Enviar o lote
                response = client.service.EnviarLoteEventos(BatchElement(loteEventos=lote_eventos))
                if self.event_logging_service:
                    self.event_logging_service.log(f"Batch sent: Group ID: {group_id}")
                    self.event_logging_service.log(f"Transmissor tpInsc: {self.transmissorTpInsc}")
                    self.event_logging_service.log(f"Transmissor nrInsc: {self.transmissorCpfCnpj}")
                    self.event_logging_service.log(f"Empregador tpInsc: {lote_eventos.find('.//ideEmpregador/tpInsc', lote_eventos.nsmap).text}")
                    self.event_logging_service.log(f"Empregador nrInsc: {lote_eventos.find('.//ideEmpregador/nrInsc', lote_eventos.nsmap).text}")
                
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
    
    def retrieve(self, wsdl: str, protocol_number: str) -> Dict[str, Any]:
        try:
            self.event_logging_service.log(f"Retrieving batch: {protocol_number} | wsdl: {wsdl}")
            if not protocol_number:
                raise ESocialValidationError("O 'protocoloEnvio' não pode ser vazio")
            
            with self._create_client(wsdl) as client:
                batch_to_search = self._create_retrive_envelope(protocol_number)

                SearchElement = client.get_element('ns1:ConsultarLoteEventos')

                print(etree.tostring(batch_to_search, pretty_print=True).decode('utf-8'))

                # validate batch
                xsd_batch = XSDHelper().xsd_from_file(ESocialTipoEvento.EVT_CONSULTAR_LOTE_EVENTOS)
                XMLValidator(batch_to_search, xsd_batch).validate()

                response = client.service.ConsultarLoteEventos(SearchElement(consulta=batch_to_search))

                xsd_response = XSDHelper().xsd_from_file(ESocialTipoEvento.EVT_CONSULTAR_LOTE_EVENTOS, 'retorno')
                XMLValidator(response, xsd_response).validate()

                response_json = self.decode_response(response)
                
                return response_json
        except Exception as e:
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