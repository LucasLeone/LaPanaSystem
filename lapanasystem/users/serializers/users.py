"""Users serializers."""

# Django
from django.contrib.auth import authenticate

# Django REST Framework
from rest_framework import serializers
from rest_framework.authtoken.models import Token

# Models
from lapanasystem.users.models import User
from lapanasystem.users.models import UserType


class UserTypeSerializer(serializers.ModelSerializer):
    """UserType model serializer."""

    class Meta:
        """Meta options."""

        model = UserType
        fields = ["id", "name", "description"]


class UserSerializer(serializers.ModelSerializer):
    """User model serializer."""

    user_type = serializers.PrimaryKeyRelatedField(queryset=UserType.objects.all())

    class Meta:
        """Meta options."""

        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "user_type",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        """Handle user creation."""
        user_type = validated_data.pop("user_type")
        return User.objects.create(user_type=user_type, **validated_data)

    def update(self, instance, validated_data):
        """Handle user update."""
        user_type = validated_data.pop("user_type", None)

        if user_type:
            instance.user_type = user_type

        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.email = validated_data.get("email", instance.email)
        instance.phone_number = validated_data.get(
            "phone_number",
            instance.phone_number,
        )
        instance.save()

        return instance

    def get_user_type(self, obj):
        """Get user type as a serialized representation."""
        if obj.user_type:
            return UserTypeSerializer(obj.user_type).data
        return None


class UserLoginSerializer(serializers.Serializer):
    """User login serializer.

    Handle the login request data.
    """

    username = serializers.CharField()
    password = serializers.CharField(min_length=8, max_length=64)

    def validate(self, data):
        """Check credentials."""
        user = authenticate(username=data["username"], password=data["password"])
        if not user:
            error_message = "Invalid credentials"
            raise serializers.ValidationError(error_message)
        if not user.is_active:
            error_message = "This account is inactive."
            raise serializers.ValidationError(error_message)
        self.context["user"] = user
        return data

    def create(self, data):
        """Generate or retrieve new token."""
        token, _ = Token.objects.get_or_create(user=self.context["user"])
        return self.context["user"], token.key


class UserLogoutSerializer(serializers.Serializer):
    """User logout serializer.

    Delete current auth_token from user.
    """

    def save(self, **kwargs):
        """Handle logout request."""
        request = self.context["request"]
        user = request.user
        from contextlib import suppress

        with suppress(AttributeError, Token.DoesNotExist):
            user.auth_token.delete()


class UserCreateSerializer(serializers.Serializer):
    """User create serializer.

    Handle the user creation request data.
    """

    username = serializers.CharField()
    password = serializers.CharField(min_length=8, max_length=64)
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    user_type = serializers.PrimaryKeyRelatedField(queryset=UserType.objects.all())

    def validate(self, data):
        """Check if the user exists."""
        if User.objects.filter(username=data["username"]).exists():
            error_message = "A user with that username already exists."
            raise serializers.ValidationError(error_message)
        if User.objects.filter(email=data["email"]).exists():
            error_message = "A user with that email already exists."
            raise serializers.ValidationError(error_message)
        return data

    def create(self, data):
        """Handle user creation."""
        return User.objects.create_user(
            username=data["username"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            phone_number=data["phone_number"],
            user_type=data["user_type"],
        )
