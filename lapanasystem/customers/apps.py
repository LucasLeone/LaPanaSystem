import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CustomersConfig(AppConfig):
    name = "lapanasystem.customers"
    verbose_name = _("Customers")

    def ready(self):
        with contextlib.suppress(ImportError):
            import lapanasystem.customers.signals  # noqa: F401
