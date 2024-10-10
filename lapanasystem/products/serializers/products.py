"""Products serializers."""

# Django
from django.db.models.functions import Lower

# Django REST Framework
from rest_framework import serializers

# Models
from lapanasystem.products.models import Product
from lapanasystem.products.models import ProductBrand
from lapanasystem.products.models import ProductCategory


class ProductCategorySerializer(serializers.ModelSerializer):
    """Serializer for ProductCategory model."""

    class Meta:
        model = ProductCategory
        fields = ["id", "name", "description"]

    def validate_name(self, value):
        """Validate name."""
        queryset = ProductCategory.objects.filter(name__iexact=value, is_active=True)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("Ya existe una categoría con este nombre.")

        return value


class ProductBrandSerializer(serializers.ModelSerializer):
    """Serializer for ProductBrand model."""

    class Meta:
        model = ProductBrand
        fields = ["id", "name", "description"]

    def validate_name(self, value):
        """Validate name."""
        queryset = ProductBrand.objects.filter(name__iexact=value, is_active=True)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("Ya existe una marca con este nombre.")

        return value


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model."""

    category = serializers.PrimaryKeyRelatedField(
        queryset=ProductCategory.objects.all(), write_only=True
    )
    category_details = ProductCategorySerializer(source="category", read_only=True)
    brand = serializers.PrimaryKeyRelatedField(
        queryset=ProductBrand.objects.all(), write_only=True
    )
    brand_details = ProductBrandSerializer(source="brand", read_only=True)
    weight_unit = serializers.ChoiceField(
        choices=Product.WEIGHT_UNIT_CHOICES, required=False, allow_null=True
    )
    wholesale_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "barcode",
            "name",
            "slug",
            "retail_price",
            "wholesale_price",
            "weight",
            "weight_unit",
            "description",
            "category",
            "category_details",
            "brand",
            "brand_details",
        ]
        read_only_fields = ["id", "slug", "category_details", "brand_details"]

    def validate(self, attrs):
        """Validate method override for validate if product exists."""
        name = attrs.get('name', self.instance.name if self.instance else None)
        weight = attrs.get('weight', self.instance.weight if self.instance else None)
        weight_unit = attrs.get('weight_unit', self.instance.weight_unit if self.instance else None)

        name_normalized = name.lower() if name else None

        queryset = Product.objects.annotate(
            name_lower=Lower('name')
        ).filter(name_lower=name_normalized)

        if weight is not None and weight_unit is not None:
            queryset = queryset.filter(weight=weight, weight_unit=weight_unit)
        elif weight is None and weight_unit is None:
            queryset = queryset.filter(weight__isnull=True, weight_unit__isnull=True)
        else:
            queryset = queryset.none()

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "Ya existe un producto con este nombre, peso y unidad de peso."
            )

        return attrs
