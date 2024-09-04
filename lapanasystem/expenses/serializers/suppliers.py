"""Suppliers serializers."""

# Django REST Framework
from rest_framework import serializers

# Models
from lapanasystem.expenses.models import Supplier


class SupplierSerializer(serializers.ModelSerializer):
    """Supplier model serializer."""

    class Meta:
        """Meta options."""

        model = Supplier
        fields = [
            "id",
            "name",
            "phone_number",
            "email",
            "address",
        ]
        read_only_fields = ["id"]
