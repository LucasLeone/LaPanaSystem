"""Users tests."""

# Django
from django.urls import reverse

# Django REST Framework
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

# Pytest
import pytest
import secrets

# Models
from lapanasystem.users.models import User

# Serializers
from lapanasystem.users.serializers import UserSerializer


# Constants for test passwords
ADMIN_PASSWORD = secrets.token_urlsafe(16)
USER_PASSWORD = secrets.token_urlsafe(16)


# URL Configurations using reverse
CREATE_USER_URL = reverse("api:users-create-user")
LOGIN_URL = reverse("api:users-login")
LOGOUT_URL = reverse("api:users-logout")
USER_DETAIL_URL = lambda username: reverse("api:users-detail", args=[username])
LIST_USERS_URL = reverse("api:users-list")


@pytest.fixture
def admin_user(db):
    """Fixture for creating an admin user."""
    return User.objects.create_superuser(
        username="adminuser",
        password=ADMIN_PASSWORD,
        first_name="Admin",
        last_name="User",
        email="adminuser@example.com",
        user_type=User.ADMIN,
    )


@pytest.fixture
def seller_user(db):
    """Fixture for creating a seller user."""
    return User.objects.create_user(
        username="selleruser",
        password=USER_PASSWORD,
        first_name="Seller",
        last_name="User",
        email="selleruser@example.com",
        user_type=User.SELLER,
    )


@pytest.fixture
def api_client():
    """Fixture for the API client."""
    return APIClient()


