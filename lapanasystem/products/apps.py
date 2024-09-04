import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ProductsConfig(AppConfig):
    name = "lapanasystem.products"
    verbose_name = _("Products")

    def ready(self):
        with contextlib.suppress(ImportError):
            import lapanasystem.products.signals  # noqa: F401
