"""Sales tests."""

# Django
from django.urls import reverse
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

# Django REST Framework
from rest_framework.test import APIClient
from rest_framework import status

# Models
from lapanasystem.sales.models import Sale, SaleDetail, StateChange, Return, ReturnDetail
from lapanasystem.products.models import Product, ProductCategory, ProductBrand
from lapanasystem.customers.models import Customer
from lapanasystem.users.models import User

# Serializers
from lapanasystem.sales.serializers import (
    SaleSerializer,
    SaleDetailSerializer,
    StateChangeSerializer,
    ReturnSerializer,
    ReturnDetailSerializer,
    PartialChargeSerializer,
    FastSaleSerializer,
)

# Utilities
import pytest
from decimal import Decimal
from django.utils import timezone


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
def category():
    return ProductCategory.objects.create(name="Beverages", description="Drinks and beverages")


@pytest.fixture
def brand():
    return ProductBrand.objects.create(name="Coca Cola", description="Coca Cola brand")


@pytest.fixture
def product(category, brand):
    return Product.objects.create(
        barcode="1234567890123",
        name="Coca Cola 1L",
        retail_price=Decimal("1.50"),
        wholesale_price=Decimal("1.20"),
        weight=Decimal("1.0"),
        weight_unit="kg",
        description="1 liter bottle of Coca Cola",
        category=category,
        brand=brand,
    )


@pytest.fixture
def customer():
    return Customer.objects.create(
        name="John Doe",
        email="john.doe@example.com",
        phone_number="+12345678901",
        address="123 Main St",
        customer_type=Customer.MINORISTA,
    )


@pytest.fixture
def sale_data(customer, admin_user):
    return {
        "user": admin_user,
        "customer": customer,
        "date": timezone.now(),
        "total": Decimal("10.00"),
        "total_collected": Decimal("10.00"),
        "sale_type": Sale.MINORISTA,
        "payment_method": Sale.EFECTIVO,
        "needs_delivery": False,
    }


@pytest.fixture
def sale(sale_data):
    return Sale.objects.create(**sale_data)


@pytest.fixture
def sale_detail_data(product):
    return {
        "product": product,
        "quantity": Decimal("2.0"),
        "price": product.retail_price,
    }


@pytest.fixture
def sale_detail(sale, sale_detail_data):
    return SaleDetail.objects.create(sale=sale, **sale_detail_data)


@pytest.fixture
def state_change(sale):
    return StateChange.objects.create(sale=sale, state=StateChange.COBRADA)


@pytest.fixture
def return_data(customer, admin_user, sale):
    return {
        "user": admin_user,
        "sale": sale,
        "date": timezone.now(),
        "total": Decimal("2.00"),
    }


@pytest.fixture
def return_order(return_data):
    return Return.objects.create(**return_data)


@pytest.fixture
def return_detail_data(product):
    return {
        "product": product,
        "quantity": Decimal("1.0"),
        "price": product.wholesale_price,
    }


@pytest.fixture
def return_detail(return_order, return_detail_data):
    return ReturnDetail.objects.create(return_order=return_order, **return_detail_data)


@pytest.mark.django_db
class TestSaleModel:
    def test_sale_str(self, sale, customer):
        sale_str = str(sale)
        assert sale_str == f"{customer} - {sale.total}"

    def test_sale_calculate_total(self, sale, sale_detail_data):
        sale_detail = SaleDetail.objects.create(sale=sale, **sale_detail_data)
        sale.calculate_total()
        assert sale.total == sale_detail.price * sale_detail.quantity

    def test_sale_get_state(self, sale, state_change):
        state = sale.get_state()
        assert state == state_change.state

    def test_sale_save_date_auto_now(self, sale_data):
        sale_data.pop("date", None)
        sale = Sale.objects.create(**sale_data)
        assert sale.date is not None


@pytest.mark.django_db
class TestSaleDetailModel:
    def test_sale_detail_str(self, sale, sale_detail_data, product):
        sale_detail = SaleDetail.objects.create(sale=sale, **sale_detail_data)
        assert str(sale_detail) == f"{sale} - {product}"

    def test_sale_detail_get_subtotal(self, sale, sale_detail_data):
        sale_detail = SaleDetail.objects.create(sale=sale, **sale_detail_data)
        assert sale_detail.get_subtotal() == sale_detail.price * sale_detail.quantity


