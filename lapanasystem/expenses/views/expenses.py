"""Expenses views."""

# Django
from django.core.cache import cache

# Django REST Framework
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

# Models
from lapanasystem.expenses.models import Expense, ExpenseCategory

# Serializers
from lapanasystem.expenses.serializers import CategorySerializer, ExpenseSerializer

# Permissions
from lapanasystem.users.permissions import IsAdmin, IsSeller
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
        # Invalidate related caches
        cache.delete("expenses_list")
        cache.delete(f"expense_{instance.id}")
        return Response(
            data={"message": "Expense deleted successfully."},
            status=status.HTTP_200_OK,
        )

    def list(self, request, *args, **kwargs):
        """Cache the expense list."""
        cache_key = "expenses_list"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=86400)
        return response

    def retrieve(self, request, *args, **kwargs):
        """Cache individual expense retrieval."""
        expense_id = kwargs.get("id")
        cache_key = f"expense_{expense_id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=86400)
        return response

    def create(self, request, *args, **kwargs):
        """Override create to handle caching."""
        response = super().create(request, *args, **kwargs)
        cache.delete("expenses_list")
        return response

    def update(self, request, *args, **kwargs):
        """Override update to handle caching."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        cache.delete("expenses_list")
        cache.delete(f"expense_{instance.id}")

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """Override partial_update to handle caching."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


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
        cache.delete("categories_list")
        cache.delete(f"category_{instance.id}")
        return Response(
            data={"message": "Category deleted successfully."},
            status=status.HTTP_200_OK,
        )

    def list(self, request, *args, **kwargs):
        """Cache the category list."""
        cache_key = "categories_list"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=86400)
        return response

    def retrieve(self, request, *args, **kwargs):
        """Cache individual category retrieval."""
        category_id = kwargs.get("id")
        cache_key = f"category_{category_id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=86400)
        return response

    def create(self, request, *args, **kwargs):
        """Override create to handle caching."""
        response = super().create(request, *args, **kwargs)
        cache.delete("categories_list")
        return response

    def update(self, request, *args, **kwargs):
        """Override update to handle caching."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        cache.delete("categories_list")
        cache.delete(f"category_{instance.id}")

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """Override partial_update to handle caching."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
