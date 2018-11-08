from django.apps import AppConfig


class TLabelBackendConfig(AppConfig):
    name = 'tlabel_backend'

    def ready(self):
        import tlabel_backend.startup

        tlabel_backend.startup.start()