@pytest.mark.django_db
class TestStateChangeModel:
    def test_state_change_str(self, sale, state_change):
        expected_str = f"{state_change.get_state_display()} - Sale ID: {sale.id}"
        assert str(state_change) == expected_str


@pytest.mark.django_db
class TestReturnModel:
    def test_return_str(self, return_order, customer):
        return_str = str(return_order)
        assert return_str == f"{customer} - {return_order.date}"

    def test_return_calculate_total(self, return_order, return_detail_data):
        return_detail = ReturnDetail.objects.create(return_order=return_order, **return_detail_data)
        return_order.calculate_total()
        assert return_order.total == return_detail.price * return_detail.quantity


@pytest.mark.django_db
class TestReturnDetailModel:
    def test_return_detail_str(self, return_order, return_detail_data, product):
        return_detail = ReturnDetail.objects.create(return_order=return_order, **return_detail_data)
        assert str(return_detail) == f"{return_order} - {product}"

    def test_return_detail_get_subtotal(self, return_order, return_detail_data):
        return_detail = ReturnDetail.objects.create(return_order=return_order, **return_detail_data)
        assert return_detail.get_subtotal() == return_detail.price * return_detail.quantity


@pytest.mark.django_db
class TestSaleSerializer:
    def test_valid_sale_serializer(self, sale_data, customer, admin_user):
        serializer = SaleSerializer(data={
            "customer": customer.id,
            "sale_type": sale_data["sale_type"],
            "payment_method": sale_data["payment_method"],
            "needs_delivery": sale_data["needs_delivery"],
        }, context={"request": None})
        assert serializer.is_valid(), serializer.errors

    def test_invalid_sale_serializer_no_details(self, sale_data):
        serializer = SaleSerializer(data={
            "customer": sale_data["customer"].id,
            "sale_type": sale_data["sale_type"],
            "payment_method": sale_data["payment_method"],
            "needs_delivery": sale_data["needs_delivery"],
        }, context={"request": None})
        assert not serializer.is_valid()
        assert "sale_details" in serializer.errors

    def test_sale_serializer_unique_products(self, sale, sale_data, product):
        sale_detail_data = {
            "product": product,
            "quantity": Decimal("1.0"),
            "price": Decimal("1.20"),
        }
        SaleDetail.objects.create(sale=sale, **sale_detail_data)
        serializer = SaleSerializer(data={
            "customer": sale.customer.id,
            "sale_type": sale.sale_type,
            "payment_method": sale.payment_method,
            "needs_delivery": sale.needs_delivery,
            "sale_details": [sale_detail_data, sale_detail_data],
        }, context={"sale": sale})
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors


@pytest.mark.django_db
class TestSaleDetailSerializer:
    def test_valid_sale_detail_serializer(self, sale, sale_detail_data):
        serializer = SaleDetailSerializer(data={
            "product": sale_detail_data["product"].id,
            "quantity": sale_detail_data["quantity"],
        }, context={"sale": sale})
        assert serializer.is_valid(), serializer.errors
        sale_detail = serializer.save()
        assert sale_detail.price == sale_detail_data["price"]

    def test_invalid_sale_detail_serializer_negative_quantity(self, sale, sale_detail_data):
        sale_detail_data["quantity"] = Decimal("-1.0")
        serializer = SaleDetailSerializer(data={
            "product": sale_detail_data["product"].id,
            "quantity": sale_detail_data["quantity"],
        }, context={"sale": sale})
        assert not serializer.is_valid()
        assert "quantity" in serializer.errors


@pytest.mark.django_db
class TestStateChangeSerializer:
    def test_state_change_serializer(self, state_change):
        serializer = StateChangeSerializer(state_change)
        assert serializer.data["state"] == state_change.state
        assert serializer.data["state_display"] == state_change.get_state_display()


