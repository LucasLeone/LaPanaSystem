"""Products views."""

# Django REST Framework
from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response

# Models
from lapanasystem.products.models import Product
from lapanasystem.products.models import ProductBrand
from lapanasystem.products.models import ProductCategory

# Serializers
from lapanasystem.products.serializers import ProductSerializer
from lapanasystem.products.serializers import ProductBrandSerializer
from lapanasystem.products.serializers import ProductCategorySerializer

# Permissions
from lapanasystem.users.permissions import IsAdmin
from lapanasystem.users.permissions import IsSeller
from rest_framework.permissions import IsAuthenticated


class ProductViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Product view set.

    Handle create, update, retrieve and list products.
    """

    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    lookup_field = "slug"

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action in ["create", "retrieve", "list", "update"]:
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


class ProductBrandViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Product brand view set.

    Handle create, update, retrieve and list product brands.
    """

    queryset = ProductBrand.objects.filter(is_active=True)
    serializer_class = ProductBrandSerializer
    lookup_field = "id"

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action in ["create", "retrieve", "list", "update"]:
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
            {"message": "Product brand deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )


class ProductCategoryViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Product category view set.

    Handle create, update, retrieve and list product categories.
    """

    queryset = ProductCategory.objects.filter(is_active=True)
    serializer_class = ProductCategorySerializer
    lookup_field = "id"

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action in ["create", "retrieve", "list", "update"]:
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
            {"message": "Product category deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )
