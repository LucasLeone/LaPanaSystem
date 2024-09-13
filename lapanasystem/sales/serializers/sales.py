"""Sales serializers."""

# Django
from django.db import transaction

# Django REST Framework
from rest_framework import serializers

# Models
from lapanasystem.sales.models import Sale, SaleDetail, StateChange
from lapanasystem.products.models import Product


class SaleDetailSerializer(serializers.ModelSerializer):
    """Serializer for SaleDetail model."""

    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True)
    )
    quantity = serializers.DecimalField(
        min_value=0.001, max_digits=10, decimal_places=3
    )
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = SaleDetail
        fields = ["id", "product", "quantity", "price", "subtotal"]
        read_only_fields = ["id", "price"]

    def get_subtotal(self, obj):
        """Calculate the subtotal based on price and quantity."""
        return obj.price * obj.quantity

    def validate(self, data):
        """Validate the quantity."""
        quantity = data.get("quantity", None)
        if quantity is not None and quantity <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0.")
        return data

    def create(self, validated_data):
        """Create a sale detail."""
        sale = self.context.get("sale")
        product = validated_data["product"]

        price = (
            product.wholesale_price
            if sale.sale_type == Sale.MAYORISTA
            else product.retail_price
        )

        return SaleDetail.objects.create(sale=sale, price=price, **validated_data)

    def update(self, instance, validated_data):
        """Update a sale detail."""
        sale = self.context.get("sale")
        product = validated_data.get("product", instance.product)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.price = (
            product.wholesale_price
            if sale.sale_type == Sale.MAYORISTA
            else product.retail_price
        )
        instance.save()
        return instance


class StateChangeSerializer(serializers.ModelSerializer):
    """Serializer for StateChange model."""

    state_display = serializers.CharField(source="get_state_display", read_only=True)

    class Meta:
        model = StateChange
        fields = ["id", "sale", "state", "state_display", "start_date", "end_date"]


class SaleSerializer(serializers.ModelSerializer):
    """Serializer for Sale model."""

    sale_details = SaleDetailSerializer(many=True, required=False)
    state_changes = StateChangeSerializer(many=True, read_only=True)
    state = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = [
            "id",
            "user",
            "customer",
            "date",
            "total",
            "sale_type",
            "payment_method",
            "state",
            "sale_details",
            "state_changes",
        ]

    def get_state(self, obj):
        """Return the current state of the sale using the get_state method in the model."""
        return obj.get_state()

    def validate(self, data):
        """Validate the sale details."""
        sale_details = data.get("sale_details", [])
        total = data.get("total", None)

        if not sale_details and not total:
            raise serializers.ValidationError(
                "La venta debe tener al menos un detalle o el total."
            )

        return data

    @transaction.atomic
    def create(self, validated_data):
        """Create a sale."""
        sale_details_data = validated_data.pop("sale_details", [])
        sale = Sale.objects.create(**validated_data)

        for sale_detail_data in sale_details_data:
            product = sale_detail_data.pop("product")
            sale_detail_data["product"] = product.pk

            sale_detail_serializer = SaleDetailSerializer(
                data=sale_detail_data, context={"sale": sale}
            )
            sale_detail_serializer.is_valid(raise_exception=True)
            sale_detail_serializer.save()

        if sale_details_data:
            sale.calculate_total()
            StateChange.objects.create(sale=sale, state=StateChange.CREADA)
        else:
            StateChange.objects.create(sale=sale, state=StateChange.COBRADA)

        return sale

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update a sale."""
        sale_details_data = validated_data.pop("sale_details", [])
        sale = instance

        sale_type_changed = False
        new_sale_type = validated_data.get("sale_type", sale.sale_type)
        if new_sale_type != sale.sale_type:
            sale_type_changed = True

        for attr, value in validated_data.items():
            setattr(sale, attr, value)
        sale.save()

        if sale_type_changed:
            for detail in sale.sale_details.all():
                sale_detail_serializer = SaleDetailSerializer(
                    detail, data={}, context={"sale": sale}, partial=True
                )
                sale_detail_serializer.is_valid(raise_exception=True)
                sale_detail_serializer.save()

        existing_details = {detail.id: detail for detail in sale.sale_details.all()}
        incoming_ids = []

        for detail_data in sale_details_data:
            detail_id = detail_data.get("id", None)
            detail_data["product"] = detail_data["product"].pk
            if detail_id:
                detail = existing_details.get(detail_id)
                if detail:
                    sale_detail_serializer = SaleDetailSerializer(
                        detail, data=detail_data, context={"sale": sale}
                    )
                    sale_detail_serializer.is_valid(raise_exception=True)
                    sale_detail_serializer.save()
                incoming_ids.append(detail_id)
            else:
                sale_detail_serializer = SaleDetailSerializer(
                    data=detail_data, context={"sale": sale}
                )
                sale_detail_serializer.is_valid(raise_exception=True)
                sale_detail_serializer.save()

        for detail_id, detail in existing_details.items():
            if detail_id not in incoming_ids:
                detail.delete()

        sale.calculate_total()

        return sale
