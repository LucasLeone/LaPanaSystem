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
    email = models.EmailField('Correo electrónico', unique=True)
    phone_regex = RegexValidator(
        regex=r"\+?1?\d{9,15}$",
        message=(
            "Phone number must be entered in the format: +999999999. "
            "Up to 15 digits allowed."
        ),
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    address = models.CharField('Dirección', max_length=255, blank=True)
    customer_type = models.CharField(
        'Tipo de cliente',
        max_length=10,
        choices=CUSTOMER_TYPE_CHOICES,
        default=MINORISTA
    )

    def __str__(self):
        return f'{self.name}'
