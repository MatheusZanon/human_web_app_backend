import logging
import sys
import os
from typing import Optional
from datetime import datetime, UTC
from IntegracaoESocial.serializers import EventLogSerializer
from IntegracaoESocial.models import EventLog

class EventLogService:
    def __init__(self, logger_name: str = 'eventlog', log_dir: Optional[str] = '/tmp/eventlog'):
        """
        Inicializa o serviço de log de eventos.

        Args:
            logger_name (str): Nome do logger.
            log_dir (str, optional): Diretório onde os logs serão armazenados. O padrão é '/tmp/eventlog'.
        """
        # Definindo o formato do log
        self.event_log_formatter = logging.Formatter('%(asctime)s %(levelname)s | %(message)s')

        # Configurando o logger
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)  # Define o nível do logger para DEBUG

        # Criação do diretório para logs, se não existir
        os.makedirs(log_dir, exist_ok=True)

        # Configuração do handler para arquivos
        file_handler = logging.FileHandler(os.path.join(log_dir, f"{datetime.now(UTC).strftime('%Y%m%d')}.log"))
        file_handler.setFormatter(self.event_log_formatter)
        file_handler.setLevel(logging.DEBUG)  # Salva todos os logs no arquivo
        self.logger.addHandler(file_handler)

        # Configuração do handler para saída padrão (stdout)
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(self.event_log_formatter)
        stdout_handler.setLevel(logging.INFO)  # Logs INFO e acima para stdout
        self.logger.addHandler(stdout_handler)

        # Configuração do handler para saída de erro (stderr)
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(self.event_log_formatter)
        stderr_handler.setLevel(logging.ERROR)  # Logs ERROR e acima para stderr
        self.logger.addHandler(stderr_handler)

    def log(self, message: str, level: Optional[int] = logging.INFO):
        """
        Registra uma mensagem com um nível específico.

        Args:
            message (str): Mensagem a ser registrada.
            level (int, optional): Nível do log. O padrão é logging.INFO.
        """
        self.logger.log(level, message)

    def save(self, event_id, event_type, event_data, event_issuer, event_signer, user_id):
        """
        Salva os dados do evento no banco de dados.

        Args:
            event_id (str): ID do evento.
            event_type (str): Tipo do evento.
            event_data (dict): Dados do evento.
            event_issuer (str): Emissor do evento.
            event_signer (str): Assinante do evento.
            user_id (str): ID do usuário.

        Returns:
            dict: Dados serializados do evento.

        Raises:
            Exception: Se houver um erro ao salvar o evento.
        """
        try:
            # Serializar e validar dados
            serializer = EventLogSerializer(data={
                'event_id': event_id,
                'event_type': event_type,
                'event_data': event_data,
                'event_issuer': event_issuer,
                'event_signer': event_signer,
                'user_id': user_id,
            })
            serializer.is_valid(raise_exception=True)

            # Salvar o objeto validado
            event_log = serializer.save()
            return serializer.data
        except Exception as e:
            self.log(f"Erro ao salvar o evento: {e}", level=logging.ERROR)
            raise