"""API router configuration."""

# Django
from django.conf import settings

# Django REST Framework
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

# Views
from lapanasystem.users.views.users import UserViewSet
from lapanasystem.expenses.views.expenses import CategoryViewSet
from lapanasystem.expenses.views.expenses import ExpenseViewSet
from lapanasystem.expenses.views.suppliers import SupplierViewSet
from lapanasystem.products.views.products import (
    ProductBrandViewSet,
    ProductCategoryViewSet,
    ProductViewSet
)
from lapanasystem.customers.views.customers import CustomerViewSet

# Router
router = DefaultRouter() if settings.DEBUG else SimpleRouter()


# Endpoints
router.register(r"users", UserViewSet, basename="users")
router.register(r"expenses", ExpenseViewSet, basename="expenses")
router.register(r"expense-categories", CategoryViewSet, basename="expense-categories")
router.register(r"suppliers", SupplierViewSet, basename="suppliers")
router.register(r"products", ProductViewSet, basename="products")
router.register(r"product-brands", ProductBrandViewSet, basename="product-brands")
router.register(
    r"product-categories",
    ProductCategoryViewSet,
    basename="product-categories",
)
router.register(r"customers", CustomerViewSet, basename="customers")


app_name = "api"
urlpatterns = router.urls