@pytest.mark.django_db
class TestReturnSerializer:
    def test_valid_return_serializer(self, return_data, customer, admin_user):
        serializer = ReturnSerializer(data={
            "sale": return_data["sale"].id,
            "return_details": [{
                "product": return_data["sale"].sale_details.first().product.id,
                "quantity": Decimal("1.0"),
            }],
        }, context={"request": None})
        assert serializer.is_valid(), serializer.errors

    def test_invalid_return_serializer_no_details(self, return_data):
        serializer = ReturnSerializer(data={
            "sale": return_data["sale"].id,
        }, context={"request": None})
        assert not serializer.is_valid()
        assert "return_details" in serializer.errors

    def test_return_serializer_total_calculation(self, return_order, return_detail_data):
        return_order.calculate_total()
        assert return_order.total == return_detail_data["price"] * return_detail_data["quantity"]


@pytest.mark.django_db
class TestReturnDetailSerializer:
    def test_valid_return_detail_serializer(self, return_order, return_detail_data):
        serializer = ReturnDetailSerializer(data={
            "product": return_detail_data["product"].id,
            "quantity": return_detail_data["quantity"],
        }, context={"return": return_order})
        assert serializer.is_valid(), serializer.errors
        return_detail = serializer.save()
        assert return_detail.price == return_detail_data["price"]

    def test_invalid_return_detail_serializer_invalid_price(self, return_order, return_detail_data):
        return_detail_data["price"] = Decimal("0.00")
        serializer = ReturnDetailSerializer(data={
            "product": return_detail_data["product"].id,
            "quantity": return_detail_data["quantity"],
        }, context={"return": return_order})
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors


@pytest.mark.django_db
class TestPartialChargeSerializer:
    def test_valid_partial_charge_serializer(self, sale, admin_user):
        serializer = PartialChargeSerializer(data={"total": Decimal("5.00")}, context={"sale": sale})
        assert serializer.is_valid(), serializer.errors

    def test_invalid_partial_charge_exceeds_total(self, sale, admin_user):
        serializer = PartialChargeSerializer(data={"total": Decimal("15.00")}, context={"sale": sale})
        assert not serializer.is_valid()
        assert "total" in serializer.errors

    def test_invalid_partial_charge_no_sale(self, sale, admin_user):
        serializer = PartialChargeSerializer(data={"total": Decimal("5.00")}, context={})
        assert not serializer.is_valid()
        assert "total" in serializer.errors


@pytest.mark.django_db
class TestFastSaleSerializer:
    def test_valid_fast_sale_serializer(self, customer, admin_user):
        serializer = FastSaleSerializer(data={
            "customer": customer.id,
            "total": Decimal("20.00"),
            "payment_method": Sale.TARJETA,
        }, context={"request": None})
        assert serializer.is_valid(), serializer.errors

    def test_invalid_fast_sale_no_total(self, customer, admin_user):
        serializer = FastSaleSerializer(data={
            "customer": customer.id,
        }, context={"request": None})
        assert not serializer.is_valid()
        assert "total" in serializer.errors


