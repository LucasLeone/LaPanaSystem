"""Standing orders models."""

# Django
from django.db import models

# Models
from lapanasystem.customers.models import Customer
from lapanasystem.products.models import Product

# Utilities
from lapanasystem.utils.models import LPSModel


class StandingOrder(LPSModel):
    """Standing order model."""

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    DAY_OF_WEEK_CHOICES = [
        (MONDAY, 'Lunes'),
        (TUESDAY, 'Martes'),
        (WEDNESDAY, 'Miércoles'),
        (THURSDAY, 'Jueves'),
        (FRIDAY, 'Viernes'),
        (SATURDAY, 'Sábado'),
        (SUNDAY, 'Domingo'),
    ]

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='standing_orders'
    )
    day_of_week = models.IntegerField(choices=DAY_OF_WEEK_CHOICES)

    class Meta:
        unique_together = ('customer', 'day_of_week')

    def __str__(self):
        return f"{self.customer.name} - {self.get_day_of_week_display()}"


class StandingOrderDetail(LPSModel):
    """Standing order detail model."""

    standing_order = models.ForeignKey(
        StandingOrder, on_delete=models.CASCADE, related_name='details'
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"
