"""Suppliers views."""

# Django REST Framework
from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response

# Models
from lapanasystem.expenses.models import Supplier

# Serializers
from lapanasystem.expenses.serializers import SupplierSerializer

# Permissions
from lapanasystem.users.permissions import IsAdmin
from lapanasystem.users.permissions import IsSeller
from rest_framework.permissions import IsAuthenticated


class SupplierViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Supplier view set.

    Handle create, update, retrieve, list, and soft delete suppliers.
    """

    serializer_class = SupplierSerializer
    lookup_field = "id"

    def get_queryset(self):
        """Return only active suppliers."""
        return Supplier.objects.filter(is_active=True)

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action in ["create", "retrieve", "list", "update"]:
            permissions = [IsAuthenticated, IsAdmin | IsSeller]
        else:
            permissions = [IsAuthenticated, IsAdmin]
        return [permission() for permission in permissions]

    def perform_destroy(self, instance):
        """Disable delete (soft delete)."""
        instance.is_active = False
        instance.save()

    def destroy(self, request, *args, **kwargs):
        """Handle soft delete with confirmation message."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            data={"message": "Supplier deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )
