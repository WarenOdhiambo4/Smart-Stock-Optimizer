from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Register finance auto-posting signals.
        from . import signals_finance  # noqa: F401
        # Register fulfillment/payment and audit signals.
        from . import signals_operations  # noqa: F401
