"""Products admin."""

# Django
from django.contrib import admin

# Models
from lapanasystem.products.models import Product, ProductBrand, ProductCategory


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Product admin."""

    list_display = [
        "id",
        "barcode",
        "name",
        "retail_price",
        "wholesale_price",
        "weight",
        "weight_unit",
        "category",
        "brand",
        "is_active",
    ]
    list_display_links = ["barcode", "name"]
    search_fields = ["barcode", "name", "category__name", "brand__name"]
    list_filter = ["category", "brand"]
    list_editable = ["is_active",]


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    """ProductCategory admin."""

    list_display = ["id", "name", "description", "is_active"]
    list_display_links = ["id", "name"]
    search_fields = ["name"]
    list_editable = ["is_active",]


@admin.register(ProductBrand)
class ProductBrandAdmin(admin.ModelAdmin):
    """ProductBrand admin."""

    list_display = ["id", "name", "description", "is_active"]
    list_display_links = ["id", "name"]
    search_fields = ["name"]
    list_editable = ["is_active",]
