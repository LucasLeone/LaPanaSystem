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

    def test_supplier_name_uniqueness(self, supplier_data):
        """Verify that supplier name uniqueness is enforced."""
        Supplier.objects.create(**supplier_data)
        with pytest.raises(ValidationError) as exc_info:
            duplicate_supplier = Supplier(**supplier_data)
            duplicate_supplier.full_clean()
        assert 'name' in exc_info.value.message_dict

    def test_supplier_name_uniqueness_after_soft_delete(self, supplier_data):
        """Verify that creating a supplier with duplicate name and email after soft deletion is not allowed."""
        supplier = Supplier.objects.create(**supplier_data)
        supplier.is_active = False
        supplier.save()
        duplicate_supplier = Supplier(**supplier_data)
        with pytest.raises(ValidationError) as exc_info:
            duplicate_supplier.full_clean()
        assert 'name' in exc_info.value.message_dict
        assert 'Supplier with this Name already exists.' in exc_info.value.message_dict['name']
        assert 'email' in exc_info.value.message_dict
        assert 'Supplier with this Email already exists.' in exc_info.value.message_dict['email']



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

    def test_duplicate_supplier_name(self, supplier_data):
        """Verify that serializer prevents duplicate supplier names and emails."""
        Supplier.objects.create(**supplier_data)
        serializer = SupplierSerializer(data=supplier_data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors
        assert 'email' in serializer.errors
        # Adjust the expected messages based on the actual serializer output
        expected_name_error = "supplier with this name already exists."
        expected_email_error = "supplier with this email already exists."
        assert serializer.errors['name'][0].lower() == expected_name_error
        assert serializer.errors['email'][0].lower() == expected_email_error

    def test_missing_required_fields(self):
        """Verify that serializer is invalid when required fields are missing."""
        data = {
            "phone_number": "+1234567890",
            "email": "supplier@example.com",
        }
        serializer = SupplierSerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors

    def test_invalid_email(self, supplier_data):
        """Verify that serializer is invalid with incorrect email format."""
        supplier_data['email'] = 'invalid_email'
        serializer = SupplierSerializer(data=supplier_data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors


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
        assert response.data['name'] == supplier_data['name']

    def test_supplier_create_as_seller(self, api_client, seller_user, supplier_data):
        """Verify that a seller user can create a supplier."""
        api_client.force_authenticate(user=seller_user)
        response = api_client.post(self.list_url, data=supplier_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Supplier.objects.count() == 1

    def test_supplier_create_as_delivery(self, api_client, delivery_user, supplier_data):
        """Verify that a delivery user cannot create a supplier."""
        api_client.force_authenticate(user=delivery_user)
        response = api_client.post(self.list_url, data=supplier_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

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
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == supplier_data['name']

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
        assert response.data['name'] == 'New Supplier Name'

    def test_supplier_partial_update(self, api_client, admin_user, supplier_data):
        """Verify that an admin user can partially update a supplier."""
        supplier = Supplier.objects.create(**supplier_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse('api:suppliers-detail', args=[supplier.id])
        response = api_client.patch(url, data={'name': 'Partial Update Supplier'})
        assert response.status_code == status.HTTP_200_OK
        supplier.refresh_from_db()
        assert supplier.name == 'Partial Update Supplier'
        assert response.data['name'] == 'Partial Update Supplier'

    def test_supplier_delete_as_admin(self, api_client, admin_user, supplier_data):
        """Verify that an admin user can soft delete a supplier."""
        supplier = Supplier.objects.create(**supplier_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse('api:suppliers-detail', args=[supplier.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        supplier.refresh_from_db()
        assert not supplier.is_active
        response = api_client.get(self.list_url)
        assert len(response.data['results']) == 0

    def test_supplier_delete_as_seller(self, api_client, seller_user, supplier_data):
        """Verify that a seller user cannot delete a supplier."""
        supplier = Supplier.objects.create(**supplier_data)
        api_client.force_authenticate(user=seller_user)
        url = reverse('api:suppliers-detail', args=[supplier.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        supplier.refresh_from_db()
        assert supplier.is_active

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
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'Supplier One'

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
        assert response.data['results'][0]['name'] == 'Supplier A'
        assert response.data['results'][1]['name'] == 'Supplier B'

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
