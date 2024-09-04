"""Users tests."""

# Pytest
# Utilities
import secrets

import pytest

# Django REST Framework
from rest_framework import status
from rest_framework.test import APIClient

# Models
from lapanasystem.users.models import User
from lapanasystem.users.models import UserType

# Constants
ADMIN_PASSWORD = secrets.token_urlsafe(16)
USER_PASSWORD = secrets.token_urlsafe(16)


@pytest.mark.django_db
def test_create_user():
    """Test create user."""

    client = APIClient()

    admin_user = User.objects.create_superuser(
        username="admin",
        password=ADMIN_PASSWORD,
        email="admin@example.com",
    )
    client.force_authenticate(user=admin_user)

    user_type = UserType.objects.create(name="Admin", description="Administrator role")

    data = {
        "username": "testuser",
        "password": USER_PASSWORD,
        "first_name": "Test",
        "last_name": "User",
        "email": "testuser@example.com",
        "phone_number": "+1234567890",
        "user_type": user_type.id,
    }

    response = client.post("/api/v1/users/create-user/", data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["username"] == "testuser"
    assert response.data["email"] == "testuser@example.com"
    assert User.objects.filter(username="testuser").exists()


@pytest.mark.django_db
def test_user_login():
    """Test user login."""

    client = APIClient()

    user_type = UserType.objects.create(name="Admin", description="Administrator role")

    User.objects.create_user(
        username="testuser",
        password=USER_PASSWORD,
        first_name="Test",
        last_name="User",
        email="testuser@example.com",
        phone_number="+1234567890",
        user_type=user_type,
    )

    data = {
        "username": "testuser",
        "password": USER_PASSWORD,
    }

    response = client.post("/api/v1/users/login/", data)

    assert response.status_code == status.HTTP_201_CREATED
    assert "access_token" in response.data
    assert response.data["user"]["username"] == "testuser"


@pytest.mark.django_db
def test_user_logout(authenticated_client):
    """Test user logout."""

    response = authenticated_client.post("/api/v1/users/logout/")

    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_user_update(authenticated_client, user):
    """Test user update."""

    update_data = {
        "first_name": "UpdatedName",
        "last_name": "UpdatedLastName",
    }

    response = authenticated_client.patch(
        f"/api/v1/users/{user.username}/",
        update_data,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["first_name"] == "UpdatedName"
    assert response.data["last_name"] == "UpdatedLastName"


@pytest.mark.django_db
def test_user_soft_delete(authenticated_client, user):
    """Test user soft delete."""

    response = authenticated_client.delete(f"/api/v1/users/{user.username}/")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    user.refresh_from_db()
    assert user.is_active is False


@pytest.mark.django_db
def test_list_users(authenticated_client):
    """Test list users."""

    response = authenticated_client.get("/api/v1/users/")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1


@pytest.mark.django_db
def test_retrieve_user(authenticated_client, user):
    """Test retrieve user."""

    response = authenticated_client.get(f"/api/v1/users/{user.username}/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["username"] == user.username


@pytest.fixture
def authenticated_client(db):
    """Fixture for an authenticated admin client."""
    client = APIClient()

    admin_user_type = UserType.objects.create(
        name="Administrador",
        description="Admin role",
    )

    admin_user = User.objects.create_user(
        username="adminuser",
        password=ADMIN_PASSWORD,
        first_name="Admin",
        last_name="User",
        email="adminuser@example.com",
        user_type=admin_user_type,
    )

    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def user(db):
    """Fixture for a user."""
    return User.objects.create_user(
        username="testuser",
        password=USER_PASSWORD,
        first_name="Test",
        last_name="User",
        email="testuser@example.com",
    )
