from lxml import etree
from typing import Optional, Literal, Dict, Any
from datetime import datetime, UTC
from typing import Union
import pytz
import os
from ..enums import ESocialTipoEvento
from ..constants import INTEGRATION_ROOT_PATH
from ..errors import ESocialError, ESocialValidationError

class XMLHelper:
    """
    Classe para auxiliar na criação de documentos XML.

    Args:
        root_element (str): Nome do elemento raiz.
        xmlns (str, optional): Namespace XML padrão (xmlns). Defaults to None.
        **attrs: Atributos do elemento raiz.
    """

    def __init__(self, root_element: str | etree._Element, xmlns: Optional[str] = None, **attrs: Any) -> None:
        """
        Inicializa a classe XMLHelper com um elemento raiz e atributos opcionais.

        Args:
            root_element (str, etree._Element): Nome do elemento raiz ou o elemento raiz.
            xmlns (str, optional): Namespace XML padrão (xmlns). Defaults to None.
            **attrs: Atributos do elemento raiz.
        """
        self.nsmap = {None: xmlns} if xmlns is not None else {}

        if isinstance(root_element, str):
            self.root = self.create_root_element(root_element, self.nsmap, **attrs)
        elif isinstance(root_element, etree._Element):
            self.root = root_element

    def create_root_element(self, root_tag: str, ns: Optional[Dict[Optional[str], str]] = None, **kwargs: Any) -> etree._Element:
        """
        Cria um elemento raiz com os atributos passados como parâmetros.

        Args:
            root_tag (str): Nome do elemento raiz.
            ns (dict, optional): Dicionário de namespace. Defaults to None.
            **kwargs: Atributos do elemento raiz.

        Returns:
            etree._Element: O elemento raiz criado.
        """
        if ns is None:
            ns = {}

        if ns:
            root_tag = f"{{{ns.get(None, '')}}}{root_tag}"
        
        root_tag = etree.Element(root_tag, nsmap=ns)

        if kwargs:
            for attr, value in kwargs.items():
                root_tag.set(attr, self.normalize_text(str(value)))
        return root_tag
    
    def add_element(self, element_tag: Optional[str], tag_name: str, text: Optional[str] = None, **attrs: Any) -> Optional[etree._Element]:
        """
        Adiciona um elemento ao XML com o tag_name especificado e atributos opcionais.

        Args:
            element_tag (str, optional): Tag do elemento onde o novo elemento deve ser adicionado.
            tag_name (str): Nome do novo elemento.
            text (str, optional): Texto do novo elemento.
            **attrs: Atributos do novo elemento.

        Returns:
            Optional[etree._Element]: O novo elemento adicionado ou None se falhar.
        """
        tag_root = self.root
        if element_tag:
            tag_root = self.root.find(self._apply_namespaces(element_tag), namespaces=self.nsmap)

        if tag_root is not None:
            tag_name = self._apply_namespace(tag_name)
            sub_tag = etree.SubElement(tag_root, tag_name, nsmap=self.nsmap) if self.nsmap else etree.SubElement(tag_root, tag_name)
            
            if attrs:
                for attr, value in attrs.items():
                    sub_tag.set(attr, self.normalize_text(str(value)))
            if text is not None:
                sub_tag.text = self.normalize_text(text)
            
            return sub_tag
        return None

    def _apply_namespaces(self, tag: str) -> str:
        """
        Aplica namespaces aos tags se houver mais de um namespace.

        Args:
            tag (str): Tag do elemento.

        Returns:
            str: Tag com namespaces aplicados.
        """
        if len(self.nsmap) == 1 and None in self.nsmap:
            ns_uri = self.nsmap[None]
            return tag.replace('/', f"/{{{ns_uri}}}", 1)
        return tag

    def _apply_namespace(self, tag_name: str) -> str:
        """
        Aplica o namespace ao nome do tag se houver exatamente um namespace.

        Args:
            tag_name (str): Nome do tag.

        Returns:
            str: Nome do tag com namespace aplicado.
        """
        if len(self.nsmap) == 1 and None in self.nsmap:
            ns_uri = self.nsmap[None]
            return f"{{{ns_uri}}}{tag_name}"
        return tag_name

    def normalize_text(self, text: str) -> str:
        """
        Normaliza o texto para XML, escapando caracteres especiais.

        Args:
            text (str): Texto a ser normalizado.

        Returns:
            str: Texto normalizado.
        """
        _chars = {
            '>': '&gt;',
            '<': '&lt;',
            '&': '&amp;',
            '"': '&quot;',
            "'": '&apos;',
        }
        for char, replacement in _chars.items():
            text = text.replace(char, replacement)
        return text
    
    def to_string(self) -> str:
        """
        Retorna a representação em string do XML.

        Returns:
            str: A representação em string do XML.
        """
        return etree.tostring(self.root, pretty_print=True, encoding='utf-8', xml_declaration=True).decode()
    
    def to_file(self, filename: Optional[str] = None) -> None:
        """
        Exporta o XML para um arquivo.

        Args:
            filename (str): Nome do arquivo.
        """

        previous_folder = os.path.normpath(INTEGRATION_ROOT_PATH + os.sep + os.pardir)
        generated_folder = os.path.normpath(previous_folder + os.sep + "generated")

        os.makedirs(generated_folder, exist_ok=True)

        if not filename:
            # Cria um nome com o primeiro id encontrado ou gera com base na timestamp UTC

            for child in self.root.iterchildren():
                event_id = child.get('Id')
                if event_id:
                    filename = f"event_{event_id}.xml"
                    break

            if not filename:
                filename = f"event_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.xml"

        if not filename.endswith('.xml'):
            filename += '.xml'


        file_path = os.path.join(generated_folder, filename)
        
        with open(file_path, 'w', encoding='UTF-8') as file:
            file.write(self.to_string())
    
    def to_dict(self) -> Dict[str, Any]:
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

        return recursive_dict(self.root)
    
