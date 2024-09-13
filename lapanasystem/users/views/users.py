"""Users views."""

# Django REST Framework
from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

# Permissions
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from lapanasystem.users.permissions import IsAdmin

# Models
from lapanasystem.users.models import User

# Serializers
from lapanasystem.users.serializers import UserCreateSerializer
from lapanasystem.users.serializers import UserLoginSerializer
from lapanasystem.users.serializers import UserLogoutSerializer
from lapanasystem.users.serializers import UserSerializer

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
        if self.action in ["login"]:
            permissions = [AllowAny]
        elif self.action in [
            "create_user",
            "update",
            "retrieve",
            "list",
            "destroy",
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

    def destroy(self, request, *args, **kwargs):
        """Soft delete user."""
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response(
            status=status.HTTP_204_NO_CONTENT,
            data={"message": "User deleted successfully."},
        )

    def list(self, request, *args, **kwargs):
        """List all users."""
        users = User.objects.filter(is_active=True)
        data = UserSerializer(users, many=True).data
        return Response(data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        """Update user."""
        user = self.get_object()
        if user.is_active is False:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": "User is inactive."},
            )

        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = serializer.data
        return Response(data, status=status.HTTP_200_OK)
