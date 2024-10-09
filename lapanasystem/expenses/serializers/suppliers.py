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

    def validate_name(self, value):
        """Validate name."""
        queryset = Supplier.objects.filter(name__iexact=value)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("Ya existe un proveedor con este nombre.")

        return value
