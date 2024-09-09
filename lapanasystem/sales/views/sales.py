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
    """Sale view set."""

    queryset = Sale.objects.filter(is_active=True)
    serializer_class = SaleSerializer
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ["customer__name", "user__username"]
    filterset_class = SaleFilter
    ordering_fields = ["date", "total"]

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action in ["update", "partial_update", "destroy", "cancel", "list"]:
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
        """Mark the sale as delivered and update state change."""
        instance = self.get_object()

        last_state_change = instance.state_changes.order_by("-start_date").first()

        if not last_state_change or last_state_change.state == StateChange.CANCELADA:
            raise ValidationError("The sale is already canceled.")

        if (
            not last_state_change
            or last_state_change.state == StateChange.ENTREGADA
            or last_state_change.state == StateChange.COBRADA
        ):
            raise ValidationError(
                "The sale has been marked as delivered or is already charged."
            )

        last_state_change.end_date = timezone.now()
        last_state_change.save()

        StateChange.objects.create(sale=instance, state=StateChange.ENTREGADA)

        return Response(
            {"message": "Sale marked as delivered."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="mark-as-charged")
    def mark_as_charged(self, request, *args, **kwargs):
        """Mark the sale as charged and update state change."""
        instance = self.get_object()

        last_state_change = instance.state_changes.order_by("-start_date").first()

        if not last_state_change or last_state_change.state == StateChange.CANCELADA:
            raise ValidationError("The sale is already canceled.")

        if not last_state_change or last_state_change.state == StateChange.COBRADA:
            raise ValidationError(
                "The sale has been marked as charged or is already canceled."
            )

        last_state_change.end_date = timezone.now()
        last_state_change.save()

        StateChange.objects.create(sale=instance, state=StateChange.COBRADA)

        return Response(
            {"message": "Sale marked as charged."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, *args, **kwargs):
        """Cancel the sale and update state change."""
        instance = self.get_object()

        last_state_change = instance.state_changes.order_by("-start_date").first()

        if not last_state_change or last_state_change.state == StateChange.CANCELADA:
            raise ValidationError("The sale is already canceled.")

        if not last_state_change or last_state_change.state == StateChange.COBRADA:
            raise ValidationError("The sale has been marked as charged.")

        last_state_change.end_date = timezone.now()
        last_state_change.save()

        StateChange.objects.create(sale=instance, state=StateChange.CANCELADA)

        return Response(
            {"message": "Sale marked as canceled."},
            status=status.HTTP_200_OK,
        )
