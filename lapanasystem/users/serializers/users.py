"""Users serializers."""

# Django
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator

# Django REST Framework
from rest_framework import serializers
from rest_framework.authtoken.models import Token

# Models
from lapanasystem.users.models import User


class UserSerializer(serializers.ModelSerializer):
    """User model serializer."""

    user_type = serializers.ChoiceField(choices=User.USER_TYPE_CHOICES)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

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
            "password",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        """Handle user creation."""
        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Handle user update."""
        instance.username = validated_data.get("username", instance.username)
        instance.user_type = validated_data.get("user_type", instance.user_type)
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.email = validated_data.get("email", instance.email)
        instance.phone_number = validated_data.get(
            "phone_number", instance.phone_number
        )
        password = validated_data.get("password", None)
        if password:
            instance.set_password(password)

        instance.save()
        return instance


class UserLoginSerializer(serializers.Serializer):
    """User login serializer.

    Handle the login request data.
    """

    username = serializers.CharField()
    password = serializers.CharField(min_length=8, max_length=64, write_only=True)

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
    password = serializers.CharField(min_length=8, max_length=64, write_only=True)
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    user_type = serializers.ChoiceField(choices=User.USER_TYPE_CHOICES)

    def validate_phone_number(self, value):
        """Check if the phone number is valid."""
        phone_regex = RegexValidator(
            regex=r"^\+?1?\d{9,15}$",
            message=(
                "Phone number must be entered in the format: +999999999. "
                "Up to 15 digits allowed."
            ),
        )
        phone_regex(value)
        return value

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
