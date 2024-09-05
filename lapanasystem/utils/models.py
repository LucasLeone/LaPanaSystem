"""Django models utilities."""

# Django
from django.db import models


class LPSModel(models.Model):
    """LaPanaSystem base model.

    LPSModel acts as an abstract base class from which every
    other model in the project will inherit. This class provides
    every table with the following attributes:
        + created (DateTime): Store the datetime the object was created.
        + modified (DateTime): Store the last datetime the object was modified.
        + is_active (Boolean): Store the state of the object.
    """

    created = models.DateTimeField(
        "created at",
        auto_now_add=True,
        help_text="Date time on which the object was created.",
    )
    modified = models.DateTimeField(
        "modified at",
        auto_now=True,
        help_text="Date time on which the object was last modified.",
    )
    is_active = models.BooleanField(
        "active",
        default=True,
        help_text="Set to False if you want to deactivate this record.",
    )

    class Meta:
        """Meta option."""

        abstract = True

        get_latest_by = "created"
        ordering = ["-created", "-modified", "-is_active"]
