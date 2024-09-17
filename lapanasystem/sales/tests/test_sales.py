"""Sales tests."""

# Django
from django.urls import reverse
from decimal import Decimal

# Django REST Framework
from rest_framework.test import APIClient
from rest_framework import status

# Models
from lapanasystem.sales.models import Sale, SaleDetail, StateChange
from lapanasystem.products.models import Product, ProductBrand, ProductCategory
from lapanasystem.customers.models import Customer
from lapanasystem.users.models import User

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
        user_type=User.ADMIN,
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
        user_type=User.SELLER,
    )


@pytest.fixture
def delivery_user():
    return User.objects.create_user(
        username="delivery",
        email="delivery@example.com",
        password="deliverypass123",
        first_name="Delivery",
        last_name="User",
        user_type=User.DELIVERY,
    )


@pytest.fixture
def customer():
    return Customer.objects.create(
        name="John Doe",
        email="johndoe@example.com",
        phone_number="+1234567890",
        address="123 Main St",
        customer_type=Customer.MINORISTA,
    )


@pytest.fixture
def wholesale_customer():
    return Customer.objects.create(
        name="Wholesale Co.",
        email="wholesale@example.com",
        phone_number="+0987654321",
        address="456 Market St",
        customer_type=Customer.MAYORISTA,
    )


@pytest.fixture
def brand():
    return ProductBrand.objects.create(name="Brand")


@pytest.fixture
def category():
    return ProductCategory.objects.create(name="Category")


@pytest.fixture
def product_retail(brand, category):
    return Product.objects.create(
        barcode="RET123",
        name="Retail Product",
        description="A retail product",
        retail_price=Decimal("10.00"),
        wholesale_price=Decimal("8.00"),
        brand=brand,
        category=category,
        is_active=True,
    )


@pytest.fixture
def product_wholesale(brand, category):
    return Product.objects.create(
        barcode="WHO123",
        name="Wholesale Product",
        description="A wholesale product",
        retail_price=Decimal("15.00"),
        wholesale_price=Decimal("12.00"),
        brand=brand,
        category=category,
        is_active=True,
    )


@pytest.fixture
def sale(admin_user, customer, product_retail):
    sale = Sale.objects.create(
        user=admin_user,
        customer=customer,
        sale_type=Sale.MINORISTA,
        payment_method=Sale.EFECTIVO,
        total=Decimal("20.00"),
        is_active=True,
    )
    SaleDetail.objects.create(
        sale=sale,
        product=product_retail,
        quantity=Decimal("2"),
        price=product_retail.retail_price,
    )
    StateChange.objects.create(sale=sale, state=StateChange.CREADA)
    return sale


@pytest.mark.django_db
class TestSaleModel:
    def test_sale_str(self, admin_user, customer):
        sale = Sale.objects.create(
            user=admin_user,
            customer=customer,
            total=Decimal("100.00"),
            sale_type=Sale.MINORISTA,
            payment_method=Sale.EFECTIVO,
        )
        assert str(sale) == f"{sale.customer} - {sale.total}"


