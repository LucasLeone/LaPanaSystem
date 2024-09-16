"""Users models."""

# Django
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

# Utilities
from lapanasystem.utils.models import LPSModel


class User(LPSModel, AbstractUser):
    """User model.

    Extend from Django's Abstract User.
    """

    ADMIN = "ADMIN"
    SELLER = "SELLER"
    DELIVERY = "DELIVERY"
    USER_TYPE_CHOICES = [
        (ADMIN, "Admin"),
        (SELLER, "Seller"),
        (DELIVERY, "Delivery"),
    ]

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    email = models.EmailField(
        "email address",
        unique=True,
        error_messages={
            "unique": "A user with that email already exists.",
        },
    )

    phone_regex = RegexValidator(
        regex=r"\+?1?\d{9,15}$",
        message=(
            "Phone number must be entered in the format: +999999999. "
            "Up to 15 digits allowed."
        ),
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17)

    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default=SELLER,
    )
