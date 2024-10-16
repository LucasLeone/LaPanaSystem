"""Returns model."""

# Django
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

# Utilities
from lapanasystem.utils.models import LPSModel
from decimal import Decimal


class Return(LPSModel):
    """Return model."""

    user = models.ForeignKey("users.User", on_delete=models.RESTRICT)
    customer = models.ForeignKey("customers.Customer", on_delete=models.RESTRICT)
    sale = models.ForeignKey("sales.Sale", on_delete=models.RESTRICT)
    date = models.DateTimeField(default=timezone.now)
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        blank=True,
        null=True,
    )

    def __str__(self):
        """Return customer and date."""
        return f"{self.customer} - {self.date}"

    def calculate_total(self):
        """Calculate total."""
        total = sum(
            [detail.price * detail.quantity for detail in self.return_details.all()]
        )
        self.total = total
        self.save()


class ReturnDetail(LPSModel):
    """Return detail model."""

    return_order = models.ForeignKey("Return", on_delete=models.CASCADE, related_name="return_details")
    product = models.ForeignKey("products.Product", on_delete=models.RESTRICT)
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        editable=False,
    )

    def __str__(self):
        """Return return_order and product.."""
        return f"{self.return_order} - {self.product}"

    def get_subtotal(self):
        """Calculate subtotal."""
        return self.price * self.quantity
