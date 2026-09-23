from django.apps import AppConfig


class AlertsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alerts'

    def ready(self):
        try:
            import alerts.signals  # noqa: F401
        except ImportError:
            pass
