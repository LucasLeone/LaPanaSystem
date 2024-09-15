"""Customers tests."""

# Django
from django.urls import reverse

# Django REST Framework
from rest_framework.test import APIClient
from rest_framework import status

# Models
from lapanasystem.customers.models import Customer
from lapanasystem.users.models import User, UserType

# Serializers
from lapanasystem.customers.serializers import CustomerSerializer

# Utilities
import pytest


@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user_type_admin():
    return UserType.objects.create(name="Administrador", description="Admin user")

@pytest.fixture
def user_type_seller():
    return UserType.objects.create(name="Vendedor", description="Seller user")

@pytest.fixture
def admin_user(user_type_admin):
    return User.objects.create_user(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
        first_name="Admin",
        last_name="User",
        user_type=user_type_admin,
        is_staff=True,
        is_superuser=True
    )

@pytest.fixture
def seller_user(user_type_seller):
    return User.objects.create_user(
        username="seller",
        email="seller@example.com",
        password="sellerpass123",
        first_name="Seller",
        last_name="User",
        user_type=user_type_seller
    )

@pytest.fixture
def customer_data():
    return {
        "name": "John Doe",
        "email": "johndoe@example.com",
        "phone_number": "+1234567890",
        "address": "123 Main St",
        "customer_type": "minorista"
    }

@pytest.mark.django_db
class TestCustomerModel:
    def test_customer_str(self, customer_data):
        customer = Customer.objects.create(**customer_data)
        assert str(customer) == f"{customer.name} ({customer.email})"

    def test_customer_save_lowercase_email(self, customer_data):
        customer_data['email'] = 'JohnDoe@EXAMPLE.com'
        customer = Customer.objects.create(**customer_data)
        assert customer.email == 'johndoe@example.com'

@pytest.mark.django_db
class TestCustomerSerializer:
    def test_valid_customer_serializer(self, customer_data):
        serializer = CustomerSerializer(data=customer_data)
        assert serializer.is_valid()
        customer = serializer.save()
        assert customer.name == customer_data['name']
        assert customer.email == customer_data['email']
        assert customer.phone_number == customer_data['phone_number']
        assert customer.address == customer_data['address']
        assert customer.customer_type == customer_data['customer_type']

    def test_invalid_email(self, customer_data):
        customer_data['email'] = 'invalid_email'
        serializer = CustomerSerializer(data=customer_data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_missing_address_for_mayorista(self, customer_data):
        customer_data['customer_type'] = 'mayorista'
        customer_data['address'] = ''
        serializer = CustomerSerializer(data=customer_data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors
        assert serializer.errors['non_field_errors'][0] == 'Los clientes mayoristas deben tener una dirección.'

@pytest.mark.django_db
class TestCustomerAPI:
    """Customer API tests."""

    @pytest.fixture(autouse=True)
    def setup_urls(self):
        self.list_url = reverse('api:customers-list')

    def test_customer_create_as_admin(self, api_client, admin_user, customer_data):
        """Verify that an admin user can create a customer."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(self.list_url, data=customer_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Customer.objects.count() == 1
        customer = Customer.objects.first()
        assert customer.name == customer_data['name']

    def test_customer_create_as_seller(self, api_client, seller_user, customer_data):
        """Verify that a seller user can create a customer."""
        api_client.force_authenticate(user=seller_user)
        response = api_client.post(self.list_url, data=customer_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Customer.objects.count() == 1

    def test_customer_create_unauthenticated(self, api_client, customer_data):
        """Verify that an unauthenticated user cannot create a customer."""
        response = api_client.post(self.list_url, data=customer_data)
        print(f"Response status code: {response.status_code}")
        print(f"Response data: {response.data}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_customer_list(self, api_client, admin_user, customer_data):
        """Verify that an admin user can list customers."""
        Customer.objects.create(**customer_data)
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_customer_retrieve(self, api_client, admin_user, customer_data):
        """Verify that an admin user can retrieve a customer."""
        customer = Customer.objects.create(**customer_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse('api:customers-detail', args=[customer.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == customer_data['name']

    def test_customer_update(self, api_client, admin_user, customer_data):
        """Verify that an admin user can update a customer."""
        customer = Customer.objects.create(**customer_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse('api:customers-detail', args=[customer.id])
        updated_data = customer_data.copy()
        updated_data['name'] = 'Jane Doe'
        response = api_client.put(url, data=updated_data)
        assert response.status_code == status.HTTP_200_OK
        customer.refresh_from_db()
        assert customer.name == 'Jane Doe'

    def test_customer_partial_update(self, api_client, admin_user, customer_data):
        """Verify that an admin user can partially update a customer."""
        customer = Customer.objects.create(**customer_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse('api:customers-detail', args=[customer.id])
        response = api_client.patch(url, data={'name': 'Jane Doe'})
        assert response.status_code == status.HTTP_200_OK
        customer.refresh_from_db()
        assert customer.name == 'Jane Doe'

    def test_customer_delete_as_admin(self, api_client, admin_user, customer_data):
        """Verify that an admin user can soft delete a customer."""
        customer = Customer.objects.create(**customer_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse('api:customers-detail', args=[customer.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        customer.refresh_from_db()
        assert not customer.is_active

    def test_customer_delete_as_seller(self, api_client, seller_user, customer_data):
        """Verify that a seller user cannot delete a customer."""
        customer = Customer.objects.create(**customer_data)
        api_client.force_authenticate(user=seller_user)
        url = reverse('api:customers-detail', args=[customer.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_customer_filter_by_type(self, api_client, admin_user):
        """Verify that an admin user can filter customers by type."""
        Customer.objects.create(
            name="Retail Customer",
            email="retail@example.com",
            customer_type=Customer.MINORISTA
        )
        Customer.objects.create(
            name="Wholesale Customer",
            email="wholesale@example.com",
            customer_type=Customer.MAYORISTA,
            address="456 Market St"
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {'customer_type': Customer.MAYORISTA})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['email'] == 'wholesale@example.com'

    def test_customer_search(self, api_client, admin_user):
        """Verify that an admin user can search customers by name."""
        Customer.objects.create(
            name="John Smith",
            email="johnsmith@example.com",
        )
        Customer.objects.create(
            name="Jane Doe",
            email="janedoe@example.com",
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {'search': 'Jane'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == 'Jane Doe'

    def test_customer_ordering(self, api_client, admin_user):
        """Verify that an admin user can order customers by name."""
        Customer.objects.create(
            name="B Customer",
            email="bcustomer@example.com",
        )
        Customer.objects.create(
            name="A Customer",
            email="acustomer@example.com",
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {'ordering': 'name'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]['name'] == 'A Customer'
        assert response.data[1]['name'] == 'B Customer'

    def test_permissions_create(self, api_client, customer_data):
        """Verify that an unauthenticated user cannot create a customer."""
        response = api_client.post(self.list_url, data=customer_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_permissions_list(self, api_client):
        """Verify that an unauthenticated user cannot list customers."""
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_permissions_update(self, api_client, customer_data):
        """Verify that an unauthenticated user cannot update a customer."""
        customer = Customer.objects.create(**customer_data)
        url = reverse('api:customers-detail', args=[customer.id])
        response = api_client.put(url, data=customer_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_permissions_delete(self, api_client, customer_data):
        """Verify that an unauthenticated user cannot delete a customer."""
        customer = Customer.objects.create(**customer_data)
        url = reverse('api:customers-detail', args=[customer.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
