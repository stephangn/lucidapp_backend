from django.apps import AppConfig


class BackendTradechainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lucidapp'

    def ready(self):
        import lucidapp.signals  # noqa