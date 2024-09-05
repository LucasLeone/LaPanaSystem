"""Users and UserType models."""

# Django
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

# Utilities
from lapanasystem.utils.models import LPSModel


class UserType(LPSModel):
    """UserType model.

    Defines the types of users and associated permissions.
    """

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class User(LPSModel, AbstractUser):
    """User model.

    Extend from Django's Abstract User and link to UserType.
    """

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

    user_type = models.ForeignKey(
        UserType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
