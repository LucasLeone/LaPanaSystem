"""Collects models."""

# Django
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

# Utilities
from lapanasystem.utils.models import LPSModel
from decimal import Decimal


class Collect(LPSModel):
    """Collect model."""

    user = models.ForeignKey("users.User", on_delete=models.RESTRICT)
    customer = models.ForeignKey("customers.Customer", on_delete=models.RESTRICT)
    date = models.DateTimeField(default=timezone.now)
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    def __str__(self):
        """Return collect."""
        return f"{self.customer} - {self.date} - {self.total}"
