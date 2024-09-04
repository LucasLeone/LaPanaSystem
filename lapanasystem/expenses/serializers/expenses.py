"""Expenses serializer."""

# Django REST Framework
from rest_framework import serializers

from lapanasystem.expenses.models import Category

# Models
from lapanasystem.expenses.models import Expense
from lapanasystem.expenses.models import Supplier
from lapanasystem.users.models import User


class CategorySerializer(serializers.ModelSerializer):
    """Category model serializer."""

    class Meta:
        """Meta options."""

        model = Category
        fields = [
            "id",
            "name",
            "description",
        ]
        read_only_fields = ["id"]


class ExpenseSerializer(serializers.ModelSerializer):
    """Expense model serializer."""

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    supplier = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(),
        allow_null=True,
    )

    class Meta:
        model = Expense
        fields = ["id", "user", "amount", "date", "description", "category", "supplier"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        """Handle expense creation."""
        return Expense.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Handle expense update."""
        instance.user = validated_data.get("user", instance.user)
        instance.amount = validated_data.get("amount", instance.amount)
        instance.date = validated_data.get("date", instance.date)
        instance.description = validated_data.get("description", instance.description)
        instance.category = validated_data.get("category", instance.category)
        instance.supplier = validated_data.get("supplier", instance.supplier)
        instance.save()
        return instance
