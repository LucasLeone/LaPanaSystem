"""Expenses models."""

# Django
from django.db import models
from django.utils import timezone

# Utilities
from lapanasystem.utils.models import LPSModel


class ExpenseCategory(LPSModel):
    """Expense category model."""

    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        """Return name."""
        return self.name

    class Meta:
        """Meta options."""

        verbose_name = "Expense Category"
        verbose_name_plural = "Expense Categories"


class Expense(LPSModel):
    """Expense model."""

    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255)
    category = models.ForeignKey(
        ExpenseCategory,
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

    def __str__(self):
        """Return a string representation of the expense."""
        return f"Expense {self.id}: {self.amount} by {self.user.username}"
