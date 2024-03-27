from django.apps import AppConfig


class HumanAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'human_app'

    def ready(self):
        import human_app.signals
