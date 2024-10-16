"""Expenses tests."""

# Django
from django.urls import reverse

# Django REST Framework
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APIRequestFactory

# Models
from lapanasystem.expenses.models import ExpenseCategory, Expense, Supplier
from lapanasystem.users.models import User

# Serializers
from lapanasystem.expenses.serializers import ExpenseSerializer

# Utilities
import pytest
from decimal import Decimal


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
def expense_category_data():
    return {
        "name": "Utilities",
        "description": "Monthly utility expenses"
    }


@pytest.fixture
def expense_category(expense_category_data):
    return ExpenseCategory.objects.create(**expense_category_data)


@pytest.fixture
def supplier_data():
    return {
        "name": "Test Supplier",
        "phone_number": "+1234567890",
        "email": "supplier@example.com",
        "address": "123 Supplier St"
    }


@pytest.fixture
def supplier(supplier_data):
    return Supplier.objects.create(**supplier_data)


@pytest.fixture
def expense(admin_user, expense_category):
    return Expense.objects.create(
        user=admin_user,
        amount=Decimal('100.00'),
        description="Default Expense",
        category=expense_category
    )


@pytest.mark.django_db
class TestExpenseCategoryModel:
    def test_category_str(self, expense_category_data):
        category = ExpenseCategory.objects.create(**expense_category_data)
        assert str(category) == category.name

    def test_category_name_uniqueness_after_soft_delete(self, expense_category_data):
        """Verify that a category with the same name can be created after soft deletion."""
        category = ExpenseCategory.objects.create(**expense_category_data)
        category.is_active = False
        category.save()
        new_category = ExpenseCategory(**expense_category_data)
        new_category.full_clean()
        new_category.save()
        assert ExpenseCategory.objects.filter(name=expense_category_data['name']).count() == 2


@pytest.mark.django_db
class TestExpenseModel:
    def test_expense_str(self, expense_category, admin_user):
        expense = Expense.objects.create(
            user=admin_user,
            amount=Decimal('100.50'),
            description="Electricity bill",
            category=expense_category
        )
        assert str(expense) == f"Expense {expense.id}: {expense.amount} by {expense.user.username}"


@pytest.mark.django_db
class TestExpenseSerializer:
    def test_valid_expense_serializer(self, expense_category, admin_user):
        """Verify that the serializer is valid with correct data."""
        data = {
            "amount": "200.00",
            "description": "Office Supplies",
            "category": expense_category.id,
        }
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = admin_user
        serializer = ExpenseSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), serializer.errors
        expense = serializer.save()
        assert expense.amount == Decimal('200.00')
        assert expense.description == data['description']
        assert expense.category == expense_category

    def test_invalid_expense_serializer(self, expense_category, admin_user):
        """Verify that the serializer is invalid with non-numeric amount."""
        data = {
            "amount": "invalid_amount",
            "description": "Office Supplies",
            "category": expense_category.id,
        }
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = admin_user
        serializer = ExpenseSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'amount' in serializer.errors

    def test_missing_required_fields(self, expense_category, admin_user):
        """Verify that the serializer is invalid when required fields are missing."""
        data = {
            "description": "Incomplete Expense",
            "category": expense_category.id,
        }
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = admin_user
        serializer = ExpenseSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'amount' in serializer.errors

    def test_invalid_category_id(self, admin_user):
        """Verify that the serializer is invalid with an invalid category ID."""
        data = {
            "amount": "100.00",
            "description": "Expense with invalid category",
            "category": 9999,  # Assuming this ID does not exist
        }
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = admin_user
        serializer = ExpenseSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'category' in serializer.errors

    def test_invalid_supplier_id(self, expense_category, admin_user):
        """Verify that the serializer is invalid with an invalid supplier ID."""
        data = {
            "amount": "100.00",
            "description": "Expense with invalid supplier",
            "category": expense_category.id,
            "supplier": 9999,  # Assuming this ID does not exist
        }
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = admin_user
        serializer = ExpenseSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'supplier' in serializer.errors

    def test_expense_creation_without_supplier(self, expense_category, admin_user):
        """Verify that an expense can be created without a supplier."""
        data = {
            "amount": "150.00",
            "description": "Expense without supplier",
            "category": expense_category.id,
        }
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = admin_user
        serializer = ExpenseSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), serializer.errors
        expense = serializer.save()
        assert expense.supplier is None

    def test_expense_serializer_includes_nested_details(self, expense_category, admin_user, supplier):
        """Verify that the serializer includes nested category and supplier details."""
        data = {
            "amount": "200.00",
            "description": "Office Supplies",
            "category": expense_category.id,
            "supplier": supplier.id,
        }
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = admin_user
        serializer = ExpenseSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), serializer.errors
        expense = serializer.save()
        serialized_data = ExpenseSerializer(expense).data
        assert 'category_details' in serialized_data
        assert serialized_data['category_details']['id'] == expense_category.id
        assert serialized_data['category_details']['name'] == expense_category.name
        assert 'supplier_details' in serialized_data
        assert serialized_data['supplier_details']['id'] == supplier.id
        assert serialized_data['supplier_details']['name'] == supplier.name


