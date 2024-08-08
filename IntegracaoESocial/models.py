from django.db import models

# Create your models here.

class EventLog(models.Model):
    event_id = models.CharField(max_length=36, unique=True)
    event_type = models.CharField(max_length=255)
    event_data = models.JSONField() # Armazena os dados do evento
    event_issuer = models.CharField(max_length=14) # CNPJ/CPF do emissor do evento (Empregador)
    event_signer = models.CharField(max_length=14) # CNPJ/CPF do assinante do evento (Dono do certificado digital)
    status_code = models.IntegerField(null=True) # Código de resposta do processo de recepção
    status_description = models.CharField(max_length=255, null=True) # Descrição do código de resposta
    user_id = models.IntegerField() # Armazena o ID do usuário
    created_at = models.DateTimeField(auto_now_add=True) # Data e hora de criação
    updated_at = models.DateTimeField(auto_now=True) # Data e hora da última atualização

    def __str__(self):
        return f"Event {self.event_id} of type {self.event_type} status {self.status_code} | From: {self.event_issuer} - Signed by: {self.event_signer}"
    
    class Meta:
        db_table = 'event_log'