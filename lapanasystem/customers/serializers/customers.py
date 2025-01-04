"""Customers serializers."""

# Django REST Framework
from rest_framework import serializers

# Models
from lapanasystem.customers.models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    """Customer model serializer."""

    class Meta:
        """Meta class."""

        model = Customer
        fields = ("id", "name", "email", "phone_number", "address", "customer_type")
        read_only_fields = ("id",)

    def validate_email(self, value):
        """Normalize email to lowercase."""
        return value.lower() if value else None
