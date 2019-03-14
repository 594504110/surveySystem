from django.apps import AppConfig

from django.utils.module_loading import import_module


class WebConfig(AppConfig):
    name = 'web'

    def ready(self):
        import_module("web.signals.survey")
