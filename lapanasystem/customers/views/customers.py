"""Customers views."""

# Django
from django.core.cache import cache

# Django REST Framework
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

# Models
from lapanasystem.customers.models import Customer

# Serializers
from lapanasystem.customers.serializers import CustomerSerializer

# Permissions
from lapanasystem.users.permissions import IsAdmin
from lapanasystem.users.permissions import IsSeller
from rest_framework.permissions import IsAuthenticated

# Filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter


class CustomerViewSet(ModelViewSet):
    """Customer view set.

    Handle create, update, retrieve, list, and soft delete customers.

    Actions:
        - create: Create a new customer.
        - retrieve: Return a customer's details.
        - list: Return a list of customers.
        - update: Update a customer's details.
        - destroy: Soft delete a customer.

    Filters:
        - search: Search customers by name or email.
        - ordering: Order customers by name or email.
        - customer_type: Filter customers by type.

    Permissions:
        - create: IsAuthenticated, IsAdmin | IsSeller
        - retrieve: IsAuthenticated, IsAdmin | IsSeller
        - list: IsAuthenticated, IsAdmin | IsSeller
        - update: IsAuthenticated, IsAdmin | IsSeller
        - partial_update: IsAuthenticated, IsAdmin | IsSeller
        - destroy: IsAuthenticated, IsAdmin
    """

    queryset = Customer.objects.filter(is_active=True)
    serializer_class = CustomerSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["customer_type",]
    ordering_fields = ["id", "name", "email", "created"]
    ordering = ["-created"]
    search_fields = ["name", "email"]

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
        cache.delete(f"customer_{instance.id}")
        return Response(
            data={"message": "Customer deleted successfully."},
            status=status.HTTP_200_OK,
        )

    def list(self, request, *args, **kwargs):
        """Cache the customer list."""
        cache_key = "customers_list"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=86400)
        return response

    def retrieve(self, request, *args, **kwargs):
        """Cache individual customer retrieval."""
        customer_id = kwargs.get("pk")
        cache_key = f"customer_{customer_id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=86400)
        return response