@pytest.mark.django_db
class TestExpenseAPI:
    """Expense API tests."""

    @pytest.fixture(autouse=True)
    def setup_urls(self):
        self.list_url = reverse('api:expenses-list')

    def test_expense_create_as_admin(self, api_client, admin_user, expense_category):
        """Verify that an admin user can create an expense."""
        api_client.force_authenticate(user=admin_user)
        data = {
            "amount": "150.00",
            "description": "New Chairs",
            "category": expense_category.id,
        }
        response = api_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Expense.objects.count() == 1
        expense = Expense.objects.first()
        assert expense.description == data['description']
        assert expense.amount == Decimal(data['amount'])
        assert response.data['category_details']['id'] == expense_category.id

    def test_expense_create_with_invalid_supplier(self, api_client, admin_user, expense_category):
        """Verify that creating an expense with an invalid supplier ID fails."""
        api_client.force_authenticate(user=admin_user)
        data = {
            "amount": "150.00",
            "description": "Expense with invalid supplier",
            "category": expense_category.id,
            "supplier": 9999,  # Assuming this ID does not exist
        }
        response = api_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'supplier' in response.data

    def test_expense_create_as_seller(self, api_client, seller_user, expense_category):
        """Verify that a seller user can create an expense."""
        api_client.force_authenticate(user=seller_user)
        data = {
            "amount": "150.00",
            "description": "New Chairs",
            "category": expense_category.id,
        }
        response = api_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Expense.objects.count() == 1

    def test_expense_create_as_delivery(self, api_client, delivery_user, expense_category):
        """Verify that a delivery user cannot create an expense."""
        api_client.force_authenticate(user=delivery_user)
        data = {
            "amount": "150.00",
            "description": "Unauthorized Expense",
            "category": expense_category.id,
        }
        response = api_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_expense_create_unauthenticated(self, api_client, expense_category):
        """Verify that an unauthenticated user cannot create an expense."""
        data = {
            "amount": "150.00",
            "description": "New Chairs",
            "category": expense_category.id,
        }
        response = api_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_expense_list(self, api_client, admin_user, expense_category):
        """Verify that an admin user can list expenses."""
        Expense.objects.create(
            user=admin_user,
            amount=Decimal('100.00'),
            description="Test Expense",
            category=expense_category
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['description'] == "Test Expense"

    def test_expense_list_as_delivery(self, api_client, delivery_user):
        """Verify that a delivery user cannot list expenses."""
        api_client.force_authenticate(user=delivery_user)
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_expense_retrieve(self, api_client, admin_user, expense_category):
        """Verify that an admin user can retrieve an expense."""
        expense = Expense.objects.create(
            user=admin_user,
            amount=Decimal('100.00'),
            description="Test Expense",
            category=expense_category
        )
        api_client.force_authenticate(user=admin_user)
        url = reverse('api:expenses-detail', args=[expense.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['description'] == "Test Expense"
        assert response.data['category_details']['id'] == expense_category.id

    def test_expense_update(self, api_client, admin_user, expense_category):
        """Verify that an admin user can update an expense."""
        expense = Expense.objects.create(
            user=admin_user,
            amount=Decimal('100.00'),
            description="Test Expense",
            category=expense_category
        )
        api_client.force_authenticate(user=admin_user)
        url = reverse('api:expenses-detail', args=[expense.id])
        data = {
            "amount": "200.00",
            "description": "Updated Expense",
            "category": expense_category.id,
        }
        response = api_client.put(url, data=data)
        assert response.status_code == status.HTTP_200_OK
        expense.refresh_from_db()
        assert expense.amount == Decimal('200.00')
        assert expense.description == "Updated Expense"

    def test_expense_partial_update(self, api_client, admin_user, expense_category):
        """Verify that an admin user can partially update an expense."""
        expense = Expense.objects.create(
            user=admin_user,
            amount=Decimal('100.00'),
            description="Test Expense",
            category=expense_category
        )
        api_client.force_authenticate(user=admin_user)
        url = reverse('api:expenses-detail', args=[expense.id])
        data = {"description": "Partially Updated Expense"}
        response = api_client.patch(url, data=data)
        assert response.status_code == status.HTTP_200_OK
        expense.refresh_from_db()
        assert expense.description == "Partially Updated Expense"

    def test_expense_delete_as_admin(self, api_client, admin_user, expense_category):
        """Verify that an admin user can soft delete an expense."""
        expense = Expense.objects.create(
            user=admin_user,
            amount=Decimal('100.00'),
            description="Test Expense",
            category=expense_category
        )
        api_client.force_authenticate(user=admin_user)
        url = reverse('api:expenses-detail', args=[expense.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        expense.refresh_from_db()
        assert not expense.is_active
        # Verify that the expense is no longer in the list of active expenses
        response = api_client.get(self.list_url)
        assert len(response.data['results']) == 0

    def test_expense_delete_as_seller(self, api_client, seller_user, expense_category):
        """Verify that a seller user cannot delete an expense."""
        expense = Expense.objects.create(
            user=seller_user,
            amount=Decimal('100.00'),
            description="Test Expense",
            category=expense_category
        )
        api_client.force_authenticate(user=seller_user)
        url = reverse('api:expenses-detail', args=[expense.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        expense.refresh_from_db()
        assert expense.is_active

    def test_expense_filter_by_category(self, api_client, admin_user):
        """Verify that an admin user can filter expenses by category."""
        category1 = ExpenseCategory.objects.create(name="Office", description="Office expenses")
        category2 = ExpenseCategory.objects.create(name="Travel", description="Travel expenses")
        Expense.objects.create(
            user=admin_user,
            amount=Decimal('50.00'),
            description="Office Supplies",
            category=category1
        )
        Expense.objects.create(
            user=admin_user,
            amount=Decimal('200.00'),
            description="Flight Tickets",
            category=category2
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {'category': category2.id})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['description'] == "Flight Tickets"

    def test_expense_search(self, api_client, admin_user, expense_category):
        """Verify that an admin user can search expenses by description."""
        Expense.objects.create(
            user=admin_user,
            amount=Decimal('100.00'),
            description="Office Supplies",
            category=expense_category
        )
        Expense.objects.create(
            user=admin_user,
            amount=Decimal('200.00'),
            description="Travel Expenses",
            category=expense_category
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {'search': 'Office'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['description'] == "Office Supplies"

    def test_expense_ordering(self, api_client, admin_user, expense_category):
        """Verify that an admin user can order expenses by amount."""
        Expense.objects.create(
            user=admin_user,
            amount=Decimal('100.00'),
            description="Expense A",
            category=expense_category
        )
        Expense.objects.create(
            user=admin_user,
            amount=Decimal('50.00'),
            description="Expense B",
            category=expense_category
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {'ordering': 'amount'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'][0]['amount'] == '50.00'
        assert response.data['results'][1]['amount'] == '100.00'

    def test_expense_ordering_descending(self, api_client, admin_user, expense_category):
        """Verify that an admin user can order expenses by amount descending."""
        Expense.objects.create(
            user=admin_user,
            amount=Decimal('100.00'),
            description="Expense A",
            category=expense_category
        )
        Expense.objects.create(
            user=admin_user,
            amount=Decimal('50.00'),
            description="Expense B",
            category=expense_category
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {'ordering': '-amount'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'][0]['amount'] == '100.00'
        assert response.data['results'][1]['amount'] == '50.00'

    def test_permissions_create(self, api_client, expense_category):
        """Verify that an unauthenticated user cannot create an expense."""
        data = {
            "amount": "150.00",
            "description": "Unauthorized Expense",
            "category": expense_category.id,
        }
        response = api_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_permissions_list(self, api_client):
        """Verify that an unauthenticated user cannot list expenses."""
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_permissions_update(self, api_client, expense):
        """Verify that an unauthenticated user cannot update an expense."""
        url = reverse('api:expenses-detail', args=[expense.id])
        data = {
            "amount": "200.00",
            "description": "Updated Expense",
            "category": expense.category.id,
        }
        response = api_client.put(url, data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_permissions_delete(self, api_client, expense):
        """Verify that an unauthenticated user cannot delete an expense."""
        url = reverse('api:expenses-detail', args=[expense.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_expense_create_with_supplier(self, api_client, admin_user, expense_category, supplier):
        """Verify that an admin user can create an expense with a supplier."""
        api_client.force_authenticate(user=admin_user)
        data = {
            "amount": "150.00",
            "description": "Purchased Goods",
            "category": expense_category.id,
            "supplier": supplier.id,
        }
        response = api_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        expense = Expense.objects.get()
        assert expense.supplier == supplier
        # Verify that the response includes supplier details
        assert response.data['supplier_details']['id'] == supplier.id
        assert response.data['supplier_details']['name'] == supplier.name


@pytest.mark.django_db
class TestExpenseCategoryAPI:
    """Expense Category API tests."""

    @pytest.fixture(autouse=True)
    def setup_urls(self):
        self.list_url = reverse('api:expense-categories-list')

    def test_category_create_as_admin(self, api_client, admin_user):
        """Verify that an admin user can create a category."""
        api_client.force_authenticate(user=admin_user)
        data = {
            "name": "New Category",
            "description": "Category Description"
        }
        response = api_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert ExpenseCategory.objects.count() == 1
        category = ExpenseCategory.objects.first()
        assert category.name == data['name']
        assert response.data['name'] == data['name']

    def test_category_create_as_seller(self, api_client, seller_user):
        """Verify that a seller user can create a category."""
        api_client.force_authenticate(user=seller_user)
        data = {
            "name": "Seller Category",
            "description": "Seller's Category"
        }
        response = api_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_category_create_as_delivery(self, api_client, delivery_user):
        """Verify that a delivery user cannot create a category."""
        api_client.force_authenticate(user=delivery_user)
        data = {
            "name": "Unauthorized Category",
            "description": "Should not be created"
        }
        response = api_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_category_delete_as_admin(self, api_client, admin_user, expense_category):
        """Verify that an admin user can soft delete a category."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('api:expense-categories-detail', args=[expense_category.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        expense_category.refresh_from_db()
        assert not expense_category.is_active
        # Verify that the category is no longer in the list of active categories
        response = api_client.get(self.list_url)
        assert len(response.data['results']) == 0

    def test_category_delete_as_seller(self, api_client, seller_user, expense_category):
        """Verify that a seller user cannot delete a category."""
        api_client.force_authenticate(user=seller_user)
        url = reverse('api:expense-categories-detail', args=[expense_category.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        expense_category.refresh_from_db()
        assert expense_category.is_active

    def test_category_name_uniqueness(self, api_client, admin_user):
        """Verify that category name uniqueness is enforced."""
        api_client.force_authenticate(user=admin_user)
        data = {
            "name": "Unique Category",
            "description": "First instance"
        }
        response = api_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        response = api_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data

    def test_category_name_uniqueness_after_soft_delete(self, api_client, admin_user):
        """Verify that a category with the same name can be created after soft deletion."""
        api_client.force_authenticate(user=admin_user)
        data = {
            "name": "Soft Deleted Category",
            "description": "Will be soft deleted"
        }
        response = api_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        category_id = response.data['id']
        # Soft delete the category
        url = reverse('api:expense-categories-detail', args=[category_id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        # Create a new category with the same name
        response = api_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
