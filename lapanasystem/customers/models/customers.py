"""Customer models."""

# Django
from django.db import models
from django.core.validators import RegexValidator

# Models
from lapanasystem.utils.models import LPSModel


class Customer(LPSModel):
    """Customer model."""

    MINORISTA = 'minorista'
    MAYORISTA = 'mayorista'

    CUSTOMER_TYPE_CHOICES = [
        (MINORISTA, 'Minorista'),
        (MAYORISTA, 'Mayorista'),
    ]

    name = models.CharField('Nombre', max_length=100)
    email = models.EmailField('Correo electrónico', unique=True, null=True, blank=True)
    phone_regex = RegexValidator(
        regex=r"\+?1?\d{9,15}$",
        message=(
            "El número de teléfono debe tener el formato: +999999999. "
            "Hasta 15 dígitos permitidos."
        ),
    )
    phone_number = models.CharField(
        validators=[phone_regex], max_length=17, blank=True, null=True
    )
    address = models.CharField('Dirección', max_length=255, blank=True, null=True)
    customer_type = models.CharField(
        'Tipo de cliente',
        max_length=10,
        choices=CUSTOMER_TYPE_CHOICES,
        default=MINORISTA
    )

    def __str__(self):
        """Return name and customer type."""
        return f'{self.name} - ({self.customer_type})'

    def save(self, *args, **kwargs):
        """
        Save method override to normalize the email to lowercase.

        This ensures that email uniqueness checks are case-insensitive.
        """
        self.email = self.email.lower() if self.email else None
        super().save(*args, **kwargs)
