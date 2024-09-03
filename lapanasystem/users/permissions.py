"""Users permissions."""

# Django
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Allow access only to admin users."""

    def has_permission(self, request, view):
        """Check if the user is admin."""
        return (
            request.user.user_type
            and request.user.user_type.name == "Administrador"
            or request.user.is_superuser
        )


class IsSeller(permissions.BasePermission):
    """Allow access only to seller users."""

    def has_permission(self, request, view):
        """Check if the user is seller."""
        return request.user.user_type and request.user.user_type.name == "Vendedor"


class IsDelivery(permissions.BasePermission):
    """Allow access only to delivery users."""

    def has_permission(self, request, view):
        """Check if the user is delivery."""
        return request.user.user_type and request.user.user_type.name == "Repartidor"
