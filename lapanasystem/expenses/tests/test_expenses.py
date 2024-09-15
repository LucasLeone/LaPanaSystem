"""Expenses tests."""

# Django
from django.urls import reverse

# Django REST Framework
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APIRequestFactory

# Models
from lapanasystem.expenses.models import ExpenseCategory, Expense
from lapanasystem.users.models import User, UserType

# Serializers
from lapanasystem.expenses.serializers import ExpenseSerializer

# Utilities
import pytest
from decimal import Decimal


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
def expense_category_data():
    return {
        "name": "Utilities",
        "description": "Monthly utility expenses"
    }


@pytest.fixture
def expense_category(expense_category_data):
    return ExpenseCategory.objects.create(**expense_category_data)


@pytest.mark.django_db
class TestExpenseCategoryModel:
    def test_category_str(self, expense_category_data):
        category = ExpenseCategory.objects.create(**expense_category_data)
        assert str(category) == category.name


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
        assert len(response.data) == 1

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
        assert response.status_code == status.HTTP_204_NO_CONTENT
        expense.refresh_from_db()
        assert not expense.is_active

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
        assert len(response.data) == 1
        assert response.data[0]['description'] == "Flight Tickets"

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
        assert len(response.data) == 1
        assert response.data[0]['description'] == "Office Supplies"

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
        assert response.data[0]['amount'] == '50.00'
        assert response.data[1]['amount'] == '100.00'

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

    def test_permissions_update(self, api_client, admin_user, expense_category):
        """Verify that an unauthenticated user cannot update an expense."""
        expense = Expense.objects.create(
            user=admin_user,
            amount=Decimal('100.00'),
            description="Test Expense",
            category=expense_category
        )
        url = reverse('api:expenses-detail', args=[expense.id])
        data = {
            "amount": "200.00",
            "description": "Updated Expense",
            "category": expense_category.id,
        }
        response = api_client.put(url, data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_permissions_delete(self, api_client, admin_user, expense_category):
        """Verify that an unauthenticated user cannot delete an expense."""
        expense = Expense.objects.create(
            user=admin_user,
            amount=Decimal('100.00'),
            description="Test Expense",
            category=expense_category
        )
        url = reverse('api:expenses-detail', args=[expense.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
