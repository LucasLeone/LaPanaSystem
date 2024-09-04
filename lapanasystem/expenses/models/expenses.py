"""Expenses models."""

# Django
from django.db import models
from django.utils import timezone

# Utilities
from lapanasystem.utils.models import LPSModel


class Category(LPSModel):
    """Expense category model."""

    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        """Return name."""
        return self.name


class Expense(LPSModel):
    """Expense model."""

    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    description = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="expenses",
        null=True,
        blank=True,
    )
    supplier = models.ForeignKey(
        "expenses.Supplier",
        on_delete=models.SET_NULL,
        related_name="expenses",
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        """Return title and username."""
        return f"{self.description} - {self.user.username} - ${self.amount}"