class XSDHelper:
    """
        Classe para auxiliar na manipulação e extração de informações de um arquivo XSD.
    """

    @staticmethod
    def xsd_from_file(eventType: ESocialTipoEvento, type: Literal['envio', 'retorno'] = 'envio') -> etree.XMLSchema:
        """
            Retorna uma instância de XSD a partir de um arquivo.

            Args:
                eventType (ESocialTipoEvento): O tipo do evento.
                type (Literal['envio', 'retorno'], optional): O tipo de operação (envio ou retorno). O padrão é 'envio'.

            Returns:
                lxml.etree.XMLSchema: A instância de XSD.
        """

        if type == 'envio':
            xsd_path = os.path.join(INTEGRATION_ROOT_PATH, 'config', 'xsd', f"{eventType.value[1]}.xsd")
        else:
            xsd_path = os.path.join(INTEGRATION_ROOT_PATH, 'config', 'xsd', f"{eventType.value[2]}.xsd")
        
        with open(xsd_path, 'r', encoding='UTF-8') as file:
            xmlschema = etree.parse(file)
        
        return etree.XMLSchema(xmlschema)

    @staticmethod
    def get_namespace_from_xsd(eventType: ESocialTipoEvento, type: Literal['envio', 'retorno'] = 'envio') -> str:
            """
                Retorna o targetNamespace do XSD do evento com base no tipo de evento.

                Args:
                    eventType (ESocialTipoEvento): O tipo de evento.
                    type (Literal['envio', 'retorno'], optional): O tipo de arquivo. O padrão é 'envio'.

                Returns:
                    str: O targetNamespace do XSD do evento.
            """
            if type == 'envio':
                xsd_path = os.path.join(INTEGRATION_ROOT_PATH, 'config', 'xsd', f"{eventType.value[1]}.xsd")
            else:
                xsd_path = os.path.join(INTEGRATION_ROOT_PATH, 'config', 'xsd', f"{eventType.value[2]}.xsd")

            try:
                tree = etree.parse(xsd_path)
                root = tree.getroot()
                return root.get('targetNamespace')
            except OSError as e:
                raise ESocialError(f"Erro ao ler o arquivo XSD: {e}")
            except etree.XMLSyntaxError as e:
                raise ESocialError(f"Erro ao analisar o arquivo XSD: {e}")
            except Exception as e:
                raise ESocialError(f"Erro ao ler o namespace do XSD: {e}")

class ESocialEventIDGenerator:
    def __init__(self, batch_to_send):
        self.batch_to_send = batch_to_send

    def generate_event_id(self, cnpj_cpf: Union[str, int]) -> str:
        """
        Gera um ID de evento baseado no CNPJ/CPF do emissor e timestamp atual.

        Args:
            cnpj_cpf (str | int): O CNPJ ou CPF a ser utilizado como base para o ID.

        Returns:
            str: Um identificador único para o evento, com exatamente 36 caracteres.
        """
        
        # Garantir que cnpj_cpf é uma string
        if isinstance(cnpj_cpf, int):
            cnpj_cpf = str(cnpj_cpf)
        
        # Sanitizar o CNPJ/CPF removendo caracteres não numéricos se necessário
        sanitized_cnpj_cpf = ''.join(filter(str.isdigit, cnpj_cpf))
        
        # Verificar o tipo de inscrição (1 = CNPJ, 2 = CPF)
        if len(sanitized_cnpj_cpf) == 14:
            tipo_inscricao = '1'  # CNPJ
            cnpj_cpf = sanitized_cnpj_cpf.ljust(14, '0')  # Completa com zeros à direita se necessário
        elif len(sanitized_cnpj_cpf) == 11:
            tipo_inscricao = '2'  # CPF
            cnpj_cpf = sanitized_cnpj_cpf  # CPF já tem 11 dígitos
        else:
            raise ESocialValidationError("CNPJ/CPF inválido")
        
        # Obter a data e hora atual no formato UTC
        current_time = datetime.now(pytz.UTC).strftime("%Y%m%d%H%M%S")
        
        # Gerar o número sequencial da chave (5 dígitos, zeros à esquerda)
        numero_sequencial = str(len(self.batch_to_send) + 1).zfill(5)
        
        # Criar o ID completo conforme a regra
        full_id = f"ID{tipo_inscricao}{cnpj_cpf}{current_time}{numero_sequencial}"
        
        # Retornar o ID completo que deve ter exatamente 36 caracteres
        return full_id