@pytest.mark.django_db
class TestSaleAPI:
    @pytest.fixture(autouse=True)
    def setup_urls(self):
        self.list_url = reverse("api:sales-list")

    def test_sale_create_as_admin(self, api_client, admin_user, sale_data, customer, product):
        """Test creating a sale as an admin user."""
        api_client.force_authenticate(user=admin_user)
        sale_data_api = {
            "customer": customer.id,
            "sale_type": sale_data["sale_type"],
            "payment_method": sale_data["payment_method"],
            "needs_delivery": sale_data["needs_delivery"],
            "sale_details": [{
                "product": product.id,
                "quantity": "2.0"
            }]
        }
        response = api_client.post(self.list_url, data=sale_data_api, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Sale.objects.count() == 1
        sale = Sale.objects.first()
        assert sale.customer == customer
        assert sale.sale_details.count() == 1

    def test_sale_create_as_seller(self, api_client, seller_user, sale_data, customer, product):
        """Test creating a sale as a seller user."""
        api_client.force_authenticate(user=seller_user)
        sale_data_api = {
            "customer": customer.id,
            "sale_type": sale_data["sale_type"],
            "payment_method": sale_data["payment_method"],
            "needs_delivery": sale_data["needs_delivery"],
            "sale_details": [{
                "product": product.id,
                "quantity": "2.0"
            }]
        }
        response = api_client.post(self.list_url, data=sale_data_api, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Sale.objects.count() == 1

    def test_sale_create_unauthenticated(self, api_client, sale_data):
        """Test creating a sale without authentication."""
        sale_data_api = {
            "customer": sale_data["customer"].id,
            "sale_type": sale_data["sale_type"],
            "payment_method": sale_data["payment_method"],
            "needs_delivery": sale_data["needs_delivery"],
            "sale_details": [],
        }
        response = api_client.post(self.list_url, data=sale_data_api, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sale_list(self, api_client, admin_user, sale):
        """Test listing sales as an admin user."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == sale.id

    def test_sale_retrieve(self, api_client, admin_user, sale):
        """Test retrieving a sale as an admin user."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:sales-detail", args=[sale.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == sale.id

    def test_sale_update(self, api_client, admin_user, sale, product, customer):
        """Test updating a sale as an admin user."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:sales-detail", args=[sale.id])
        updated_data = {
            "customer": customer.id,
            "sale_type": Sale.MAYORISTA,
            "payment_method": Sale.TARJETA,
            "needs_delivery": True,
            "sale_details": [{
                "product": product.id,
                "quantity": "3.0"
            }]
        }
        response = api_client.put(url, data=updated_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        sale.refresh_from_db()
        assert sale.sale_type == Sale.MAYORISTA
        assert sale.payment_method == Sale.TARJETA
        assert sale.needs_delivery is True
        assert sale.sale_details.count() == 1
        assert sale.sale_details.first().quantity == Decimal("3.0")

    def test_sale_partial_update(self, api_client, admin_user, sale):
        """Test partially updating a sale as an admin user."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:sales-detail", args=[sale.id])
        response = api_client.patch(url, data={"needs_delivery": True}, format='json')
        assert response.status_code == status.HTTP_200_OK
        sale.refresh_from_db()
        assert sale.needs_delivery is True

    def test_sale_delete_as_admin(self, api_client, admin_user, sale):
        """Test deleting a sale as an admin user."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:sales-detail", args=[sale.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        sale.refresh_from_db()
        assert not sale.is_active

    def test_sale_delete_as_seller(self, api_client, seller_user, sale):
        """Test deleting a sale as a seller user."""
        api_client.force_authenticate(user=seller_user)
        url = reverse("api:sales-detail", args=[sale.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sale_filter_by_total_range(self, api_client, admin_user, sale):
        """Test filtering sales by total range."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {"min_total": "5.00", "max_total": "15.00"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_sale_filter_by_state(self, api_client, admin_user, sale, state_change):
        """Test filtering sales by state."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {"state": state_change.state})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_sale_mark_as_delivered(self, api_client, delivery_user, sale, state_change):
        """Test marking a sale as delivered."""
        api_client.force_authenticate(user=delivery_user)
        url = reverse("api:sales-mark-as-delivered", args=[sale.id])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        sale.refresh_from_db()
        new_state = sale.get_state()
        assert new_state == StateChange.ENTREGADA

    def test_sale_mark_as_charged(self, api_client, delivery_user, sale, state_change):
        """Test marking a sale as charged."""
        api_client.force_authenticate(user=delivery_user)
        url = reverse("api:sales-mark-as-charged", args=[sale.id])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        sale.refresh_from_db()
        new_state = sale.get_state()
        assert new_state == StateChange.COBRADA

    def test_sale_statistics(self, api_client, admin_user, sale, state_change):
        """Test retrieving sales statistics."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:sales-statistics")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "statistics" in response.data

    def test_sale_create_fast_sale(self, api_client, admin_user, customer):
        """Test creating a fast sale."""
        api_client.force_authenticate(user=admin_user)
        fast_sale_data = {
            "customer": customer.id,
            "total": "50.00",
            "payment_method": Sale.EFECTIVO,
        }
        url = reverse("api:sales-create-fast-sale")
        response = api_client.post(url, data=fast_sale_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Sale.objects.count() == 1
        sale = Sale.objects.first()
        assert sale.total == Decimal("50.00")
        assert sale.total_collected == Decimal("50.00")

    def test_sale_update_fast_sale(self, api_client, admin_user, sale, customer):
        """Test updating a fast sale."""
        api_client.force_authenticate(user=admin_user)
        fast_sale_update_data = {
            "customer": customer.id,
            "total": "60.00",
            "payment_method": Sale.TARJETA,
        }
        url = reverse("api:sales-update-fast-sale", args=[sale.id])
        response = api_client.put(url, data=fast_sale_update_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        sale.refresh_from_db()
        assert sale.total == Decimal("60.00")
        assert sale.payment_method == Sale.TARJETA

    def test_sale_cancel(self, api_client, seller_user, sale, state_change):
        """Test cancelling a sale."""
        api_client.force_authenticate(user=seller_user)
        url = reverse("api:sales-cancel", args=[sale.id])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        sale.refresh_from_db()
        new_state = sale.get_state()
        assert new_state in [StateChange.CANCELADA, StateChange.ANULADA]


@pytest.mark.django_db
class TestReturnAPI:
    @pytest.fixture(autouse=True)
    def setup_urls(self):
        self.list_url = reverse("api:returns-list")

    def test_return_create_as_admin(self, api_client, admin_user, return_data, product):
        """Test creating a return as an admin user."""
        api_client.force_authenticate(user=admin_user)
        return_data_api = {
            "sale": return_data["sale"].id,
            "return_details": [{
                "product": product.id,
                "quantity": "1.0"
            }]
        }
        response = api_client.post(self.list_url, data=return_data_api, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Return.objects.count() == 1
        return_order = Return.objects.first()
        assert return_order.sale == return_data["sale"]
        assert return_order.return_details.count() == 1

    def test_return_create_as_seller(self, api_client, seller_user, return_data, product):
        """Test creating a return as a seller user."""
        api_client.force_authenticate(user=seller_user)
        return_data_api = {
            "sale": return_data["sale"].id,
            "return_details": [{
                "product": product.id,
                "quantity": "1.0"
            }]
        }
        response = api_client.post(self.list_url, data=return_data_api, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Return.objects.count() == 1

    def test_return_create_unauthenticated(self, api_client, return_data):
        """Test creating a return without authentication."""
        return_data_api = {
            "sale": return_data["sale"].id,
            "return_details": [],
        }
        response = api_client.post(self.list_url, data=return_data_api, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_return_list(self, api_client, admin_user, return_order):
        """Test listing returns as an admin user."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == return_order.id

    def test_return_retrieve(self, api_client, admin_user, return_order):
        """Test retrieving a return as an admin user."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:returns-detail", args=[return_order.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == return_order.id

    def test_return_update(self, api_client, admin_user, return_order, product):
        """Test updating a return as an admin user."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:returns-detail", args=[return_order.id])
        updated_data = {
            "sale": return_order.sale.id,
            "return_details": [{
                "product": product.id,
                "quantity": "2.0"
            }]
        }
        response = api_client.put(url, data=updated_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        return_order.refresh_from_db()
        assert return_order.return_details.count() == 1
        assert return_order.return_details.first().quantity == Decimal("2.0")

    def test_return_partial_update(self, api_client, admin_user, return_order, return_detail, product):
        """Test partially updating a return as an admin user by modifying return_details."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:returns-detail", args=[return_order.id])
        updated_data = {
            "return_details": [{
                "id": return_detail.id,
                "quantity": "3.00"
            }]
        }
        response = api_client.patch(url, data=updated_data, format='json')
        print(response.data)
        assert response.status_code == status.HTTP_200_OK
        return_order.refresh_from_db()
        expected_total = return_detail.price * Decimal("3.00")
        assert return_order.total == expected_total

    def test_return_delete_as_admin(self, api_client, admin_user, return_order):
        """Test deleting a return as an admin user."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:returns-detail", args=[return_order.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        return_order.refresh_from_db()
        assert not return_order.is_active

    def test_return_delete_as_seller(self, api_client, seller_user, return_order):
        """Test deleting a return as a seller user."""
        api_client.force_authenticate(user=seller_user)
        url = reverse("api:returns-detail", args=[return_order.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_return_filter_by_customer(self, api_client, admin_user, return_order, customer):
        """Test filtering returns by customer."""
        api_client.force_authenticate(user=admin_user)
        customer_id = return_order.sale.customer.id
        response = api_client.get(self.list_url, {"customer": customer_id})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_return_search(self, api_client, admin_user, return_order, customer):
        """Test searching returns by customer name."""
        api_client.force_authenticate(user=admin_user)
        print("*" * 100)
        customer_name = return_order.sale.customer.name
        print(customer_name)
        print("*" * 100)
        response = api_client.get(self.list_url, {"search": customer_name})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_return_ordering(self, api_client, admin_user, return_order):
        """Test ordering returns by date."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {"ordering": "-date"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_return_permissions_create(self, api_client, return_data):
        """Test creating a return without permissions."""
        return_data_api = {
            "sale": return_data["sale"].id,
            "return_details": [],
        }
        response = api_client.post(self.list_url, data=return_data_api, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_return_permissions_list(self, api_client):
        """Test listing returns without permissions."""
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_return_permissions_update(self, api_client, return_data):
        """Test updating a return without permissions."""
        return_order = Return.objects.create(**return_data)
        url = reverse("api:returns-detail", args=[return_order.id])
        response = api_client.put(url, data={}, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_return_permissions_delete(self, api_client, return_data):
        """Test deleting a return without permissions."""
        return_order = Return.objects.create(**return_data)
        url = reverse("api:returns-detail", args=[return_order.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestFastSaleSerializer:
    def test_valid_fast_sale_serializer(self, fast_sale_data, customer, admin_user):
        serializer = FastSaleSerializer(data=fast_sale_data, context={"request": None})
        assert serializer.is_valid(), serializer.errors

    def test_invalid_fast_sale_serializer_no_total(self, fast_sale_data, customer, admin_user):
        fast_sale_data.pop("total")
        serializer = FastSaleSerializer(data=fast_sale_data, context={"request": None})
        assert not serializer.is_valid()
        assert "total" in serializer.errors


@pytest.mark.django_db
class TestFastSaleAPI:
    @pytest.fixture
    def fast_sale_data(self, customer):
        return {
            "customer": customer.id,
            "total": "100.00",
            "payment_method": Sale.TRANSFERENCIA,
        }

    def test_create_fast_sale_as_admin(self, api_client, admin_user, fast_sale_data):
        """Test creating a fast sale as an admin user."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:sales-create-fast-sale")
        response = api_client.post(url, data=fast_sale_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Sale.objects.count() == 1
        sale = Sale.objects.first()
        assert sale.total == Decimal("100.00")
        assert sale.payment_method == Sale.TRANSFERENCIA

    def test_create_fast_sale_as_seller(self, api_client, seller_user, fast_sale_data):
        """Test creating a fast sale as a seller user."""
        api_client.force_authenticate(user=seller_user)
        url = reverse("api:sales-create-fast-sale")
        response = api_client.post(url, data=fast_sale_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Sale.objects.count() == 1

    def test_create_fast_sale_unauthenticated(self, api_client, fast_sale_data):
        """Test creating a fast sale without authentication."""
        url = reverse("api:sales-create-fast-sale")
        response = api_client.post(url, data=fast_sale_data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_fast_sale_as_admin(self, api_client, admin_user, sale, fast_sale_data):
        """Test updating a fast sale as an admin user."""
        api_client.force_authenticate(user=admin_user)
        fast_sale_update_data = {
            "customer": fast_sale_data["customer"],
            "total": "150.00",
            "payment_method": Sale.TARJETA,
        }
        url = reverse("api:sales-update-fast-sale", args=[sale.id])
        response = api_client.put(url, data=fast_sale_update_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        sale.refresh_from_db()
        assert sale.total == Decimal("150.00")
        assert sale.payment_method == Sale.TARJETA

    def test_update_fast_sale_as_seller(self, api_client, seller_user, sale, fast_sale_data):
        """Test updating a fast sale as a seller user."""
        api_client.force_authenticate(user=seller_user)
        fast_sale_update_data = {
            "customer": fast_sale_data["customer"],
            "total": "150.00",
            "payment_method": Sale.TARJETA,
        }
        url = reverse("api:sales-update-fast-sale", args=[sale.id])
        response = api_client.put(url, data=fast_sale_update_data, format='json')
        print(response.data)
        assert response.status_code == status.HTTP_200_OK
        sale.refresh_from_db()
        assert sale.total == Decimal("150.00")
        assert sale.payment_method == Sale.TARJETA

    def test_update_fast_sale_unauthenticated(self, api_client, sale, fast_sale_data):
        """Test updating a fast sale without authentication."""
        fast_sale_update_data = {
            "customer": fast_sale_data["customer"],
            "total": "150.00",
            "payment_method": Sale.TARJETA,
        }
        url = reverse("api:sales-update-fast-sale", args=[sale.id])
        response = api_client.put(url, data=fast_sale_update_data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
