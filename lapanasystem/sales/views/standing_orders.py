"""Standing order views."""

# Django REST Framework
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

# Models
from lapanasystem.sales.models import StandingOrder

# Serializers
from lapanasystem.sales.serializers import StandingOrderSerializer


class StandingOrderViewSet(ModelViewSet):
    """Standing order view set."""

    queryset = StandingOrder.objects.all()
    serializer_class = StandingOrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['customer',]
