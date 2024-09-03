"""API router configuration."""

# Django
from django.conf import settings

# Django REST Framework
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

# Views
from lapanasystem.users.views.users import UserViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()


router.register(r"users", UserViewSet, basename="users")


app_name = "api"
urlpatterns = router.urls
