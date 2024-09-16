"""Suppliers tests."""

# Django
from django.urls import reverse
from django.core.exceptions import ValidationError

# Django REST Framework
from rest_framework.test import APIClient
from rest_framework import status

# Models
from lapanasystem.expenses.models import Supplier
from lapanasystem.users.models import User

# Serializers
from lapanasystem.expenses.serializers import SupplierSerializer

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
        is_superuser=True
    )


@pytest.fixture
def seller_user():
    return User.objects.create_user(
        username="seller",
        email="seller@example.com",
        password="sellerpass123",
        first_name="Seller",
        last_name="User",
        user_type="SELLER"
    )


@pytest.fixture
def supplier_data():
    return {
        "name": "ABC Supplies",
        "phone_number": "+1234567890",
        "email": "supplier@example.com",
        "address": "123 Supplier St"
    }


@pytest.fixture
def supplier(supplier_data):
    return Supplier.objects.create(**supplier_data)


@pytest.mark.django_db
class TestSupplierModel:
    def test_supplier_str(self, supplier_data):
        supplier = Supplier.objects.create(**supplier_data)
        assert str(supplier) == supplier.name

    def test_supplier_phone_number_validation(self, supplier_data):
        supplier_data['phone_number'] = 'invalid_phone'
        supplier = Supplier(**supplier_data)
        with pytest.raises(ValidationError) as exc_info:
            supplier.full_clean()
        assert 'Phone number must be entered in the format' in str(exc_info.value)


@pytest.mark.django_db
class TestSupplierSerializer:
    def test_valid_supplier_serializer(self, supplier_data):
        serializer = SupplierSerializer(data=supplier_data)
        assert serializer.is_valid(), serializer.errors
        supplier = serializer.save()
        assert supplier.name == supplier_data['name']
        assert supplier.phone_number == supplier_data['phone_number']
        assert supplier.email == supplier_data['email']
        assert supplier.address == supplier_data['address']

    def test_invalid_supplier_serializer(self, supplier_data):
        supplier_data['phone_number'] = 'invalid_phone'
        serializer = SupplierSerializer(data=supplier_data)
        assert not serializer.is_valid()
        assert 'phone_number' in serializer.errors


@pytest.mark.django_db
class TestSupplierAPI:
    """Supplier API tests."""

    @pytest.fixture(autouse=True)
    def setup_urls(self):
        self.list_url = reverse('api:suppliers-list')

    def test_supplier_create_as_admin(self, api_client, admin_user, supplier_data):
        """Verify that an admin user can create a supplier."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(self.list_url, data=supplier_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Supplier.objects.count() == 1
        supplier = Supplier.objects.first()
        assert supplier.name == supplier_data['name']

    def test_supplier_create_as_seller(self, api_client, seller_user, supplier_data):
        """Verify that a seller user can create a supplier."""
        api_client.force_authenticate(user=seller_user)
        response = api_client.post(self.list_url, data=supplier_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Supplier.objects.count() == 1

    def test_supplier_create_unauthenticated(self, api_client, supplier_data):
        """Verify that an unauthenticated user cannot create a supplier."""
        response = api_client.post(self.list_url, data=supplier_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_supplier_list(self, api_client, admin_user, supplier_data):
        """Verify that an admin user can list suppliers."""
        Supplier.objects.create(**supplier_data)
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_supplier_retrieve(self, api_client, admin_user, supplier_data):
        """Verify that an admin user can retrieve a supplier."""
        supplier = Supplier.objects.create(**supplier_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse('api:suppliers-detail', args=[supplier.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == supplier_data['name']

    def test_supplier_update(self, api_client, admin_user, supplier_data):
        """Verify that an admin user can update a supplier."""
        supplier = Supplier.objects.create(**supplier_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse('api:suppliers-detail', args=[supplier.id])
        updated_data = supplier_data.copy()
        updated_data['name'] = 'New Supplier Name'
        response = api_client.put(url, data=updated_data)
        assert response.status_code == status.HTTP_200_OK
        supplier.refresh_from_db()
        assert supplier.name == 'New Supplier Name'

    def test_supplier_partial_update(self, api_client, admin_user, supplier_data):
        """Verify that an admin user can partially update a supplier."""
        supplier = Supplier.objects.create(**supplier_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse('api:suppliers-detail', args=[supplier.id])
        response = api_client.patch(url, data={'name': 'Partial Update Supplier'})
        assert response.status_code == status.HTTP_200_OK
        supplier.refresh_from_db()
        assert supplier.name == 'Partial Update Supplier'

    def test_supplier_delete_as_admin(self, api_client, admin_user, supplier_data):
        """Verify that an admin user can soft delete a supplier."""
        supplier = Supplier.objects.create(**supplier_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse('api:suppliers-detail', args=[supplier.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        supplier.refresh_from_db()
        assert not supplier.is_active

    def test_supplier_delete_as_seller(self, api_client, seller_user, supplier_data):
        """Verify that a seller user cannot delete a supplier."""
        supplier = Supplier.objects.create(**supplier_data)
        api_client.force_authenticate(user=seller_user)
        url = reverse('api:suppliers-detail', args=[supplier.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_supplier_search(self, api_client, admin_user):
        """Verify that an admin user can search suppliers by name."""
        Supplier.objects.create(
            name="Supplier One",
            phone_number="+1234567890",
            email="one@example.com"
        )
        Supplier.objects.create(
            name="Supplier Two",
            phone_number="+0987654321",
            email="two@example.com"
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {'search': 'One'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == 'Supplier One'

    def test_supplier_ordering(self, api_client, admin_user):
        """Verify that an admin user can order suppliers by name."""
        Supplier.objects.create(
            name="Supplier B",
            phone_number="+1234567890",
            email="b@example.com"
        )
        Supplier.objects.create(
            name="Supplier A",
            phone_number="+0987654321",
            email="a@example.com"
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {'ordering': 'name'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]['name'] == 'Supplier A'
        assert response.data[1]['name'] == 'Supplier B'

    def test_permissions_create(self, api_client, supplier_data):
        """Verify that an unauthenticated user cannot create a supplier."""
        response = api_client.post(self.list_url, data=supplier_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_permissions_list(self, api_client):
        """Verify that an unauthenticated user cannot list suppliers."""
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_permissions_update(self, api_client, supplier_data):
        """Verify that an unauthenticated user cannot update a supplier."""
        supplier = Supplier.objects.create(**supplier_data)
        url = reverse('api:suppliers-detail', args=[supplier.id])
        response = api_client.put(url, data=supplier_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_permissions_delete(self, api_client, supplier_data):
        """Verify that an unauthenticated user cannot delete a supplier."""
        supplier = Supplier.objects.create(**supplier_data)
        url = reverse('api:suppliers-detail', args=[supplier.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
