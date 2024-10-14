# Django
from django.db import transaction

# Django REST Framework
from rest_framework import serializers

# Models
from lapanasystem.sales.models import Return, ReturnDetail
from lapanasystem.products.models import Product
from lapanasystem.customers.models import Customer

# Serializers
from lapanasystem.products.serializers import ProductSerializer
from lapanasystem.customers.serializers import CustomerSerializer
from lapanasystem.users.serializers import UserSerializer

# Utilities
from decimal import Decimal


class ReturnDetailSerializer(serializers.ModelSerializer):
    """Serializer for the ReturnDetail model."""

    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True, wholesale_price__gt=0),
        write_only=True,
    )
    product_details = ProductSerializer(source="product", read_only=True)

    quantity = serializers.DecimalField(
        min_value=Decimal("0.001"), max_digits=10, decimal_places=3
    )
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = ReturnDetail
        fields = ["id", "product", "product_details", "quantity", "price", "subtotal"]
        read_only_fields = ["id", "price", "subtotal", "product_details"]

    def get_subtotal(self, obj):
        """Calculate the subtotal for the detail."""
        return obj.price * obj.quantity

    def validate(self, data):
        """Validate that the product has a valid wholesale price and quantity is valid."""
        product = data.get("product")
        if not product.wholesale_price or product.wholesale_price <= 0:
            raise serializers.ValidationError(
                f"The product '{product.name}' does not have a valid wholesale price and cannot be returned."
            )
        return data

    def create(self, validated_data):
        """Create a return detail."""
        return_order = self.context.get("return")
        product = validated_data["product"]
        price = product.wholesale_price

        validated_data["price"] = price

        return ReturnDetail.objects.create(return_order=return_order, **validated_data)


class ReturnSerializer(serializers.ModelSerializer):
    """Serializer for the Return model."""

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    user_details = UserSerializer(source="user", read_only=True)
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(), required=True, write_only=True
    )
    customer_details = CustomerSerializer(source="customer", read_only=True)
    return_details = ReturnDetailSerializer(many=True, required=False)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Return
        fields = [
            "id",
            "user",
            "user_details",
            "customer",
            "customer_details",
            "date",
            "total",
            "return_details",
            "reason",
        ]
        read_only_fields = [
            "id",
            "total",
            "customer_details",
            "user_details",
        ]

    @transaction.atomic
    def create(self, validated_data):
        """Create a return."""
        return_details_data = validated_data.pop("return_details", [])
        return_order = Return.objects.create(**validated_data)

        if return_details_data:
            for detail_data in return_details_data:
                product = detail_data.pop("product")
                detail_data["product"] = product.pk

                detail_serializer = ReturnDetailSerializer(
                    data=detail_data, context={"return": return_order}
                )
                detail_serializer.is_valid(raise_exception=True)
                detail_serializer.save()

            return_order.calculate_total()
            return return_order
        else:
            raise serializers.ValidationError(
                "La devolución tiene que tener un detalle por lo menos."
            )

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update a return."""
        return_details_data = validated_data.pop("return_details", [])
        return_order = instance

        for attr, value in validated_data.items():
            setattr(return_order, attr, value)
        return_order.save()

        existing_details = {
            detail.id: detail for detail in return_order.return_details.all()
        }
        incoming_ids = []

        for detail_data in return_details_data:
            detail_id = detail_data.get("id", None)
            product = detail_data.pop("product")
            detail_data["product"] = product.pk

            if detail_id:
                detail = existing_details.get(detail_id)
                if detail:
                    detail_serializer = ReturnDetailSerializer(
                        detail, data=detail_data, context={"return": return_order}
                    )
                    detail_serializer.is_valid(raise_exception=True)
                    detail_serializer.save()
                incoming_ids.append(detail_id)
            else:
                detail_serializer = ReturnDetailSerializer(
                    data=detail_data, context={"return": return_order}
                )
                detail_serializer.is_valid(raise_exception=True)
                detail_serializer.save()

        for detail_id, detail in existing_details.items():
            if detail_id not in incoming_ids:
                detail.delete()

        return_order.calculate_total()
        return return_order
