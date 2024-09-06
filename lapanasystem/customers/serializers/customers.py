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
        fields = ('id', 'name', 'email', 'phone_number', 'address', 'customer_type')
        read_only_fields = ('id',)
