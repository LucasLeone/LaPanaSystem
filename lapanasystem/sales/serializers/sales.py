"""Sales serializers."""

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
        if data["quantity"] <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0.")
        return data

    def create(self, validated_data):
        """Create a sale detail."""
        sale = self.context.get('sale')
        product = validated_data["product"]

        price = product.wholesale_price if sale.sale_type == Sale.MAYORISTA else product.retail_price

        return SaleDetail.objects.create(sale=sale, price=price, **validated_data)


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
            'state',
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
            raise serializers.ValidationError("La venta debe tener al menos un detalle o el total.")

        return data

    def create(self, validated_data):
        """Create a sale."""
        sale_details_data = validated_data.pop("sale_details", [])
        sale = Sale.objects.create(**validated_data)

        for sale_detail_data in sale_details_data:
            product = sale_detail_data.pop("product")
            sale_detail_data["product"] = product.pk

            sale_detail_serializer = SaleDetailSerializer(
                data=sale_detail_data,
                context={"sale": sale}
            )
            sale_detail_serializer.is_valid(raise_exception=True)
            sale_detail_serializer.save()

        if sale_details_data:
            sale.calculate_total()
            StateChange.objects.create(sale=sale, state=StateChange.CREADA)
        else:
            StateChange.objects.create(sale=sale, state=StateChange.COBRADA)

        return sale

    def update(self, instance, validated_data):
        """Update a sale."""
        sale_details_data = validated_data.pop("sale_details", [])
        sale = instance

        for sale_detail_data in sale_details_data:
            product = sale_detail_data.pop("product")
            sale_detail_data["product"] = product.pk

            sale_detail_serializer = SaleDetailSerializer(
                data=sale_detail_data,
                context={"sale": sale}
            )
            sale_detail_serializer.is_valid(raise_exception=True)
            sale_detail_serializer.save()

        if sale_details_data:
            sale.calculate_total()
            StateChange.objects.create(sale=sale, state=StateChange.CREADA)
        else:
            sale.total = validated_data.get("total", sale.total)

        return sale
