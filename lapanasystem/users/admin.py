"""Users admin."""

# Django
from django.contrib import admin

# Models
from lapanasystem.users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """User admin."""

    list_display = (
        "pk",
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
    )
    search_fields = ("username", "email", "first_name", "last_name")
    list_display_links = ("pk", "username")
    list_filter = ("is_staff", "is_active", "created", "modified")
    list_editable = ["is_active",]
