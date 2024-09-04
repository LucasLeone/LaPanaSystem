"""Supplier models."""

# Django
from django.core.validators import RegexValidator
from django.db import models

# Utilities
from lapanasystem.utils.models import LPSModel


class Supplier(LPSModel):
    """Supplier model."""

    name = models.CharField(max_length=50)
    phone_regex = RegexValidator(
        regex=r"\+?1?\d{9,15}$",
        message=(
            "Phone number must be entered in the format: +999999999. "
            "Up to 15 digits allowed."
        ),
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17)
    email = models.EmailField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        """Return name."""
        return self.name
