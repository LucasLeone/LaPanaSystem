"""Products models."""

# Django
from django.db import models
from django.utils.text import slugify

# Utilities
from lapanasystem.utils.models import LPSModel


class ProductCategory(LPSModel):
    """Product category model."""

    name = models.CharField("category name", max_length=30)
    description = models.TextField("category description", blank=True, max_length=255)

    def __str__(self):
        """Return category name."""
        return self.name

    class Meta:
        """Meta options."""

        verbose_name = "Product Category"
        verbose_name_plural = "Product Categories"


class ProductBrand(LPSModel):
    """Product brand model."""

    name = models.CharField("brand name", max_length=30)
    description = models.TextField("brand description", blank=True, max_length=255)

    def __str__(self):
        """Return brand name."""
        return self.name

    class Meta:
        """Meta options."""

        verbose_name = "Product Brand"
        verbose_name_plural = "Product Brands"


class Product(LPSModel):
    """Product model."""

    GRAMS = "g"
    KILOS = "kg"
    LITERS = "l"
    MILLILITERS = "ml"
    CUBIC_CENTIMETERS = "cm3"

    WEIGHT_UNIT_CHOICES = [
        (GRAMS, "Gramos"),
        (KILOS, "Kilos"),
        (LITERS, "Litros"),
        (MILLILITERS, "Mililitros"),
        (CUBIC_CENTIMETERS, "Centímetros cúbicos"),
    ]

    barcode = models.CharField("product barcode", max_length=255, unique=True)
    name = models.CharField("product name", max_length=100)
    slug = models.SlugField(unique=True, blank=True, max_length=255)
    retail_price = models.DecimalField("retail price", max_digits=10, decimal_places=2)
    wholesale_price = models.DecimalField(
        "wholesale price", max_digits=10, decimal_places=2, blank=True, null=True
    )
    weight = models.DecimalField(
        "product weight", max_digits=10, decimal_places=3, blank=True, null=True
    )
    weight_unit = models.CharField(
        max_length=3, choices=WEIGHT_UNIT_CHOICES, blank=True, null=True
    )
    description = models.TextField("product description", blank=True)
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.RESTRICT,
        related_name="products",
    )
    brand = models.ForeignKey(
        ProductBrand,
        on_delete=models.RESTRICT,
        related_name="products",
    )

    def __str__(self):
        """Return product name."""
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            num = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{num}"
                num += 1
            self.slug = slug
        super().save(*args, **kwargs)
