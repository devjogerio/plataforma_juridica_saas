from django.apps import AppConfig


class AlertasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alertas'
    verbose_name = 'Sistema de Alertas'
    
    def ready(self):
        """Carrega os signals quando o app estiver pronto"""
        try:
            import alertas.signals
        except ImportError:
            pass