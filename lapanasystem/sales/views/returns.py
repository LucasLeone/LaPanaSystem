"""Return views."""

# Django
from django.core.cache import cache

# Django REST Framework
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet

# Permissions
from rest_framework.permissions import IsAuthenticated
from lapanasystem.users.permissions import IsAdmin, IsDelivery

# Models
from lapanasystem.sales.models import Return

# Serializers
from lapanasystem.sales.serializers import ReturnSerializer

# Filters
from lapanasystem.sales.filters import ReturnFilter


class ReturnViewSet(ModelViewSet):
    """
    Return view set.

    Handles the creation, updating, and deletion of returns.

    Actions:
        - List: Return a list of returns.
        - Retrieve: Return a specific return instance.
        - Create: Create a return with details.
        - Update: Update a return.
        - Partial update: Partially update a return.
        - Destroy: Soft delete a return.

    Filters:
        - Search: Search returns by customer name.
        - Ordering: Order returns by date or total.
        - Filter: Filter returns by user, customer, date, or total.

    Permissions:
        - List: IsAuthenticated, IsDelivery | IsAdmin
        - Retrieve: IsAuthenticated, IsDelivery | IsAdmin
        - Create: IsAuthenticated, IsDelivery | IsAdmin
        - Update: IsAuthenticated, IsDelivery | IsAdmin
        - Partial update: IsAuthenticated, IsDelivery | IsAdmin
        - Destroy: IsAuthenticated, IsDelivery | IsAdmin
    """

    queryset = Return.objects.filter(is_active=True)
    serializer_class = ReturnSerializer
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ["customer__name"]
    filterset_class = ReturnFilter
    ordering_fields = ["date", "total"]

    def get_permissions(self):
        """Assign permissions based on action."""
        permissions = [IsAuthenticated, IsDelivery | IsAdmin]
        return [permission() for permission in permissions]

    def perform_destroy(self, instance):
        """Soft delete the return instance."""
        instance.is_active = False
        instance.save()

    def destroy(self, request, *args, **kwargs):
        """Handle soft delete with a confirmation message."""
        instance = self.get_object()
        self.perform_destroy(instance)
        cache.delete("returns_list")
        cache.delete(f"return_{instance.id}")
        return Response(
            {"message": "Return deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )

    def list(self, request, *args, **kwargs):
        """Cache the return list."""
        cache_key = "returns_list"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=86400)
        return response

    def retrieve(self, request, *args, **kwargs):
        """Cache individual return retrieval."""
        return_id = kwargs.get("pk")
        cache_key = f"return_{return_id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=86400)
        return response

    def create(self, request, *args, **kwargs):
        """Override create to handle caching."""
        response = super().create(request, *args, **kwargs)
        cache.delete("returns_list")
        return response

    def update(self, request, *args, **kwargs):
        """Override update to handle caching."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        cache.delete("returns_list")
        cache.delete(f"return_{instance.id}")

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """Override partial_update to handle caching."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
