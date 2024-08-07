from IntegracaoESocial.serializers import EventLogSerializer
from IntegracaoESocial.models import EventLog

class EventLogService:
    def __init__(self):
        pass

    def get_next_event_id(self):
        last_event = EventLog.objects.all().order_by('event_id').last()
        if last_event:
            last_id = int(last_event.event_id)
            new_id = '{:0>20d}'.format(last_id + 1)
        else:
            new_id = '00000000000000000001'
        
        return new_id

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