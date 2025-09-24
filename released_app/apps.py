from django.apps import AppConfig


class ReleasedAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'released_app'
    verbose_name = 'Released App'


