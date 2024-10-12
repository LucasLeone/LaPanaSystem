"""Collects serializers."""

# Django REST Framework
from rest_framework import serializers

# Models
from lapanasystem.sales.models import Collect
from lapanasystem.customers.models import Customer

# Serializers
from lapanasystem.users.serializers import UserSerializer
from lapanasystem.customers.serializers import CustomerSerializer


class CollectSerializer(serializers.ModelSerializer):
    """Collect model serializer."""

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    user_details = UserSerializer(source="user", read_only=True)
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        write_only=True,
    )
    customer_details = CustomerSerializer(source="customer", read_only=True)

    class Meta:
        """Meta class."""

        model = Collect
        fields = [
            "id",
            "user",
            "user_details",
            "customer",
            "customer_details",
            "date",
            "total",
        ]
        read_only_fields = ["user_details", "customer_details"]
