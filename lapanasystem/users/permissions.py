"""Users permissions."""

# Django
from rest_framework import permissions

# Models
from lapanasystem.users.models import User


class IsAdmin(permissions.BasePermission):
    """Allow access only to admin users."""

    def has_permission(self, request, view):
        """Check if the user is admin."""
        return (
            request.user.is_authenticated and
            (request.user.user_type == User.ADMIN or request.user.is_superuser)
        )


class IsSeller(permissions.BasePermission):
    """Allow access only to seller users."""

    def has_permission(self, request, view):
        """Check if the user is seller."""
        return request.user.is_authenticated and request.user.user_type == User.SELLER


class IsDelivery(permissions.BasePermission):
    """Allow access only to delivery users."""

    def has_permission(self, request, view):
        """Check if the user is delivery."""
        return request.user.is_authenticated and request.user.user_type == User.DELIVERY
