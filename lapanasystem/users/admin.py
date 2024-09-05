"""Users admin."""

# Django
from django.contrib import admin

# Models
from lapanasystem.users.models import User
from lapanasystem.users.models import UserType


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


@admin.register(UserType)
class UserTypeAdmin(admin.ModelAdmin):
    """UserType admin."""

    list_display = ("pk", "name", "description", "is_active")
    list_display_links = ("pk", "name")
    search_fields = ("name", "description")
    list_filter = ("name", "description")
    actions = ["assign_permissions"]
    list_editable = ["is_active",]

    @admin.action(
        description="Assign permissions",
    )
    def assign_permissions(self, request, queryset):
        """Assign permissions to a group based on the user type."""
        for user_type in queryset:
            user_type.assign_permissions()
        self.message_user(request, "Permissions assigned successfully.")