@pytest.fixture
def api_client_authenticated_admin(admin_user):
    """Fixture for an API client authenticated as an admin."""
    token, created = Token.objects.get_or_create(user=admin_user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    return client


@pytest.fixture
def api_client_authenticated_seller(seller_user):
    """Fixture for an API client authenticated as a seller."""
    token, created = Token.objects.get_or_create(user=seller_user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    return client


@pytest.fixture
def user(db):
    """Fixture for creating a regular user."""
    return User.objects.create_user(
        username="testuser",
        password=USER_PASSWORD,
        first_name="Test",
        last_name="User",
        email="testuser@example.com",
        phone_number="+1234567890",
        user_type=User.SELLER,
    )


@pytest.mark.django_db
class TestUserAPI:
    """Tests for the Users API."""

    def test_create_user_as_admin(self, api_client_authenticated_admin):
        """Test that an admin can create a new user."""
        data = {
            "username": "newuser",
            "password": "NewPass123",
            "first_name": "New",
            "last_name": "User",
            "email": "newuser@example.com",
            "phone_number": "+19876543210",
            "user_type": "SELLER",
        }

        response = api_client_authenticated_admin.post(CREATE_USER_URL, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username="newuser").exists()
        assert response.data["username"] == "newuser"
        assert response.data["email"] == "newuser@example.com"

    def test_create_user_as_non_admin(self, api_client_authenticated_seller):
        """Test that a non-admin user cannot create a new user."""
        data = {
            "username": "anotheruser",
            "password": "AnotherPass123",
            "first_name": "Another",
            "last_name": "User",
            "email": "anotheruser@example.com",
            "phone_number": "+19876543211",
            "user_type": "SELLER",
        }

        response = api_client_authenticated_seller.post(CREATE_USER_URL, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_user_with_invalid_data(self, api_client_authenticated_admin):
        """Test creating a user with invalid data."""
        data = {
            "username": "",
            "password": "short",
            "first_name": "Invalid",
            "last_name": "User",
            "email": "invalid-email",
            "phone_number": "123",
            "user_type": "INVALID_TYPE",
        }

        response = api_client_authenticated_admin.post(CREATE_USER_URL, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data
        assert "password" in response.data
        assert "email" in response.data
        assert "phone_number" in response.data
        assert "user_type" in response.data

    def test_create_user_duplicate_username(self, api_client_authenticated_admin, user):
        """Test creating a user with a duplicate username."""
        data = {
            "username": user.username,
            "password": "DuplicatePass123",
            "first_name": "Duplicate",
            "last_name": "User",
            "email": "duplicateuser@example.com",
            "phone_number": "+19876543212",
            "user_type": "SELLER",
        }

        response = api_client_authenticated_admin.post(CREATE_USER_URL, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_user_duplicate_email(self, api_client_authenticated_admin, user):
        """Test creating a user with a duplicate email."""
        data = {
            "username": "uniqueusername",
            "password": "UniquePass123",
            "first_name": "Unique",
            "last_name": "User",
            "email": user.email,
            "phone_number": "+19876543213",
            "user_type": "SELLER",
        }

        response = api_client_authenticated_admin.post(CREATE_USER_URL, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_as_active_user(self, api_client, user):
        """Test that an active user can log in."""
        data = {
            "username": user.username,
            "password": USER_PASSWORD,
        }

        response = api_client.post(LOGIN_URL, data)
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.data
        assert response.data["user"]["username"] == user.username

    def test_login_as_inactive_user(self, api_client, user):
        """Test that an inactive user cannot log in."""
        user.is_active = False
        user.save()

        data = {
            "username": user.username,
            "password": USER_PASSWORD,
        }

        response = api_client.post(LOGIN_URL, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data

    def test_login_with_invalid_credentials(self, api_client):
        """Test logging in with invalid credentials."""
        data = {
            "username": "nonexistentuser",
            "password": "WrongPass123",
        }

        response = api_client.post(LOGIN_URL, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["non_field_errors"][0] == "Invalid credentials"

    def test_logout_deletes_token(self, api_client_authenticated_admin, admin_user):
        """Test that logging out deletes the authentication token."""
        user = admin_user
        token = Token.objects.get(user=user)
        assert token is not None

        response = api_client_authenticated_admin.post(LOGOUT_URL)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        with pytest.raises(Token.DoesNotExist):
            Token.objects.get(user=user)

    def test_list_users_as_admin(self, api_client_authenticated_admin, user):
        """Test that an admin can list all users."""
        response = api_client_authenticated_admin.get(LIST_USERS_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == User.objects.filter(is_active=True).count()

    def test_list_users_as_non_admin(self, api_client_authenticated_seller):
        """Test that a non-admin user cannot list all users."""
        response = api_client_authenticated_seller.get(LIST_USERS_URL)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_user_as_admin(self, api_client_authenticated_admin, user):
        """Test that an admin can retrieve a user's details."""
        url = USER_DETAIL_URL(user.username)
        response = api_client_authenticated_admin.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == user.username

    def test_retrieve_user_as_non_admin(self, api_client_authenticated_seller, user):
        """Test that a non-admin user cannot retrieve another user's details."""
        url = USER_DETAIL_URL(user.username)
        response = api_client_authenticated_seller.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_user_as_admin(self, api_client_authenticated_admin, user):
        """Test that an admin can update a user's details."""
        url = USER_DETAIL_URL(user.username)
        update_data = {
            "first_name": "UpdatedName",
            "last_name": "UpdatedLastName",
        }

        response = api_client_authenticated_admin.patch(url, update_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "UpdatedName"
        assert response.data["last_name"] == "UpdatedLastName"

        user.refresh_from_db()
        assert user.first_name == "UpdatedName"
        assert user.last_name == "UpdatedLastName"

    def test_update_user_with_invalid_data(self, api_client_authenticated_admin, user):
        """Test updating a user with invalid data."""
        url = USER_DETAIL_URL(user.username)
        update_data = {
            "email": "invalid-email",
            "phone_number": "invalid-phone",
        }

        response = api_client_authenticated_admin.patch(url, update_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data
        assert "phone_number" in response.data

    def test_update_user_as_non_admin(self, api_client_authenticated_seller, user):
        """Test that a non-admin user cannot update another user's details."""
        url = USER_DETAIL_URL(user.username)
        update_data = {
            "first_name": "HackerName",
        }

        response = api_client_authenticated_seller.patch(url, update_data)
        print(response.data)
        print(response.status_code)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_soft_delete_user_as_admin(self, api_client_authenticated_admin, user):
        """Test that an admin can soft delete a user."""
        url = USER_DETAIL_URL(user.username)
        response = api_client_authenticated_admin.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        user.refresh_from_db()
        assert user.is_active is False

    def test_soft_delete_user_as_non_admin(self, api_client_authenticated_seller, user):
        """Test that a non-admin user cannot soft delete a user."""
        url = USER_DETAIL_URL(user.username)
        response = api_client_authenticated_seller.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        user.refresh_from_db()
        assert user.is_active is True

    def test_soft_deleted_user_cannot_login(self, api_client, user):
        """Test that a soft-deleted user cannot log in."""
        user.is_active = False
        user.save()

        data = {
            "username": user.username,
            "password": USER_PASSWORD,
        }

        response = api_client.post(LOGIN_URL, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data


@pytest.mark.django_db
class TestUserLogout:
    """Tests specifically for user logout functionality."""

    def test_user_logout_success(self, api_client_authenticated_admin, admin_user):
        """Test successful user logout."""
        user = admin_user
        token = Token.objects.get(user=user)
        assert token is not None

        response = api_client_authenticated_admin.post(LOGOUT_URL)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        with pytest.raises(Token.DoesNotExist):
            Token.objects.get(user=user)

    def test_user_logout_without_token(self, api_client_authenticated_admin, admin_user):
        """Test logout when the user does not have a token."""
        user = admin_user
        Token.objects.filter(user=user).delete()

        response = api_client_authenticated_admin.post(LOGOUT_URL)
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestUserPermissions:
    """Tests to ensure proper permissions are enforced."""

    def test_admin_can_retrieve_user(self, api_client_authenticated_admin, user):
        """Test that an admin can retrieve any user's details."""
        url = USER_DETAIL_URL(user.username)
        response = api_client_authenticated_admin.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == user.username

    def test_seller_cannot_retrieve_other_user(self, api_client_authenticated_seller, user):
        """Test that a seller cannot retrieve another user's details."""
        url = USER_DETAIL_URL(user.username)
        response = api_client_authenticated_seller.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_list_users(self, api_client_authenticated_admin, user):
        """Test that an admin can list all active users."""
        response = api_client_authenticated_admin.get(LIST_USERS_URL)
        assert response.status_code == status.HTTP_200_OK
        active_users_count = User.objects.filter(is_active=True).count()
        assert response.data["count"] == active_users_count

    def test_seller_cannot_list_users(self, api_client_authenticated_seller):
        """Test that a seller cannot list all users."""
        response = api_client_authenticated_seller.get(LIST_USERS_URL)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_non_authenticated_user_cannot_access_protected_endpoints(self, api_client, user):
        """Test that unauthenticated users cannot access protected endpoints."""
        response = api_client.get(LIST_USERS_URL)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        url = USER_DETAIL_URL(user.username)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        data = {
            "username": "unauthuser",
            "password": "UnauthPass123",
            "first_name": "Unauth",
            "last_name": "User",
            "email": "unauthuser@example.com",
            "phone_number": "+19876543214",
            "user_type": "SELLER",
        }
        response = api_client.post(CREATE_USER_URL, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_only_admin_can_delete_user(self, api_client_authenticated_admin, api_client_authenticated_seller, user):
        """Test that only an admin can delete a user."""
        admin_response = api_client_authenticated_admin.delete(USER_DETAIL_URL(user.username))
        assert admin_response.status_code == status.HTTP_204_NO_CONTENT
        user.refresh_from_db()
        assert user.is_active is False

        another_user = User.objects.create_user(
            username="anotheruser",
            password="AnotherPass123",
            first_name="Another",
            last_name="User",
            email="anotheruser@example.com",
            phone_number="+19876543215",
            user_type=User.SELLER,
        )
        seller_response = api_client_authenticated_seller.delete(USER_DETAIL_URL(another_user.username))
        assert seller_response.status_code == status.HTTP_403_FORBIDDEN
