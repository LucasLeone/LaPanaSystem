"""Users views."""

# Django
from django.core.cache import cache

# Django REST Framework
from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

# Permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from lapanasystem.users.permissions import IsAdmin

# Models
from lapanasystem.users.models import User

# Serializers
from lapanasystem.users.serializers import (
    UserCreateSerializer,
    UserLoginSerializer,
    UserLogoutSerializer,
    UserSerializer,
)

# Filters
from rest_framework.filters import OrderingFilter, SearchFilter


class UserViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """User view set.

    Handle login, logout, create, update and retrieve users.

    Actions:
        - login: User sign in.
        - logout: User sign out.
        - create_user: Create a new user.
        - retrieve: Return a user's details.
        - list: Return a list of users.
        - update: Update a user's details.
        - destroy: Soft delete a user.

    Filters:
        - search: Search users by username or email.
        - ordering: Order users by username or email.

    Permissions:
        - login: AllowAny
        - logout: IsAuthenticated
        - create_user: IsAuthenticated, IsAdmin
        - retrieve: IsAuthenticated, IsAdmin
        - list: IsAuthenticated, IsAdmin
        - update: IsAuthenticated, IsAdmin
        - partial_update: IsAuthenticated, IsAdmin
        - destroy: IsAuthenticated, IsAdmin
    """

    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    lookup_field = "username"
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["username", "email"]
    ordering_fields = ["username", "email"]

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action == "login":
            permission_classes = [AllowAny]
        elif self.action in [
            "create_user",
            "update",
            "partial_update",
            "retrieve",
            "list",
            "destroy",
        ]:
            permission_classes = [IsAuthenticated, IsAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["post"])
    def login(self, request):
        """User sign in."""
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, token = serializer.save()
        data = {
            "user": UserSerializer(user).data,
            "access_token": token,
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def logout(self, request):
        """User logout."""
        serializer = UserLogoutSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            status=status.HTTP_204_NO_CONTENT,
            data={"message": "User logged out successfully!"},
        )

    @action(detail=False, methods=["post"], url_path="create-user")
    def create_user(self, request):
        """Create user."""
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = UserSerializer(user).data

        cache.delete("users_list")
        cache.set(f"user_{user.username}", data, timeout=86400)

        return Response(data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Soft delete user."""
        user = self.get_object()
        user.is_active = False
        user.save()

        cache.delete("users_list")
        cache.delete(f"user_{user.username}")

        return Response(
            status=status.HTTP_204_NO_CONTENT,
            data={"message": "User deleted successfully."},
        )

    def list(self, request, *args, **kwargs):
        """List all users with caching."""
        cache_key = "users_list"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data

        cache.set(cache_key, data, timeout=86400)

        return Response(data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single user with caching."""
        username = kwargs.get("username")
        cache_key = f"user_{username}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        user = self.get_object()
        serializer = self.get_serializer(user)
        data = serializer.data

        cache.set(cache_key, data, timeout=86400)

        return Response(data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        """Update user with cache invalidation."""
        user = self.get_object()
        if not user.is_active:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": "User is inactive."},
            )

        old_username = user.username

        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = serializer.data

        new_username = user.username

        cache.delete("users_list")
        cache.delete(f"user_{old_username}")
        if old_username != new_username:
            cache.delete(f"user_{new_username}")

        cache.set(f"user_{new_username}", data, timeout=86400)

        return Response(data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """Partial update user with cache invalidation."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
