from django.apps import AppConfig


class ProcessCreatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'process_creator'
    verbose_name = 'Process Creator'

    def ready(self):
        # Import signals
        from . import signals  # noqa: F401