@pytest.mark.django_db
class TestSaleAPI:
    @pytest.fixture(autouse=True)
    def setup_urls(self):
        self.list_url = reverse("api:sales-list")

    def test_sale__with_details_create_as_admin(
        self, api_client, admin_user, customer, product_retail
    ):
        """Verify that an admin user can create a sale."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "sale_details": [{"product": product_retail.id, "quantity": "2.000"}],
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Sale.objects.count() == 1
        sale = Sale.objects.first()
        assert sale.customer == customer
        assert sale.sale_details.count() == 1
        assert sale.state_changes.count() == 1
        assert sale.state_changes.first().state == StateChange.CREADA

    def test_sale_without_sale_details_as_admin(self, api_client, admin_user, customer):
        """Verify that an admin user can create a sale with only total."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "total": 1600,
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["total"] == "1600.00"
        assert response.data["sale_details"] == []
        assert response.data["payment_method"] == Sale.EFECTIVO
        assert response.data["sale_type"] == Sale.MINORISTA

    def test_sale_with_details_create_as_seller(
        self, api_client, seller_user, customer, product_retail
    ):
        """Verify that a seller user can create a sale."""
        api_client.force_authenticate(user=seller_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MAYORISTA,
            "payment_method": Sale.TARJETA,
            "sale_details": [{"product": product_retail.id, "quantity": "3.000"}],
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        sale = Sale.objects.first()
        assert sale.sale_type == Sale.MAYORISTA
        assert sale.sale_details.first().price == product_retail.wholesale_price

    def test_sale_without_sale_details_as_seller(
        self, api_client, seller_user, customer
    ):
        """Verify that a seller user can create a sale with only total."""
        api_client.force_authenticate(user=seller_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "total": 1600,
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["total"] == "1600.00"
        assert response.data["sale_details"] == []
        assert response.data["payment_method"] == Sale.EFECTIVO
        assert response.data["sale_type"] == Sale.MINORISTA

    def test_sale_create_unauthenticated(self, api_client, customer, product_retail):
        """Verify that an unauthenticated user cannot create a sale."""
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "sale_details": [{"product": product_retail.id, "quantity": "1.000"}],
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sale_list_as_admin(self, api_client, admin_user, customer, product_retail):
        """Verify that an admin user can list sales."""
        sale = Sale.objects.create(
            user=admin_user,
            customer=customer,
            sale_type=Sale.MINORISTA,
            payment_method=Sale.EFECTIVO,
            total=Decimal("20.00"),
            is_active=True,
        )
        SaleDetail.objects.create(
            sale=sale,
            product=product_retail,
            quantity=Decimal("2"),
            price=product_retail.retail_price,
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["total"] == "20.00"

    def test_sale_retrieve_as_admin(
        self, api_client, admin_user, customer, product_retail
    ):
        """Verify that an admin user can retrieve a sale."""
        sale = Sale.objects.create(
            user=admin_user,
            customer=customer,
            sale_type=Sale.MINORISTA,
            payment_method=Sale.EFECTIVO,
            total=Decimal("10.00"),
            is_active=True,
        )
        SaleDetail.objects.create(
            sale=sale,
            product=product_retail,
            quantity=Decimal("1"),
            price=product_retail.retail_price,
        )
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:sales-detail", args=[sale.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total"] == "10.00"
        assert len(response.data["sale_details"]) == 1

    def test_sale_update_as_admin(
        self, api_client, admin_user, customer, product_retail, product_wholesale
    ):
        """Verify that an admin user can update a sale."""
        sale = Sale.objects.create(
            user=admin_user,
            customer=customer,
            sale_type=Sale.MINORISTA,
            payment_method=Sale.EFECTIVO,
            is_active=True,
        )
        sale_detail = SaleDetail.objects.create(
            sale=sale,
            product=product_retail,
            quantity=Decimal("2"),
            price=product_retail.retail_price,
        )
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:sales-detail", args=[sale.id])
        update_data = {
            "sale_type": Sale.MAYORISTA,
            "sale_details": [
                {
                    "id": sale_detail.id,
                    "product": product_retail.id,
                    "quantity": "3.000",
                },
                {"product": product_wholesale.id, "quantity": "1.000"},
            ],
        }
        response = api_client.put(url, data=update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        sale.refresh_from_db()
        assert sale.sale_type == Sale.MAYORISTA
        assert sale.sale_details.count() == 2
        updated_detail = sale.sale_details.get(product=product_retail)
        assert updated_detail.quantity == Decimal("3.000")
        new_detail = sale.sale_details.get(product=product_wholesale)
        assert new_detail.quantity == Decimal("1.000")
        assert sale.total == (Decimal("8.00") * 3) + (Decimal("12.00") * 1)

    def test_sale_partial_update_as_seller(
        self, api_client, seller_user, customer, sale, product_retail
    ):
        """Verify that a seller user can partially update a sale."""
        api_client.force_authenticate(user=seller_user)
        url = reverse("api:sales-detail", args=[sale.id])
        partial_update_data = {"payment_method": Sale.TARJETA, "total": "20.00"}
        response = api_client.patch(url, data=partial_update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        sale.refresh_from_db()
        assert sale.payment_method == Sale.TARJETA

    def test_sale_delete_as_admin(self, api_client, admin_user, customer, sale):
        """Verify that an admin user can soft delete a sale."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:sales-detail", args=[sale.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        sale.refresh_from_db()
        assert not sale.is_active

    def test_sale_delete_as_seller(self, api_client, seller_user, customer, sale):
        """Verify that a seller user can delete a sale."""
        api_client.force_authenticate(user=seller_user)
        url = reverse("api:sales-detail", args=[sale.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        sale.refresh_from_db()
        assert not sale.is_active

    def test_sale_cancel_as_admin(self, api_client, admin_user, customer, sale):
        """Verify that an admin user can cancel a sale."""
        StateChange.objects.create(sale=sale, state=StateChange.CREADA)
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:sales-cancel", args=[sale.id])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        sale.refresh_from_db()
        last_state = sale.get_state()
        assert last_state == StateChange.CANCELADA

    def test_sale_mark_as_delivered_as_delivery(
        self, api_client, delivery_user, customer, sale
    ):
        """Verify that a delivery user can mark a sale as delivered."""
        StateChange.objects.create(sale=sale, state=StateChange.PENDIENTE_ENTREGA)
        api_client.force_authenticate(user=delivery_user)
        url = reverse("api:sales-mark-as-delivered", args=[sale.id])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        sale.refresh_from_db()
        last_state = sale.get_state()
        assert last_state == StateChange.ENTREGADA

    def test_sale_mark_as_charged_as_delivery(
        self, api_client, delivery_user, customer, sale
    ):
        """Verify that a delivery user can mark a sale as charged."""
        StateChange.objects.create(sale=sale, state=StateChange.ENTREGADA)
        api_client.force_authenticate(user=delivery_user)
        url = reverse("api:sales-mark-as-charged", args=[sale.id])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        sale.refresh_from_db()
        last_state = sale.get_state()
        assert last_state == StateChange.COBRADA

    def test_sale_permissions_cancel_as_delivery(
        self, api_client, delivery_user, customer, sale
    ):
        """Verify that a delivery user cannot cancel a sale."""
        StateChange.objects.create(sale=sale, state=StateChange.CREADA)
        api_client.force_authenticate(user=delivery_user)
        url = reverse("api:sales-cancel", args=[sale.id])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sale_permissions_mark_as_delivered_as_seller(
        self, api_client, seller_user, customer, sale
    ):
        """Verify that a seller user cannot mark a sale as delivered."""
        StateChange.objects.create(sale=sale, state=StateChange.PENDIENTE_ENTREGA)
        api_client.force_authenticate(user=seller_user)
        url = reverse("api:sales-mark-as-delivered", args=[sale.id])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sale_permissions_mark_as_charged_as_seller(
        self, api_client, seller_user, customer, sale
    ):
        """Verify that a seller user cannot mark a sale as charged."""
        StateChange.objects.create(sale=sale, state=StateChange.ENTREGADA)
        api_client.force_authenticate(user=seller_user)
        url = reverse("api:sales-mark-as-charged", args=[sale.id])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sale_mark_as_delivered_invalid_state(
        self, api_client, delivery_user, customer, sale
    ):
        """Verify that marking as delivered fails if the sale is already canceled."""
        StateChange.objects.create(sale=sale, state=StateChange.CANCELADA)
        api_client.force_authenticate(user=delivery_user)
        url = reverse("api:sales-mark-as-delivered", args=[sale.id])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_sale_filter_by_state(self, api_client, admin_user, customer, sale):
        """Verify that an admin user can filter sales by state."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {"state": StateChange.CREADA})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == sale.id

    def test_sale_search_by_customer_name(self, api_client, admin_user, customer, sale):
        """Verify that an admin user can search sales by customer name."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {"search": "John"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["customer_details"]["name"] == "John Doe"

    def test_sale_ordering_by_total(
        self, api_client, admin_user, customer, sale, product_retail
    ):
        """Verify that an admin user can order sales by total."""
        sale1 = Sale.objects.create(
            user=admin_user,
            customer=customer,
            sale_type=Sale.MINORISTA,
            payment_method=Sale.EFECTIVO,
            total=Decimal("30.00"),
            is_active=True,
        )
        sale2 = Sale.objects.create(
            user=admin_user,
            customer=customer,
            sale_type=Sale.MINORISTA,
            payment_method=Sale.EFECTIVO,
            total=Decimal("10.00"),
            is_active=True,
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {"ordering": "-total"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]["total"] == "30.00"
        assert response.data[1]["total"] == "20.00"
        assert response.data[2]["total"] == "10.00"

    def test_sale_permissions_create_as_delivery(
        self, api_client, delivery_user, customer, product_retail
    ):
        """Verify that a delivery user cannot create a sale."""
        api_client.force_authenticate(user=delivery_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "sale_details": [{"product": product_retail.id, "quantity": "1.000"}],
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sale_cancel_already_canceled(self, api_client, admin_user, customer, sale):
        """Verify that canceling an already canceled sale raises an error."""
        StateChange.objects.create(sale=sale, state=StateChange.CANCELADA)
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:sales-cancel", args=[sale.id])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_sale_create_with_invalid_product(self, api_client, admin_user, customer):
        """Verify that creating a sale with an invalid product raises an error."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "sale_details": [{"product": 999, "quantity": "1.000"}],
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_sale_partial_update_with_invalid_total(
        self, api_client, admin_user, customer, sale
    ):
        """Verify that partially updating a sale with an invalid total raises an error."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:sales-detail", args=[sale.id])
        partial_update_data = {"total": "-50.00"}
        response = api_client.patch(url, data=partial_update_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_sale_update_with_invalid_sale_detail(
        self, api_client, admin_user, customer, sale
    ):
        """Verify that updating a sale with an invalid sale detail raises an error."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:sales-detail", args=[sale.id])
        update_data = {
            "sale_details": [{"id": 999, "product": 999, "quantity": "1.000"}]
        }
        response = api_client.put(url, data=update_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_sale_create_with_zero_quantity(self, api_client, admin_user, customer, product_retail):
        """Verify that creating a sale with zero quantity raises an error."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "sale_details": [{"product": product_retail.id, "quantity": "0.000"}],
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "quantity" in response.data["sale_details"][0]

    def test_sale_create_with_negative_quantity(self, api_client, admin_user, customer, product_retail):
        """Verify that creating a sale with negative quantity raises an error."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "sale_details": [{"product": product_retail.id, "quantity": "-1.000"}],
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "quantity" in response.data["sale_details"][0]

    def test_sale_create_with_inconsistent_total(self, api_client, admin_user, customer, product_retail):
        """Verify that creating a sale with an inconsistent total raises an error."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "sale_details": [{"product": product_retail.id, "quantity": "2.000"}],
            "total": "15.00",
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
