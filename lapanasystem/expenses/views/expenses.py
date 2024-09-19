"""Expenses views."""

# Django REST Framework
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

# Models
from lapanasystem.expenses.models import Expense
from lapanasystem.expenses.models import ExpenseCategory

# Serializers
from lapanasystem.expenses.serializers import CategorySerializer
from lapanasystem.expenses.serializers import ExpenseSerializer

# Permissions
from lapanasystem.users.permissions import IsAdmin
from lapanasystem.users.permissions import IsSeller
from rest_framework.permissions import IsAuthenticated

# Filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter


class ExpenseViewSet(ModelViewSet):
    """Expense view set.

    Handle create, update, retrieve and list expenses.

    Actions:
        - create: Create a new expense.
        - retrieve: Return an expense's details.
        - list: Return a list of expenses.
        - update: Update an expense's details.
        - destroy: Soft delete an expense.

    Filters:
        - search: Search expenses by description.
        - ordering: Order expenses by amount.
        - category: Filter expenses by category.

    Permissions:
        - create: IsAuthenticated, IsAdmin | IsSeller
        - retrieve: IsAuthenticated, IsAdmin | IsSeller
        - list: IsAuthenticated, IsAdmin | IsSeller
        - update: IsAuthenticated, IsAdmin | IsSeller
        - partial_update: IsAuthenticated, IsAdmin | IsSeller
        - destroy: IsAuthenticated, IsAdmin
    """

    queryset = Expense.objects.filter(is_active=True)
    serializer_class = ExpenseSerializer
    lookup_field = "id"
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ["description"]
    ordering_fields = ["amount"]
    filterset_fields = ["category"]

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action in ["create", "retrieve", "list", "update", "partial_update"]:
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
            data={"message": "Expense deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )


class CategoryViewSet(ModelViewSet):
    """Category view set.

    Handle create, update, retrieve and list categories.

    Actions:
        - create: Create a new category.
        - retrieve: Return a category's details.
        - list: Return a list of categories.
        - update: Update a category's details.
        - destroy: Soft delete a category.
    """

    queryset = ExpenseCategory.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = "id"

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action in ["create", "retrieve", "list", "update", "partial_update"]:
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
            data={"message": "Category deleted successfully."},
            status=status.HTTP_200_OK,
        )
