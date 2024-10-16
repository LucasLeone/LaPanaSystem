"""Customers tests."""

# Django
from django.urls import reverse

# Django REST Framework
from rest_framework.test import APIClient
from rest_framework import status

# Models
from lapanasystem.customers.models import Customer
from lapanasystem.users.models import User

# Serializers
from lapanasystem.customers.serializers import CustomerSerializer

# Utilities
import pytest


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
        first_name="Admin",
        last_name="User",
        user_type="ADMIN",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def seller_user():
    return User.objects.create_user(
        username="seller",
        email="seller@example.com",
        password="sellerpass123",
        first_name="Seller",
        last_name="User",
        user_type="SELLER",
    )


@pytest.fixture
def delivery_user():
    return User.objects.create_user(
        username="delivery",
        email="delivery@example.com",
        password="deliverypass123",
        first_name="Delivery",
        last_name="User",
        user_type="DELIVERY",
    )


@pytest.fixture
def customer_data():
    return {
        "name": "John Doe",
        "email": "johndoe@example.com",
        "phone_number": "+1234567890",
        "address": "123 Main St",
        "customer_type": Customer.MINORISTA,
    }


@pytest.mark.django_db
class TestCustomerModel:
    def test_customer_str(self, customer_data):
        """Verifies that the __str__ method returns the correct format."""
        customer = Customer.objects.create(**customer_data)
        assert str(customer) == f"{customer.name} - ({customer.customer_type})"

    def test_customer_save_lowercase_email(self, customer_data):
        """Verifies that the email is saved in lowercase."""
        customer_data["email"] = "JohnDoe@EXAMPLE.com"
        customer = Customer.objects.create(**customer_data)
        assert customer.email == "johndoe@example.com"


@pytest.mark.django_db
class TestCustomerSerializer:
    def test_valid_customer_serializer(self, customer_data):
        """Verifies that the serializer is valid with correct data."""
        serializer = CustomerSerializer(data=customer_data)
        assert serializer.is_valid()
        customer = serializer.save()
        assert customer.name == customer_data["name"]
        assert customer.email == customer_data["email"]
        assert customer.phone_number == customer_data["phone_number"]
        assert customer.address == customer_data["address"]
        assert customer.customer_type == customer_data["customer_type"]

    def test_invalid_email(self, customer_data):
        """Verifies that the serializer is invalid with an incorrect email."""
        customer_data["email"] = "invalid_email"
        serializer = CustomerSerializer(data=customer_data)
        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_missing_address_for_mayorista(self, customer_data):
        """Verifies that an address is required for wholesale customers."""
        customer_data["customer_type"] = Customer.MAYORISTA
        customer_data["address"] = ""
        serializer = CustomerSerializer(data=customer_data)
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors
        assert (
            serializer.errors["non_field_errors"][0]
            == "Los clientes mayoristas deben tener una dirección."
        )

    def test_invalid_phone_number(self, customer_data):
        """Verifies that the serializer is invalid with an incorrect phone number."""
        customer_data["phone_number"] = "12345"
        serializer = CustomerSerializer(data=customer_data)
        assert not serializer.is_valid()
        assert "phone_number" in serializer.errors

    def test_valid_phone_number(self, customer_data):
        """Verifies that the serializer is valid with a correct phone number."""
        customer_data["phone_number"] = "+19876543210"
        serializer = CustomerSerializer(data=customer_data)
        assert serializer.is_valid()

    def test_invalid_customer_type(self, customer_data):
        """Verifies that the serializer is invalid with an incorrect customer type."""
        customer_data["customer_type"] = "invalid_type"
        serializer = CustomerSerializer(data=customer_data)
        assert not serializer.is_valid()
        assert "customer_type" in serializer.errors


