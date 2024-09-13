"""Expenses serializer."""

# Django REST Framework
from rest_framework import serializers

# Models
from lapanasystem.expenses.models import Expense
from lapanasystem.expenses.models import ExpenseCategory
from lapanasystem.expenses.models import Supplier

# Serializers
from .suppliers import SupplierSerializer


class CategorySerializer(serializers.ModelSerializer):
    """Category model serializer."""

    class Meta:
        """Meta options."""

        model = ExpenseCategory
        fields = [
            "id",
            "name",
            "description",
        ]
        read_only_fields = ["id"]


class ExpenseSerializer(serializers.ModelSerializer):
    """Expense model serializer."""

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    category = serializers.PrimaryKeyRelatedField(
        queryset=ExpenseCategory.objects.all(),
        write_only=True
    )
    supplier = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(),
        write_only=True,
        allow_null=True,
        required=False
    )

    category_details = CategorySerializer(source='category', read_only=True)
    supplier_details = SupplierSerializer(source='supplier', read_only=True, allow_null=True)

    class Meta:
        model = Expense
        fields = [
            "id", "user", "amount", "date", "description",
            "category", "supplier",
            "category_details", "supplier_details"
        ]
        read_only_fields = ["id", "category_details", "supplier_details"]
