"""Products models."""

# Django
from django.db import models
from django.utils.text import slugify

# Utilities
from lapanasystem.utils.models import LPSModel


class ProductCategory(LPSModel):
    """Product category model."""

    name = models.CharField("category name", max_length=255)
    description = models.TextField("category description", blank=True)

    def __str__(self):
        """Return category name."""
        return self.name


class ProductBrand(LPSModel):
    """Product brand model."""

    name = models.CharField("brand name", max_length=255)
    description = models.TextField("brand description", blank=True)

    def __str__(self):
        """Return brand name."""
        return self.name


class Product(LPSModel):
    """Product model."""

    GRAMS = "g"
    KILOS = "kg"

    WEIGHT_UNIT_CHOICES = [
        (GRAMS, "Gramos"),
        (KILOS, "Kilos"),
    ]

    barcode = models.CharField("product barcode", max_length=255, unique=True)
    name = models.CharField("product name", max_length=255)
    slug = models.SlugField(unique=True, blank=True, max_length=255)
    retail_price = models.DecimalField("retail price", max_digits=10, decimal_places=2)
    wholesale_price = models.DecimalField(
        "wholesale price",
        max_digits=10,
        decimal_places=2,
    )
    weight = models.DecimalField("product weight", max_digits=10, decimal_places=3)
    weight_unit = models.CharField(
        max_length=2,
        choices=WEIGHT_UNIT_CHOICES,
        default=GRAMS,
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
    is_active = models.BooleanField(default=True)

    def __str__(self):
        """Return product name."""
        return self.name

    def save(self, *args, **kwargs):
        """Override save method to generate slug automatically."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)