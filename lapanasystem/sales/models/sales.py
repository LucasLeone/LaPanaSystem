"""Sales models."""

# Django
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

# Utilities
from lapanasystem.utils.models import LPSModel
from decimal import Decimal


class Sale(LPSModel):
    """Sale model."""

    MINORISTA = "minorista"
    MAYORISTA = "mayorista"

    CUSTOMER_TYPE_CHOICES = [(MINORISTA, "Minorista"), (MAYORISTA, "Mayorista")]

    EFECTIVO = "efectivo"
    TARJETA = "tarjeta"
    TRANSFERENCIA = "transferencia"
    QR = "qr"
    CUENTA_CORRIENTE = "cuenta_corriente"

    SALE_PAYMENT_METHOD_CHOICES = [
        (EFECTIVO, "Efectivo"),
        (TARJETA, "Tarjeta"),
        (TRANSFERENCIA, "Transferencia"),
        (QR, "QR"),
        (CUENTA_CORRIENTE, "Cuenta Corriente"),
    ]

    user = models.ForeignKey("users.User", on_delete=models.RESTRICT)
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.RESTRICT, blank=True, null=True
    )
    date = models.DateTimeField(blank=True, null=True)
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        blank=True,
        null=True,
    )
    sale_type = models.CharField(
        max_length=10, choices=CUSTOMER_TYPE_CHOICES, default=MINORISTA
    )
    payment_method = models.CharField(
        max_length=16, choices=SALE_PAYMENT_METHOD_CHOICES, default=EFECTIVO
    )
    needs_delivery = models.BooleanField(default=False)

    def __str__(self):
        """Return sale."""
        return f"{self.customer} - {self.total}"

    def calculate_total(self):
        """Calculate total."""
        total = sum(
            [detail.price * detail.quantity for detail in self.sale_details.all()]
        )
        self.total = total
        self.save()

    def get_state(self):
        """Return the last state of the sale based on start_date."""
        last_state_change = self.state_changes.order_by("-start_date").first()
        return last_state_change.state if last_state_change else None

    def save(self, *args, **kwargs):
        """Calculate total automatically."""
        if not self.date:
            self.date = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        """Meta options."""

        constraints = [
            models.UniqueConstraint(fields=['sale', 'product'], name='unique_sale_product')
        ]


class SaleDetail(LPSModel):
    """Sale detail model."""

    sale = models.ForeignKey(
        "Sale", on_delete=models.CASCADE, related_name="sale_details"
    )
    product = models.ForeignKey("products.Product", on_delete=models.RESTRICT)
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        editable=False,
    )

    def __str__(self):
        """Return sale and product.."""
        return f"{self.sale} - {self.product}"

    def get_subtotal(self):
        """Calculate subtotal."""
        return self.price * self.quantity


class StateChange(LPSModel):
    """Model to record the state changes of a wholesale sale."""

    CREADA = "creada"
    PENDIENTE_ENTREGA = "pendiente_entrega"
    ENTREGADA = "entregada"
    COBRADA = "cobrada"
    CANCELADA = "cancelada"

    STATE_CHOICES = [
        (CREADA, "Creada"),
        (PENDIENTE_ENTREGA, "Pendiente de Entrega"),
        (ENTREGADA, "Entregada"),
        (COBRADA, "Cobrada"),
        (CANCELADA, "Cancelada"),
    ]

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        verbose_name="Sale",
        related_name="state_changes",
    )
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default=CREADA)
    start_date = models.DateTimeField("Start date", auto_now_add=True)
    end_date = models.DateTimeField("End date", blank=True, null=True)

    def __str__(self):
        """Return state change."""
        return f"{self.get_state_display()} - Sale ID: {self.sale.id}"
