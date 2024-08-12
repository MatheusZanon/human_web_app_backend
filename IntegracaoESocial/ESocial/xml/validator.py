from lxml import etree
from ..errors import ESocialValidationError

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