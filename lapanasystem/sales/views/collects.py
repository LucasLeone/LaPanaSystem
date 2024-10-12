"""Collects views."""

# Django REST Framework
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

# Models
from lapanasystem.sales.models import Collect

# Serializers
from lapanasystem.sales.serializers import CollectSerializer
from lapanasystem.users.permissions import IsAdmin

# Permissions
from rest_framework.permissions import IsAuthenticated

# Filters
from lapanasystem.sales.filters import CollectFilter


class CollectViewSet(ModelViewSet):
    """Collect view set."""

    queryset = Collect.objects.filter(is_active=True)
    serializer_class = CollectSerializer
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    filterset_class = CollectFilter
    ordering_fields = ["date", "total"]
    ordering = ["-created"]

    def get_permission(self):
        """Assign permissions based on action."""
        if self.action in [
            "create",
            "update",
            "partial_update",
            "list",
            "retrieve",
        ]:
            permissions = [IsAuthenticated,]
        elif self.action in ["destroy"]:
            permissions = [IsAuthenticated, IsAdmin]
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
            {"message": "Collect deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )
