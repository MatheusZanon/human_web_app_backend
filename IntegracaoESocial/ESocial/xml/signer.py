from lxml import etree
from typing import Tuple
import signxml
from signxml import XMLSigner as BaseXMLSigner
from cryptography.hazmat.primitives import serialization

# Override signxml.XMLSigner.check_deprecated_methods() para ignorar os erros e poder utilizar o SHA1, remover quando o e-social aceitar assinaturas mais seguras
class XMLSignerWithSHA1(BaseXMLSigner):
    def check_deprecated_methods(self):
        pass

class XMLSigner:
    """
        Classe para assinar arquivos XML.
    """

    def __init__(self, cert_data: Tuple) -> None:
        """
            Cria uma instância da classe XMLSigner.

            Args:
                cert_data (Tuple): Os dados do certificado.
        """
        self.cert = cert_data
    
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

        """
        signer = XMLSignerWithSHA1(
            method=signxml.methods.enveloped,
            signature_algorithm=signxml.algorithms.SignatureMethod.RSA_SHA256,
            digest_algorithm=signxml.algorithms.DigestAlgorithm.SHA1,
            c14n_algorithm=signxml.algorithms.CanonicalizationMethod.CANONICAL_XML_1_0,
        )
        """

        signer = BaseXMLSigner(
            method=signxml.methods.enveloped,
            signature_algorithm=signxml.algorithms.SignatureMethod.RSA_SHA256,
            digest_algorithm=signxml.algorithms.DigestAlgorithm.SHA256,
            c14n_algorithm=signxml.algorithms.CanonicalizationMethod.CANONICAL_XML_1_0,
        )

        signed = signer.sign(xml, key=key_pem, cert=cert_pem)

        return signed