from django.apps import AppConfig


class ChildrenConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'children'

    def ready(self):
        from . import signals