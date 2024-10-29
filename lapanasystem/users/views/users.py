"""Users views."""

# Django REST Framework
from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

# Permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from lapanasystem.users.permissions import IsAdmin, IsRequestUser

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
    ordering_fields = ["username", "email", "first_name", "last_name"]

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action == "login":
            permission_classes = [AllowAny]
        elif self.action == "list":
            permission_classes = [IsAuthenticated]
        elif self.action in [
            "create_user",
            "update",
            "partial_update",
            "retrieve",
            "destroy",
        ]:
            permission_classes = [IsAuthenticated, IsAdmin]
        elif self.action in ["profile",]:
            permission_classes = [IsAuthenticated, IsRequestUser]
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

        return Response(data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        """Disable delete (soft delete)."""
        instance.is_active = False
        instance.save()

    def destroy(self, request, *args, **kwargs):
        """Handle soft delete with confirmation message."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "User deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(detail=False, methods=["get"], url_path="profile")
    def profile(self, request):
        """Return user's profile."""
        user = request.user
        data = UserSerializer(user).data
        return Response(data, status=status.HTTP_200_OK)
