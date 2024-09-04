"""Expenses views."""

# Django REST Framework
from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets

# Permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from lapanasystem.expenses.models import Category

# Models
from lapanasystem.expenses.models import Expense
from lapanasystem.expenses.serializers import CategorySerializer

# Serializers
from lapanasystem.expenses.serializers import ExpenseSerializer

# Permissions
from lapanasystem.users.permissions import IsAdmin
from lapanasystem.users.permissions import IsSeller


class ExpenseViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Expense view set.

    Handle create, update, retrieve and list expenses.
    """

    serializer_class = ExpenseSerializer
    lookup_field = "id"

    def get_queryset(self):
        """Return only active expenses."""
        return Expense.objects.filter(is_active=True)

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


class CategoryViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Category view set.

    Handle create, update, retrieve and list categories.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "id"

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action in ["create", "retrieve", "list", "update"]:
            permissions = [IsAuthenticated, IsAdmin | IsSeller]
        else:
            permissions = [IsAuthenticated, IsAdmin]
        return [permission() for permission in permissions]
