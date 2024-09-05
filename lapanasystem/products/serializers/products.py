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
        queryset=ProductCategory.objects.all(),
    )
    brand = serializers.PrimaryKeyRelatedField(queryset=ProductBrand.objects.all())

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
            "brand",
        ]
        read_only_fields = ["id", "slug"]
