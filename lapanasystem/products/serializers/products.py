"""Products serializers."""

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


class ProductBrandSerializer(serializers.ModelSerializer):
    """Serializer for ProductBrand model."""

    class Meta:
        model = ProductBrand
        fields = ["id", "name", "description"]


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
    weitgh_unit = serializers.ChoiceField(choices=Product.WEIGHT_UNIT_CHOICES)

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
