"""Sales views."""

# Django REST Framework
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.exceptions import ValidationError

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


class SaleViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Sale view set.

    Handle the creation, updating, and deletion of sales.

    Actions:
        - List: Return a list of sales.
        - Retrieve: Return a sale.
        - Create: Create a sale.
        - Update: Update a sale.
        - Partial update: Update a sale partially.
        - Destroy: Delete a sale.
        - Cancel: Cancel a sale.
        - Mark as delivered: Mark a sale as delivered.
        - Mark as charged: Mark a sale as charged.
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
        ]:
            permissions = [IsAuthenticated, IsSeller | IsAdmin]
        elif self.action in ["mark_as_delivered", "mark_as_charged"]:
            permissions = [IsAuthenticated, IsDelivery | IsAdmin]
        else:
            permissions = [IsAuthenticated, IsAdmin]
        return [p() for p in permissions]

    def perform_destroy(self, instance):
        """Disable delete (soft delete)."""
        instance.is_active = False
        instance.save()

    def destroy(self, request, *args, **kwargs):
        """Handle soft delete with confirmation message."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Sale deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )

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

        return Response(
            {"message": "Venta marcada como cancelada."},
            status=status.HTTP_200_OK,
        )
