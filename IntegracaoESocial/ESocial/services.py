from IntegracaoESocial.serializers import EventLogSerializer
from IntegracaoESocial.models import EventLog

class EventLogService:
    def __init__(self):
        pass

    def log_event(self, event_id, event_type, event_data, event_issuer, event_signer, user_id):
        event_id = self.get_next_event_id()

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