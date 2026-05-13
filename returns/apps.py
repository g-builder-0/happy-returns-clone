from django.apps import AppConfig


class ReturnsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'returns'

    def ready(self):
        """Import signals when Django starts"""
        import returns.signals  # This registers the signal handlers