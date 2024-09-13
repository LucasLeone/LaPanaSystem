"""Customers serializers."""

# Django REST Framework
from rest_framework import serializers

# Models
from lapanasystem.customers.models import Customer


class CustomerModelSerializer(serializers.ModelSerializer):
    """Customer model serializer."""

    class Meta:
        """Meta class."""

        model = Customer
        fields = ("id", "name", "email", "phone_number", "address", "customer_type")
        read_only_fields = ("id",)
        unique_together = ("email", "is_active")

    def validate_email(self, value):
        """Normalize email to lowercase."""
        return value.lower()

    def validate(self, data):
        """Add any cross-field validations here."""
        if data.get("customer_type") == "mayorista" and not data.get("address"):
            raise serializers.ValidationError(
                "Los clientes mayoristas deben tener una dirección."
            )
        return data
