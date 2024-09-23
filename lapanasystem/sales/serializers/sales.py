"""Sales serializers."""

# Django
from django.db import transaction

# Django REST Framework
from rest_framework import serializers

# Models
from lapanasystem.sales.models import Sale, SaleDetail, StateChange
from lapanasystem.products.models import Product
from lapanasystem.customers.models import Customer

# Serializers
from lapanasystem.products.serializers import ProductSerializer
from lapanasystem.customers.serializers import CustomerSerializer
from lapanasystem.users.serializers import UserSerializer

# Utilities
from decimal import Decimal


class SaleDetailSerializer(serializers.ModelSerializer):
    """Serializer for SaleDetail model."""

    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True),
        write_only=True,
    )
    product_details = ProductSerializer(source="product", read_only=True)

    quantity = serializers.DecimalField(
        min_value=Decimal('0.001'), max_digits=10, decimal_places=3
    )
    subtotal = serializers.SerializerMethodField()

    class Meta:
        """Meta options."""

        model = SaleDetail
        fields = ["id", "product", "product_details", "quantity", "price", "subtotal"]
        read_only_fields = ["id", "price", "subtotal", "product_details"]

    def get_subtotal(self, obj):
        """Return the subtotal of the detail."""
        return obj.price * obj.quantity

    def validate(self, data):
        """Validate the quantity."""
        quantity = data.get("quantity", None)
        if quantity is not None and quantity <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0.")
        return data

    def _get_price(self, sale, product):
        """Return the price of the product based on the sale type."""
        if sale.sale_type == Sale.MAYORISTA:
            if product.wholesale_price and product.wholesale_price > 0:
                return product.wholesale_price
            elif product.retail_price and product.retail_price > 0:
                return product.retail_price
            else:
                raise serializers.ValidationError(
                    f"El producto '{product.name}' no tiene precio definido para venta mayorista."
                )
        else:  # Venta minorista
            if product.retail_price and product.retail_price > 0:
                return product.retail_price
            else:
                raise serializers.ValidationError(
                    f"El producto '{product.name}' no tiene precio definido para venta minorista."
                )

    def create(self, validated_data):
        """Create a sale detail."""
        sale = self.context.get("sale")
        product = validated_data["product"]

        price = self._get_price(sale, product)
        validated_data['price'] = price

        return SaleDetail.objects.create(sale=sale, **validated_data)

    def update(self, instance, validated_data):
        """Update a sale detail."""
        sale = self.context.get("sale")
        product = validated_data.get("product", instance.product)

        # Actualizar los campos del detalle
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Recalcular el precio
        instance.price = self._get_price(sale, product)
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

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    user_details = UserSerializer(source="user", read_only=True)
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(), required=False, write_only=True
    )
    customer_details = CustomerSerializer(source="customer", read_only=True)
    sale_details = SaleDetailSerializer(many=True, required=False)
    state_changes = StateChangeSerializer(many=True, read_only=True)
    state = serializers.SerializerMethodField()
    needs_delivery = serializers.BooleanField(write_only=True, default=False)

    class Meta:
        model = Sale
        fields = [
            "id",
            "user",
            "user_details",
            "customer",
            "customer_details",
            "date",
            "total",
            "sale_type",
            "payment_method",
            "state",
            "sale_details",
            "state_changes",
            "needs_delivery",
        ]
        read_only_fields = [
            "id",
            "state",
            "state_changes",
            "customer_details",
            "user_details",
        ]

    def get_state(self, obj):
        """Return the current state of the sale using the get_state method in the model."""
        return obj.get_state()

    def validate(self, data):
        """Validate the sale details."""
        sale_details = data.get("sale_details", [])
        total = data.get("total", None)

        if not sale_details and total is None:
            raise serializers.ValidationError(
                "La venta debe tener al menos un detalle o el total."
            )

        if sale_details and total is not None:
            raise serializers.ValidationError(
                "La venta no puede tener detalles y total al mismo tiempo."
            )

        return data

    @transaction.atomic
    def create(self, validated_data):
        """Create a sale."""
        sale_details_data = validated_data.pop("sale_details", [])
        needs_delivery = validated_data.pop("needs_delivery", False)
        sale = Sale.objects.create(**validated_data)

        if sale_details_data:
            for sale_detail_data in sale_details_data:
                product = sale_detail_data.pop("product")
                sale_detail_data["product"] = product.pk

                sale_detail_serializer = SaleDetailSerializer(
                    data=sale_detail_data, context={"sale": sale}
                )
                sale_detail_serializer.is_valid(raise_exception=True)
                sale_detail_serializer.save()

        if sale_details_data and needs_delivery is True:
            sale.calculate_total()
            StateChange.objects.create(sale=sale, state=StateChange.CREADA)
        elif sale_details_data and needs_delivery is False:
            sale.calculate_total()
            StateChange.objects.create(sale=sale, state=StateChange.COBRADA)
        else:
            StateChange.objects.create(sale=sale, state=StateChange.COBRADA)

        return sale

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update a sale."""
        sale_details_data = validated_data.pop("sale_details", None)
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

        if sale_details_data is not None:
            existing_details = {detail.id: detail for detail in sale.sale_details.all()}
            incoming_ids = []

            for detail_data in sale_details_data:
                product = detail_data.pop("product")
                detail_data["product"] = product.pk
                detail_id = detail_data.get("id", None)
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

            # Eliminar detalles que no están en incoming_ids
            for detail_id, detail in existing_details.items():
                if detail_id not in incoming_ids:
                    detail.delete()

            # Recalcular total basado en los detalles
            sale.calculate_total()
        else:
            # No se proporcionaron sale_details_data, mantener el total proporcionado
            pass

        return sale
