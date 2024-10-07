"""Suppliers views."""

# Django
from django.core.cache import cache

# Django REST Framework
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

# Models
from lapanasystem.expenses.models import Supplier

# Serializers
from lapanasystem.expenses.serializers import SupplierSerializer

# Permissions
from lapanasystem.users.permissions import IsAdmin, IsSeller
from rest_framework.permissions import IsAuthenticated

# Filters
from rest_framework.filters import OrderingFilter, SearchFilter


class SupplierViewSet(ModelViewSet):
    """Supplier view set.

    Handle create, update, retrieve, list, and soft delete suppliers.

    Actions:
        - create: Create a new supplier.
        - retrieve: Return a supplier's details.
        - list: Return a list of suppliers.
        - update: Update a supplier's details.
        - destroy: Soft delete a supplier.

    Filters:
        - search: Search suppliers by name, email or phone_number.
        - ordering: Order suppliers by name, email or phone_number.

    Permissions:
        - create: IsAuthenticated, IsAdmin | IsSeller
        - retrieve: IsAuthenticated, IsAdmin | IsSeller
        - list: IsAuthenticated, IsAdmin | IsSeller
        - update: IsAuthenticated, IsAdmin | IsSeller
        - partial_update: IsAuthenticated, IsAdmin | IsSeller
        - destroy: IsAuthenticated, IsAdmin
    """

    queryset = Supplier.objects.filter(is_active=True)
    serializer_class = SupplierSerializer
    lookup_field = "id"
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "email", "phone_number"]
    ordering_fields = ["name", "email", "phone_number"]

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
        cache.delete("suppliers_list")
        cache.delete(f"supplier_{instance.id}")
        return Response(
            data={"message": "Supplier deleted successfully."},
            status=status.HTTP_200_OK
        )

    def list(self, request, *args, **kwargs):
        """Cache the supplier list."""
        cache_key = "suppliers_list"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=86400)
        return response

    def retrieve(self, request, *args, **kwargs):
        """Cache individual supplier retrieval."""
        supplier_id = kwargs.get("id")
        cache_key = f"supplier_{supplier_id}"
        cached_data = cache.get(cache_key)

        if (cached_data):
            return Response(cached_data, status=status.HTTP_200_OK)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=86400)
        return response

    def create(self, request, *args, **kwargs):
        """Override create to handle caching."""
        response = super().create(request, *args, **kwargs)
        cache.delete("suppliers_list")
        return response

    def update(self, request, *args, **kwargs):
        """Override update to handle caching."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        cache.delete("suppliers_list")
        cache.delete(f"supplier_{instance.id}")

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """Override partial_update to handle caching."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
