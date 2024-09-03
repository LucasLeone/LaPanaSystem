"""Users views."""

# Django

# Django REST Framework
from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

# Permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Models
from lapanasystem.users.models import User
from lapanasystem.users.models import UserType

# Permissions
from lapanasystem.users.permissions import IsAdmin
from lapanasystem.users.serializers import UserCreateSerializer

# Serializers
from lapanasystem.users.serializers import UserLoginSerializer
from lapanasystem.users.serializers import UserLogoutSerializer
from lapanasystem.users.serializers import UserSerializer
from lapanasystem.users.serializers import UserTypeSerializer


class UserViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """User view set.

    Handle login, logout, create, update and retrieve users.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = "username"

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action in ["login"]:
            permissions = [AllowAny]
        elif self.action in [
            "create_user",
            "update_user",
            "get_users",
            "get_user_types",
        ]:
            permissions = [IsAuthenticated, IsAdmin]
        else:
            permissions = [IsAuthenticated]
        return [permission() for permission in permissions]

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
        return Response(data, status=status.HTTP_201_CREATED)

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

    @action(detail=True, methods=["put"], url_path="update-user")
    def update_user(self, request, username):
        """Update user."""
        user = self.get_object()
        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = UserSerializer(user).data
        return Response(data)

    @action(detail=False, methods=["get"], url_path="list")
    def get_users(self, request):
        """Get users."""
        users = User.objects.all()
        data = UserSerializer(users, many=True).data
        return Response(data)

    @action(detail=False, methods=["get"], url_path="list-user-types")
    def get_user_types(self, request):
        """Get user types."""
        user_types = UserType.objects.all()
        data = UserTypeSerializer(user_types, many=True).data
        return Response(data)

    @action(detail=False, methods=["post"])
    def create_user_type(self, request):
        """Create user type."""
        serializer = UserTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_type = serializer.save()
        data = UserTypeSerializer(user_type).data
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["put"])
    def update_user_type(self, request, pk):
        """Update user type."""
        user_type = UserType.objects.get(pk=pk)
        serializer = UserTypeSerializer(user_type, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user_type = serializer.save()
        data = UserTypeSerializer(user_type).data
        return Response(data)

    @action(detail=True, methods=["delete"])
    def delete_user_type(self, request, pk):
        """Delete user type."""
        user_type = UserType.objects.get(pk=pk)
        user_type.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
