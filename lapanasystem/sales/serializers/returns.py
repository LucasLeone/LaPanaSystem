# Django
from django.db import transaction

# Django REST Framework
from rest_framework import serializers

# Models
from lapanasystem.sales.models import Return, ReturnDetail
from lapanasystem.products.models import Product
from lapanasystem.sales.models import Sale

# Serializers
from lapanasystem.products.serializers import ProductSerializer
from lapanasystem.users.serializers import UserSerializer
from lapanasystem.sales.serializers import SaleSerializer

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

    def __init__(self, *args, **kwargs):
        """Set product field as not required for update."""
        super(ReturnDetailSerializer, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['product'].required = False

    def get_subtotal(self, obj):
        """Calculate the subtotal for the detail."""
        return obj.price * obj.quantity

    def validate(self, data):
        """Validate that the product has a valid wholesale price and quantity is valid."""
        product = data.get("product", getattr(self.instance, 'product', None))
        if product is None:
            raise serializers.ValidationError("El campo 'product' es obligatorio.")

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

    def update(self, instance, validated_data):
        """Update a return detail."""
        product = validated_data.get("product", instance.product)
        quantity = validated_data.get("quantity", instance.quantity)

        instance.product = product
        instance.quantity = quantity
        instance.price = product.wholesale_price
        instance.save()

        return instance


class ReturnSerializer(serializers.ModelSerializer):
    """Serializer for the Return model."""

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    user_details = UserSerializer(source="user", read_only=True)
    return_details = ReturnDetailSerializer(many=True, required=False)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    sale = serializers.PrimaryKeyRelatedField(
        queryset=Sale.objects.filter(is_active=True), required=True, write_only=True
    )
    sale_details = SaleSerializer(source="sale", read_only=True)
    customer = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Return
        fields = [
            "id",
            "user",
            "user_details",
            "date",
            "customer",
            "total",
            "sale",
            "sale_details",
            "return_details",
        ]
        read_only_fields = [
            "id",
            "total",
            "user_details",
            "sale_details",
        ]

    def get_customer(self, obj):
        """Return the customer details."""
        return {
            "id": obj.sale.customer.id,
            "name": obj.sale.customer.name,
            "email": obj.sale.customer.email,
        } if obj.sale.customer else None

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