@pytest.mark.django_db
class TestCustomerAPI:
    """Customer API tests."""

    @pytest.fixture(autouse=True)
    def setup_urls(self):
        self.list_url = reverse("api:customers-list")

    def test_customer_create_as_admin(self, api_client, admin_user, customer_data):
        """Verifies that an admin user can create a customer."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(self.list_url, data=customer_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Customer.objects.count() == 1
        customer = Customer.objects.first()
        assert customer.name == customer_data["name"]
        assert response.data["id"] == customer.id
        assert response.data["email"] == customer_data["email"]

    def test_customer_create_as_seller(self, api_client, seller_user, customer_data):
        """Verifies that a seller user can create a customer."""
        api_client.force_authenticate(user=seller_user)
        response = api_client.post(self.list_url, data=customer_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Customer.objects.count() == 1
        customer = Customer.objects.first()
        assert customer.name == customer_data["name"]
        assert response.data["id"] == customer.id

    def test_customer_create_as_delivery(self, api_client, delivery_user, customer_data):
        """Verifies that a delivery user cannot create a customer."""
        api_client.force_authenticate(user=delivery_user)
        response = api_client.post(self.list_url, data=customer_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_customer_create_unauthenticated(self, api_client, customer_data):
        """Verifies that an unauthenticated user cannot create a customer."""
        response = api_client.post(self.list_url, data=customer_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_customer_list(self, api_client, admin_user, customer_data):
        """Verifies that an admin user can list customers."""
        Customer.objects.create(**customer_data)
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == customer_data["name"]

    def test_customer_retrieve(self, api_client, admin_user, customer_data):
        """Verifies that an admin user can retrieve a customer's details."""
        customer = Customer.objects.create(**customer_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:customers-detail", args=[customer.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == customer_data["name"]
        assert response.data["email"] == customer_data["email"]

    def test_customer_update(self, api_client, admin_user, customer_data):
        """Verifies that an admin user can update a customer."""
        customer = Customer.objects.create(**customer_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:customers-detail", args=[customer.id])
        updated_data = customer_data.copy()
        updated_data["name"] = "Jane Doe"
        response = api_client.put(url, data=updated_data)
        assert response.status_code == status.HTTP_200_OK
        customer.refresh_from_db()
        assert customer.name == "Jane Doe"
        assert response.data["name"] == "Jane Doe"
        assert customer.email == customer_data["email"]

    def test_customer_partial_update(self, api_client, admin_user, customer_data):
        """Verifies that an admin user can partially update a customer."""
        customer = Customer.objects.create(**customer_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:customers-detail", args=[customer.id])
        response = api_client.patch(url, data={"name": "Jane Doe"})
        assert response.status_code == status.HTTP_200_OK
        customer.refresh_from_db()
        assert customer.name == "Jane Doe"
        assert customer.email == customer_data["email"]

    def test_customer_delete_as_admin(self, api_client, admin_user, customer_data):
        """Verifies that an admin user can delete (soft delete) a customer."""
        customer = Customer.objects.create(**customer_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:customers-detail", args=[customer.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        customer.refresh_from_db()
        assert not customer.is_active
        response = api_client.get(self.list_url)
        assert len(response.data["results"]) == 0
        assert response.data["results"] == []

    def test_customer_delete_as_seller(self, api_client, seller_user, customer_data):
        """Verifies that a seller user cannot delete a customer."""
        customer = Customer.objects.create(**customer_data)
        api_client.force_authenticate(user=seller_user)
        url = reverse("api:customers-detail", args=[customer.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        customer.refresh_from_db()
        assert customer.is_active

    def test_customer_filter_by_type(self, api_client, admin_user):
        """Verifies that an admin user can filter customers by type."""
        Customer.objects.create(
            name="Retail Customer",
            email="retail@example.com",
            customer_type=Customer.MINORISTA,
        )
        Customer.objects.create(
            name="Wholesale Customer",
            email="wholesale@example.com",
            customer_type=Customer.MAYORISTA,
            address="456 Market St",
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {"customer_type": Customer.MAYORISTA})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["email"] == "wholesale@example.com"

    def test_customer_search(self, api_client, admin_user):
        """Verifies that an admin user can search customers by name."""
        Customer.objects.create(
            name="John Smith",
            email="johnsmith@example.com",
        )
        Customer.objects.create(
            name="Jane Doe",
            email="janedoe@example.com",
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {"search": "Jane"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Jane Doe"

    def test_customer_ordering(self, api_client, admin_user):
        """Verifies that an admin user can order customers by name."""
        Customer.objects.create(
            name="B Customer",
            email="bcustomer@example.com",
        )
        Customer.objects.create(
            name="A Customer",
            email="acustomer@example.com",
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {"ordering": "name"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["name"] == "A Customer"
        assert response.data["results"][1]["name"] == "B Customer"

    def test_customer_ordering_descending(self, api_client, admin_user):
        """Verifies that an admin user can order customers by name descending."""
        Customer.objects.create(
            name="B Customer",
            email="bcustomer@example.com",
        )
        Customer.objects.create(
            name="A Customer",
            email="acustomer@example.com",
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {"ordering": "-name"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["name"] == "B Customer"
        assert response.data["results"][1]["name"] == "A Customer"

    def test_permissions_create(self, api_client, customer_data):
        """Verifies that an unauthenticated user cannot create a customer."""
        response = api_client.post(self.list_url, data=customer_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_permissions_list(self, api_client):
        """Verifies that an unauthenticated user cannot list customers."""
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_permissions_update(self, api_client, customer_data):
        """Verifies that an unauthenticated user cannot update a customer."""
        customer = Customer.objects.create(**customer_data)
        url = reverse("api:customers-detail", args=[customer.id])
        response = api_client.put(url, data=customer_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_permissions_delete(self, api_client, customer_data):
        """Verifies that an unauthenticated user cannot delete a customer."""
        customer = Customer.objects.create(**customer_data)
        url = reverse("api:customers-detail", args=[customer.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        "email, is_valid",
        [
            ("valid.email@example.com", True),
            ("another.valid@example.co.uk", True),
            ("invalid_email", False),
            ("invalid@.com", False),
            ("invalid@com", False),
            ("@example.com", False),
            ("user@domain.com", True),
        ],
    )
    def test_email_validation(self, api_client, admin_user, customer_data, email, is_valid):
        """Verifies the validation of different email formats."""
        customer_data["email"] = email
        serializer = CustomerSerializer(data=customer_data)
        if is_valid:
            assert serializer.is_valid(), f"El email {email} debería ser válido."
        else:
            assert not serializer.is_valid(), f"El email {email} debería ser inválido."
            assert "email" in serializer.errors
