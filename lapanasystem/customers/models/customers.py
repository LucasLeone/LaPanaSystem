"""Customer models."""

# Django
from django.db import models
from django.core.validators import RegexValidator

# Models
from lapanasystem.utils.models import LPSModel


class Customer(LPSModel):
    """
    Customer model.

    A customer is a person or company that buys products from the store.

    Attributes:
    - name (str): Customer's name.
    - email (str): Customer's email address.
    - phone_number (str): Customer's phone number.
    - address (str): Customer's address.
    - customer_type (str): Customer's type (minorista or mayorista).
    """

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
            "Phone number must be entered in the format: +999999999. "
            "Up to 15 digits allowed."
        ),
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    address = models.CharField('Dirección', max_length=255, blank=True, null=True)
    customer_type = models.CharField(
        'Tipo de cliente',
        max_length=10,
        choices=CUSTOMER_TYPE_CHOICES,
        default=MINORISTA
    )

    def __str__(self):
        """Return name and email."""
        return f'{self.name} - ({self.customer_type})'

    def save(self, *args, **kwargs):
        """
        Save method override to normalize the email to lowercase.

        This ensures that email uniqueness checks are case-insensitive.
        """
        self.email = self.email.lower() if self.email else None
        super().save(*args, **kwargs)
