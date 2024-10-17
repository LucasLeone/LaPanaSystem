"""Sales serializers."""

# Django
from django.db import transaction
from django.utils import timezone

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

# Tasks
from lapanasystem.sales.tasks import change_state_to_ready_for_delivery

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
        min_value=Decimal("0.001"), max_digits=10, decimal_places=3
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
        else:
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
        validated_data["price"] = price

        return SaleDetail.objects.create(sale=sale, **validated_data)

    def update(self, instance, validated_data):
        """Update a sale detail."""
        sale = self.context.get("sale")
        product = validated_data.get("product", instance.product)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

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
        queryset=Customer.objects.all(),
        required=False,
        write_only=True,
        allow_null=True,
    )
    customer_details = CustomerSerializer(source="customer", read_only=True)
    sale_details = SaleDetailSerializer(many=True, required=False)
    state_changes = StateChangeSerializer(many=True, read_only=True)
    state = serializers.SerializerMethodField()

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
            "total_collected",
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
            "total",
            "total_collected",
        ]

    def get_state(self, obj):
        """Return the current state of the sale using the get_state method in the model."""
        return obj.get_state()

    def validate(self, data):
        """Validate the sale details."""
        sale_details = data.get("sale_details", [])

        if not sale_details:
            raise serializers.ValidationError(
                "La venta debe tener al menos un detalle."
            )

        product_ids = [detail['product'].id if isinstance(detail['product'], Product) else detail['product'] for detail in sale_details]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("No se pueden repetir productos en los detalles de la venta.")

        return data

    @transaction.atomic
    def create(self, validated_data):
        """Create a sale."""
        sale_details_data = validated_data.pop("sale_details", [])
        needs_delivery = validated_data.get("needs_delivery", False)

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
            eta = (
                sale.date
                if timezone.is_aware(sale.date)
                else timezone.make_aware(sale.date)
            )
            transaction.on_commit(lambda: change_state_to_ready_for_delivery.apply_async(args=[sale.id], eta=eta))
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

        if 'customer' not in self.initial_data:
            validated_data['customer'] = None

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

            for detail_id, detail in existing_details.items():
                if detail_id not in incoming_ids:
                    detail.delete()

            sale.calculate_total()

        return sale


class PartialChargeSerializer(serializers.Serializer):
    """Serializer for partial charges."""

    total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        help_text="Monto parcial cobrado. Debe ser mayor que cero y no exceder el total de la venta."
    )

    def validate_total(self, value):
        """Validate total not exceeding the total of the sale."""
        sale = self.context.get('sale')
        if sale is None:
            raise serializers.ValidationError("No se proporcionó la venta para la validación.")

        if value > sale.total:
            raise serializers.ValidationError("El monto parcial no puede exceder el total de la venta.")

        return value


class FastSaleSerializer(serializers.Serializer):
    """Serializer for fast sales."""

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    user_details = UserSerializer(source="user", read_only=True)
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        required=False,
        allow_null=True
    )
    customer_details = CustomerSerializer(source='customer', read_only=True)
    total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        required=True
    )
    date = serializers.DateTimeField(required=False)
    payment_method = serializers.ChoiceField(
        choices=Sale.SALE_PAYMENT_METHOD_CHOICES,
        default=Sale.EFECTIVO,
        required=False
    )

    class Meta:
        """Meta options."""

        fields = [
            'user',
            'user_details',
            'customer',
            'customer_details',
            'total',
            'date',
            'payment_method'
        ]
        read_only_fields = ['user_details', 'customer_details']

    def validate(self, data):
        """Validate the total."""
        total = data.get('total', None)
        if total is None:
            raise serializers.ValidationError("El total es requerido.")

        return data

    def create(self, validated_data):
        """Create a fast sale."""
        user = validated_data.get('user')
        customer = validated_data.get('customer', None)
        total = validated_data.get('total')
        date = validated_data.get('date', timezone.now())
        payment_method = validated_data.get('payment_method', Sale.EFECTIVO)

        sale = Sale.objects.create(
            user=user,
            customer=customer,
            total=total,
            total_collected=total,
            date=date,
            payment_method=payment_method
        )

        StateChange.objects.create(sale=sale, state=StateChange.COBRADA)

        return sale

    def update(self, instance, validated_data):
        """Update a fast sale."""
        instance.customer = validated_data.get('customer', instance.customer)
        instance.total = validated_data.get('total', instance.total)
        instance.date = validated_data.get('date', instance.date)
        instance.payment_method = validated_data.get('payment_method', instance.payment_method)

        instance.total_collected = instance.total

        instance.save()

        return instance
