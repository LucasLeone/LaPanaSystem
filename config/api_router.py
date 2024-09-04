"""API router configuration."""

# Django
from django.conf import settings

# Django REST Framework
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from lapanasystem.expenses.views.expenses import CategoryViewSet
from lapanasystem.expenses.views.expenses import ExpenseViewSet
from lapanasystem.expenses.views.suppliers import SupplierViewSet

# Views
from lapanasystem.users.views.users import UserViewSet

# Router
router = DefaultRouter() if settings.DEBUG else SimpleRouter()


# Endpoints
router.register(r"users", UserViewSet, basename="users")
router.register(r"expenses", ExpenseViewSet, basename="expenses")
router.register(r"expense-categories", CategoryViewSet, basename="categories")
router.register(r"suppliers", SupplierViewSet, basename="suppliers")


app_name = "api"
urlpatterns = router.urls
