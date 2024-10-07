"""Sales views."""

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
from lapanasystem.users.permissions import IsAdmin, IsSeller, IsDelivery

# Models
from lapanasystem.sales.models import Sale, StateChange

# Serializers
from lapanasystem.sales.serializers import SaleSerializer

# Filters
from lapanasystem.sales.filters import SaleFilter

# Utilities
from django.utils import timezone


class SaleViewSet(ModelViewSet):
    """
    Sale view set.

    Handle the creation, updating, and deletion of sales.

    Actions:
        - List: Return a list of sales.
        - Retrieve: Return a sale.
        - Create: Create a sale with or without details.
        - Update: Update a sale.
        - Partial update: Update a sale partially.
        - Destroy: Delete a sale.
        - Cancel: Cancel a sale.
        - Mark as delivered: Mark a sale as delivered.
        - Mark as charged: Mark a sale as charged.

    Filters:
        - Search: Search sales by customer name or seller username.
        - Ordering: Order sales by date or total.
        - Filter: Filter sales by state, customer, or user.

    Permissions:
        - List: IsAuthenticated, IsSeller | IsAdmin
        - Retrieve: IsAuthenticated, IsSeller | IsAdmin
        - Create: IsAuthenticated, IsSeller | IsAdmin
        - Update: IsAuthenticated, IsSeller | IsAdmin
        - Partial update: IsAuthenticated, IsSeller | IsAdmin
        - Destroy: IsAuthenticated, IsSeller | IsAdmin
        - Cancel: IsAuthenticated, IsSeller | IsAdmin
        - Mark as delivered: IsAuthenticated, IsDelivery | IsAdmin
        - Mark as charged: IsAuthenticated, IsDelivery | IsAdmin
    """

    queryset = Sale.objects.filter(is_active=True)
    serializer_class = SaleSerializer
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ["customer__name", "user__username"]
    filterset_class = SaleFilter
    ordering_fields = ["date", "total"]

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
            "cancel",
            "list",
            "retrieve",
        ]:
            permissions = [IsAuthenticated, IsSeller | IsAdmin]
        elif self.action in ["mark_as_delivered", "mark_as_charged"]:
            permissions = [IsAuthenticated, IsDelivery | IsAdmin]
        else:
            permissions = [IsAuthenticated, IsAdmin]
        return [p() for p in permissions]

    def create(self, request, *args, **kwargs):
        """Override create to handle caching."""
        response = super().create(request, *args, **kwargs)
        cache.delete("sales_list")
        return response

    def perform_destroy(self, instance):
        """Disable delete (soft delete)."""
        instance.is_active = False
        instance.save()

    def destroy(self, request, *args, **kwargs):
        """Handle soft delete with confirmation message."""
        instance = self.get_object()
        self.perform_destroy(instance)
        cache.delete("sales_list")
        cache.delete(f"sale_{instance.id}")
        return Response(
            {"message": "Sale deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )

    def list(self, request, *args, **kwargs):
        """Cache the sale list."""
        cache_key = "sales_list"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=86400)
        return response

    def retrieve(self, request, *args, **kwargs):
        """Cache individual sale retrieval."""
        sale_id = kwargs.get("pk")
        cache_key = f"sale_{sale_id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=86400)
        return response

    def perform_update(self, serializer):
        """Handle cache invalidation and actualización al actualizar una venta."""
        instance = serializer.save()
        cache.delete("sales_list")
        cache.delete(f"sale_{instance.id}")
        cache_key = f"sale_{instance.id}"
        data = self.get_serializer(instance).data
        cache.set(cache_key, data, timeout=86400)

    def update(self, request, *args, **kwargs):
        """Override update to handle caching."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """Override partial_update to handle caching."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="mark-as-delivered")
    def mark_as_delivered(self, request, *args, **kwargs):
        """
        Marks a sale as delivered.

        Raises:
            ValidationError: If the sale has no previous state, if the sale has already been canceled,
                if the sale has already been marked as delivered, or if the sale has already been
                marked as paid.

        Returns:
            Response: A response indicating that the sale has been marked as delivered.
        """
        instance = self.get_object()

        last_state_change = instance.state_changes.order_by("-start_date").first()

        if not last_state_change:
            raise ValidationError("La venta no tiene un estado previo.")

        if last_state_change.state == StateChange.CANCELADA:
            raise ValidationError("La venta ya ha sido cancelada.")

        if last_state_change.state == StateChange.ENTREGADA:
            raise ValidationError("La venta ya ha sido marcada como entregada.")

        if last_state_change.state == StateChange.COBRADA:
            raise ValidationError("La venta ya ha sido cobrada.")

        last_state_change.end_date = timezone.now()
        last_state_change.save()

        StateChange.objects.create(sale=instance, state=StateChange.ENTREGADA)

        cache.delete("sales_list")
        cache.delete(f"sale_{instance.id}")

        return Response(
            {"message": "Venta marcada como entregada."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="mark-as-charged")
    def mark_as_charged(self, request, *args, **kwargs):
        """
        Marks a sale as charged.

        Raises:
            ValidationError: If the sale has no previous state, if the sale has already been canceled,
                or if the sale has already been marked as charged.

        Returns:
            Response: A response indicating that the sale has been marked as charged.
        """
        instance = self.get_object()

        last_state_change = instance.state_changes.order_by("-start_date").first()

        if not last_state_change:
            raise ValidationError("La venta no tiene un estado previo.")

        if last_state_change.state == StateChange.CANCELADA:
            raise ValidationError("La venta ya ha sido cancelada.")

        if last_state_change.state == StateChange.COBRADA:
            raise ValidationError("La venta ya ha sido marcada como cobrada.")

        last_state_change.end_date = timezone.now()
        last_state_change.save()

        StateChange.objects.create(sale=instance, state=StateChange.COBRADA)

        cache.delete("sales_list")
        cache.delete(f"sale_{instance.id}")

        return Response(
            {"message": "Venta marcada como cobrada."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, *args, **kwargs):
        """
        Cancels a sale.

        Raises:
            ValidationError: If the sale has no previous state, if the sale has already been canceled,
                or if the sale has already been marked as charged.

        Returns:
            Response: A response indicating that the sale has been canceled.
        """
        instance = self.get_object()

        last_state_change = instance.state_changes.order_by("-start_date").first()

        if not last_state_change:
            raise ValidationError("La venta no tiene un estado previo.")

        if last_state_change.state == StateChange.CANCELADA:
            raise ValidationError("La venta ya ha sido cancelada.")

        if last_state_change.state == StateChange.COBRADA:
            raise ValidationError("No se puede cancelar una venta ya cobrada.")

        last_state_change.end_date = timezone.now()
        last_state_change.save()

        StateChange.objects.create(sale=instance, state=StateChange.CANCELADA)

        cache.delete("sales_list")
        cache.delete(f"sale_{instance.id}")

        return Response(
            {"message": "Venta marcada como cancelada."},
            status=status.HTTP_200_OK,
        )
