"""Products views."""

# Django
from django.core.cache import cache

# Django REST Framework
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

# Models
from lapanasystem.products.models import Product, ProductBrand, ProductCategory

# Serializers
from lapanasystem.products.serializers import (
    ProductSerializer,
    ProductBrandSerializer,
    ProductCategorySerializer,
)

# Permissions
from lapanasystem.users.permissions import IsAdmin, IsSeller
from rest_framework.permissions import IsAuthenticated


class ProductViewSet(ModelViewSet):
    """Product view set.

    Handle create, update, retrieve and list products.

    Actions:
        - create: Create a new product.
        - retrieve: Retrieve a product.
        - list: List products.
        - update: Update a product.
        - partial_update: Partial update a product.
        - destroy: Delete a product.

    Filters:
        - search: Search products by name or barcode.
        - ordering: Order products by name, retail price or wholesale price.
        - category: Filter products by category.
        - brand: Filter products by brand.

    Permissions:
        - create: IsAuthenticated, IsAdmin | IsSeller
        - retrieve: IsAuthenticated, IsAdmin | IsSeller
        - list: IsAuthenticated, IsAdmin | IsSeller
        - update: IsAuthenticated, IsAdmin | IsSeller
        - partial_update: IsAuthenticated, IsAdmin | IsSeller
        - destroy: IsAuthenticated, IsAdmin
    """

    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    lookup_field = "slug"
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ["name", "barcode"]
    ordering_fields = ["name", "retail_price", "wholesale_price"]
    filterset_fields = ["category", "brand"]

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action in ["create", "retrieve", "list", "update", "partial_update"]:
            permissions = [IsAuthenticated, IsAdmin | IsSeller]
        else:
            permissions = [IsAuthenticated, IsAdmin]
        return [permission() for permission in permissions]

    def perform_destroy(self, instance):
        """Disable delete (soft delete)."""
        instance.is_active = False
        instance.save()

    def destroy(self, request, *args, **kwargs):
        """Handle soft delete with confirmation message."""
        instance = self.get_object()
        self.perform_destroy(instance)
        cache.delete("products_list")
        cache.delete(f"product_{instance.slug}")
        return Response(
            {"message": "Product deleted successfully."},
            status=status.HTTP_200_OK,
        )

    def list(self, request, *args, **kwargs):
        """Cache the product list."""
        cache_key = "products_list"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=86400)
        return response

    def retrieve(self, request, *args, **kwargs):
        """Cache individual product retrieval."""
        product_slug = kwargs.get("slug")
        cache_key = f"product_{product_slug}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=86400)
        return response

    def create(self, request, *args, **kwargs):
        """Override create to handle caching."""
        response = super().create(request, *args, **kwargs)
        cache.delete("products_list")
        return response

    def update(self, request, *args, **kwargs):
        """Override update to handle caching."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        old_slug = instance.slug

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if old_slug != instance.slug:
            cache.delete(f"product_{old_slug}")
        cache.delete("products_list")
        cache.delete(f"product_{instance.slug}")

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """Override partial_update to handle caching."""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class ProductBrandViewSet(ModelViewSet):
    """Product brand view set.

    Handle create, update, retrieve and list product brands.
    """

    queryset = ProductBrand.objects.filter(is_active=True)
    serializer_class = ProductBrandSerializer
    lookup_field = "id"

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action in ["create", "retrieve", "list", "update", "partial_update"]:
            permissions = [IsAuthenticated, IsAdmin | IsSeller]
        else:
            permissions = [IsAuthenticated, IsAdmin]
        return [permission() for permission in permissions]

    def perform_destroy(self, instance):
        """Disable delete (soft delete)."""
        instance.is_active = False
        instance.save()

    def destroy(self, request, *args, **kwargs):
        """Handle soft delete with confirmation message."""
        instance = self.get_object()
        self.perform_destroy(instance)
        cache.delete("product_brands_list")
        cache.delete(f"product_brand_{instance.id}")
        return Response(
            {"message": "Product brand deleted successfully."},
            status=status.HTTP_200_OK,
        )

    def list(self, request, *args, **kwargs):
        """Cache the product brand list."""
        cache_key = "product_brands_list"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=86400)
        return response

    def retrieve(self, request, *args, **kwargs):
        """Cache individual product brand retrieval."""
        brand_id = kwargs.get("id")
        cache_key = f"product_brand_{brand_id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=86400)
        return response

    def create(self, request, *args, **kwargs):
        """Override create to handle caching."""
        response = super().create(request, *args, **kwargs)
        cache.delete("product_brands_list")
        return response

    def update(self, request, *args, **kwargs):
        """Override update to handle caching."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        cache.delete("product_brands_list")
        cache.delete(f"product_brand_{instance.id}")

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """Override partial_update to handle caching."""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class ProductCategoryViewSet(ModelViewSet):
    """Product category view set.

    Handle create, update, retrieve and list product categories.
    """

    queryset = ProductCategory.objects.filter(is_active=True)
    serializer_class = ProductCategorySerializer
    lookup_field = "id"

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action in ["create", "retrieve", "list", "update", "partial_update"]:
            permissions = [IsAuthenticated, IsAdmin | IsSeller]
        else:
            permissions = [IsAuthenticated, IsAdmin]
        return [permission() for permission in permissions]

    def perform_destroy(self, instance):
        """Disable delete (soft delete)."""
        instance.is_active = False
        instance.save()

    def destroy(self, request, *args, **kwargs):
        """Handle soft delete with confirmation message."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Product deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )
