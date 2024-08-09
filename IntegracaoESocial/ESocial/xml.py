from lxml import etree
from typing import Optional, Dict, Any
import os
from datetime import datetime, UTC
from typing import Literal
from .errors import ESocialValidationError
from .enums import ESocialTipoEvento
from .constants import INTEGRATION_ROOT_PATH

class XMLValidator:
    """
        Classe para auxiliar na validação de arquivos XML.

        Args:
            xml: lxml.etree._ElementTree
            xsd: lxml.etree.XMLSchema
    """

    def __init__(self, xml: etree._ElementTree, xsd: etree.XMLSchema) -> None:
        self.xml = xml
        self.xsd = xsd
        self.errors = None
    
    def is_valid(self) -> bool:
        """
            Verifica se o arquivo XML é válido pelo esquema XSD.

            Returns:
                bool: True se o arquivo for válido pelo esquema XSD, False caso contrário.
        """

        is_valid = self.xsd.validate(self.xml)
        if not is_valid:
            self.errors = self.xsd.error_log
        return is_valid
    
    def validate(self) -> None:
        """
            Verifica se o arquivo XML é válido pelo esquema XSD, e lança uma exceção caso o arquivo seja inválido.
        """
        if not self.is_valid():
            raise ESocialValidationError(self.errors)
    

class XMLHelper:
    """
    Classe para auxiliar na criação de documentos XML.

    Args:
        root_element (str): Nome do elemento raiz.
        xmlns (str, optional): Namespace XML padrão (xmlns). Defaults to None.
        **attrs: Atributos do elemento raiz.
    """

    def __init__(self, root_element: str, xmlns: Optional[str] = None, **attrs: Any) -> None:
        """
        Inicializa a classe XMLHelper com um elemento raiz e atributos opcionais.

        Args:
            root_element (str): Nome do elemento raiz.
            xmlns (str, optional): Namespace XML padrão (xmlns). Defaults to None.
            **attrs: Atributos do elemento raiz.
        """
        self.nsmap = {None: xmlns} if xmlns is not None else {}
        self.root = self.create_root_element(root_element, self.nsmap, **attrs)

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

        if not os.path.exists(generated_folder):
            os.makedirs(generated_folder)

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


def xsd_from_file(eventType: ESocialTipoEvento, type: Literal['envio', 'retorno'] = 'envio') -> etree.XMLSchema:
    """
        Retorna uma instância de XSD a partir de um arquivo.

        Args:
            eventType (ESocialTipoEvento): O nome do arquivo.
            type (Literal['envio', 'retorno'], optional): O tipo de arquivo. O padrão é 'envio'.

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
        except Exception as e:
            raise ValueError(f"Erro ao ler o namespace do XSD: {e}")