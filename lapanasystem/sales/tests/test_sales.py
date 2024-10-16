"""Sales tests."""

# Django
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone

# Django REST Framework
from rest_framework.test import APIClient
from rest_framework import status

# Models
from lapanasystem.sales.models import Sale, SaleDetail, StateChange, Return
from lapanasystem.products.models import Product, ProductBrand, ProductCategory
from lapanasystem.customers.models import Customer
from lapanasystem.users.models import User
from lapanasystem.expenses.models import Expense

# Utilities
import pytest
from datetime import timedelta


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

    def test_sale_create_with_details_as_admin(
        self, api_client, admin_user, customer, product_retail
    ):
        """Verify that an admin user can create a sale with sale details."""
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
        # Verify total calculation
        expected_total = product_retail.retail_price * Decimal("2.000")
        assert sale.total == expected_total
        # Check via response data
        assert response.data["total"] == str(expected_total)

    def test_sale_create_without_sale_details_as_admin(
        self, api_client, admin_user, customer
    ):
        """Verify that an admin user can create a sale without sale details."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "total": "1600.00",
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["total"] == "1600.00"
        assert response.data["sale_details"] == []
        assert response.data["payment_method"] == Sale.EFECTIVO
        assert response.data["sale_type"] == Sale.MINORISTA

    def test_sale_create_with_details_as_seller(
        self, api_client, seller_user, customer, product_retail
    ):
        """Verify that a seller user can create a sale with sale details."""
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
        # Verify total calculation
        expected_total = product_retail.wholesale_price * Decimal("3.000")
        assert sale.total == expected_total
        assert response.data["total"] == str(expected_total)

    def test_sale_create_without_sale_details_as_seller(
        self, api_client, seller_user, customer
    ):
        """Verify that a seller user can create a sale without sale details."""
        api_client.force_authenticate(user=seller_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "total": "1600.00",
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
        assert 'results' in response.data
        assert len(response.data['results']) == 1
        assert response.data['results'][0]["total"] == "20.00"

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
        # Calculate initial total
        sale.calculate_total()
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
        # Calculate expected total based on sale_type=mayorista
        expected_total = (product_retail.wholesale_price * Decimal("3.000")) + (product_wholesale.wholesale_price * Decimal("1.000"))
        assert sale.total == expected_total
        # Check via response data
        assert response.data["total"] == str(expected_total)

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
        # Assuming 'total' was provided correctly
        assert sale.total == Decimal("20.00")
        assert response.data["total"] == "20.00"

    def test_sale_delete_as_admin(self, api_client, admin_user, customer, sale):
        """Verify that an admin user can soft delete a sale."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:sales-detail", args=[sale.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        sale.refresh_from_db()
        assert not sale.is_active
        # Verify that the sale is no longer in the list of active sales
        response = api_client.get(self.list_url)
        assert 'results' in response.data
        assert len(response.data['results']) == 0

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
        self, api_client, delivery_user, customer, sale, product_retail
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
        # Verify that a new StateChange was created
        assert sale.state_changes.count() == 2
        assert sale.state_changes.last().state == StateChange.ENTREGADA

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
        assert "non_field_errors" in response.data
        expected_error = "La venta ya ha sido cancelada."
        assert response.data["non_field_errors"][0] == expected_error

    def test_sale_mark_as_delivered_without_previous_state(
        self, api_client, delivery_user, customer, sale
    ):
        """Verify that marking as delivered fails if the sale has no previous state."""
        # Ensure no StateChange exists
        sale.state_changes.all().delete()
        api_client.force_authenticate(user=delivery_user)
        url = reverse("api:sales-mark-as-delivered", args=[sale.id])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data
        expected_error = "La venta no tiene un estado previo."
        assert response.data["non_field_errors"][0] == expected_error

    def test_sale_filter_by_state(self, api_client, admin_user, customer, sale):
        """Verify that an admin user can filter sales by state."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {"state": StateChange.CREADA})
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 1
        assert response.data['results'][0]["id"] == sale.id

    def test_sale_search_by_customer_name(self, api_client, admin_user, customer, sale):
        """Verify that an admin user can search sales by customer name."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {"search": "John"})
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 1
        assert response.data['results'][0]["customer_details"]["name"] == "John Doe"

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
        SaleDetail.objects.create(
            sale=sale1,
            product=product_retail,
            quantity=Decimal("3"),
            price=product_retail.retail_price,
        )
        sale2 = Sale.objects.create(
            user=admin_user,
            customer=customer,
            sale_type=Sale.MINORISTA,
            payment_method=Sale.EFECTIVO,
            total=Decimal("10.00"),
            is_active=True,
        )
        SaleDetail.objects.create(
            sale=sale2,
            product=product_retail,
            quantity=Decimal("1"),
            price=product_retail.retail_price,
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {"ordering": "-total"})
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 3  # Including the initial sale
        assert response.data['results'][0]["total"] == "30.00"
        assert response.data['results'][1]["total"] == "20.00"
        assert response.data['results'][2]["total"] == "10.00"

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
        assert "non_field_errors" in response.data
        expected_error = "La venta ya ha sido cancelada."
        assert response.data["non_field_errors"][0] == expected_error

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
        assert "sale_details" in response.data
        assert "product" in response.data["sale_details"][0]
        assert "does not exist" in response.data["sale_details"][0]["product"][0].lower()

    def test_sale_partial_update_with_invalid_total(
        self, api_client, admin_user, customer, sale
    ):
        """Verify that partially updating a sale with an invalid total raises an error."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:sales-detail", args=[sale.id])
        partial_update_data = {"total": "-50.00"}
        response = api_client.patch(url, data=partial_update_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data
        expected_error = "El total proporcionado no coincide con la suma de los detalles de la venta."
        assert response.data["non_field_errors"][0] == expected_error

    def test_sale_create_with_zero_quantity(
        self, api_client, admin_user, customer, product_retail
    ):
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
        assert "sale_details" in response.data
        assert "quantity" in response.data["sale_details"][0]
        expected_error = "La cantidad debe ser mayor a 0."
        assert response.data["sale_details"][0]["quantity"][0] == expected_error

    def test_sale_create_with_negative_quantity(
        self, api_client, admin_user, customer, product_retail
    ):
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
        assert "sale_details" in response.data
        assert "quantity" in response.data["sale_details"][0]
        expected_error = "La cantidad debe ser mayor a 0."
        assert response.data["sale_details"][0]["quantity"][0] == expected_error

    def test_sale_create_with_inconsistent_total(
        self, api_client, admin_user, customer, product_retail
    ):
        """Verify that creating a sale with an inconsistent total raises an error."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "sale_details": [{"product": product_retail.id, "quantity": "2.000"}],
            "total": "15.00",  # Correct total should be 20.00
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data
        expected_error = "El total proporcionado no coincide con la suma de los detalles de la venta."
        assert response.data["non_field_errors"][0] == expected_error

    def test_sale_statistics_as_admin(
        self, api_client, admin_user, customer, product_retail, product_wholesale
    ):
        """Verify that an admin user can retrieve accurate sales statistics."""
        # Create additional sales
        sale2 = Sale.objects.create(
            user=admin_user,
            customer=customer,
            sale_type=Sale.MAYORISTA,
            payment_method=Sale.TARJETA,
            total=Decimal("50.00"),
            is_active=True,
        )
        SaleDetail.objects.create(
            sale=sale2,
            product=product_retail,
            quantity=Decimal("5"),
            price=product_retail.wholesale_price,
        )
        SaleDetail.objects.create(
            sale=sale2,
            product=product_wholesale,
            quantity=Decimal("2"),
            price=product_wholesale.wholesale_price,
        )
        # Create returns and expenses
        Return.objects.create(sale=sale, total=Decimal("5.00"))
        Expense.objects.create(amount=Decimal("10.00"), date=timezone.now())

        # Authenticate as admin
        api_client.force_authenticate(user=admin_user)

        # Define date range covering all sales
        today = timezone.now().date()
        start_date = today - timedelta(days=7)
        end_date = today + timedelta(days=1)

        # Call the statistics endpoint with custom date range
        url = reverse("api:sales-statistics")
        response = api_client.get(
            url,
            {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "statistics" in response.data
        statistics = response.data["statistics"]

        # Verify statistics for the 'custom' period
        assert "custom" in statistics
        custom_stats = statistics["custom"]
        assert custom_stats["total_sales_count"] == 2
        assert custom_stats["total_sales_amount"] == "70.00"  # 20.00 + 50.00
        assert custom_stats["total_returns_amount"] == "5.00"  # Based on created returns
        assert custom_stats["net_revenue"] == "65.00"  # 70.00 - 5.00
        assert custom_stats["total_expenses"] == "10.00"  # Based on created expenses
        assert "most_sold_products" in custom_stats
        assert len(custom_stats["most_sold_products"]) == 2
        assert custom_stats["most_sold_products"][0]["product_name"] == "Retail Product"
        assert custom_stats["most_sold_products"][0]["total_quantity_sold"] == "7.000"  # 2 + 5
        assert custom_stats["most_sold_products"][1]["product_name"] == "Wholesale Product"
        assert custom_stats["most_sold_products"][1]["total_quantity_sold"] == "2.000"

    def test_sale_statistics_with_product_filter(
        self, api_client, admin_user, customer, sale, product_retail, product_wholesale
    ):
        """Verify that the statistics endpoint can filter by product_slug."""
        # Create additional sales
        sale2 = Sale.objects.create(
            user=admin_user,
            customer=customer,
            sale_type=Sale.MAYORISTA,
            payment_method=Sale.TARJETA,
            total=Decimal("50.00"),
            is_active=True,
        )
        SaleDetail.objects.create(
            sale=sale2,
            product=product_retail,
            quantity=Decimal("5"),
            price=product_retail.wholesale_price,
        )
        SaleDetail.objects.create(
            sale=sale2,
            product=product_wholesale,
            quantity=Decimal("2"),
            price=product_wholesale.wholesale_price,
        )
        # Create returns and expenses
        Return.objects.create(sale=sale, total=Decimal("5.00"))
        Expense.objects.create(amount=Decimal("10.00"), date=timezone.now())

        # Authenticate as admin
        api_client.force_authenticate(user=admin_user)

        # Define date range covering all sales
        today = timezone.now().date()
        start_date = today - timedelta(days=7)
        end_date = today + timedelta(days=1)

        # Call the statistics endpoint with product_slug filter
        url = reverse("api:sales-statistics")
        response = api_client.get(
            url,
            {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "product_slug": product_retail.slug,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert "statistics" in response.data
        statistics = response.data["statistics"]

        # Verify statistics for the 'custom' period
        assert "custom" in statistics
        custom_stats = statistics["custom"]
        assert custom_stats["total_sales_count"] == 2
        assert custom_stats["total_sales_amount"] == "70.00"  # 20.00 + 50.00
        assert custom_stats["total_returns_amount"] == "5.00"  # Based on created returns
        assert custom_stats["net_revenue"] == "65.00"  # 70.00 - 5.00
        assert custom_stats["total_expenses"] == "10.00"  # Based on created expenses
        assert "most_sold_products" not in custom_stats  # Because a specific product is filtered
        assert "product_slug" in custom_stats
        assert custom_stats["product_slug"] == product_retail.slug
        assert custom_stats["product_name"] == product_retail.name
        assert custom_stats["total_quantity_sold"] == "7.000"  # 2 + 5

    def test_sale_create_with_delivery_as_admin(
        self, api_client, admin_user, customer, product_retail
    ):
        """Verify that creating a sale with delivery creates correct state changes and triggers delivery tasks."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "sale_details": [{"product": product_retail.id, "quantity": "2.000"}],
            "needs_delivery": True,
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        sale = Sale.objects.get(id=response.data["id"])
        assert sale.needs_delivery is True
        assert sale.state_changes.count() == 1
        assert sale.state_changes.first().state == StateChange.CREADA
        # Here you would mock and verify the asynchronous task if implemented

    def test_sale_create_with_missing_product(self, api_client, admin_user, customer):
        """Verify that creating a sale without a product in sale details raises an error."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "sale_details": [{"quantity": "1.000"}],  # Missing 'product'
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "sale_details" in response.data
        assert "product" in response.data["sale_details"][0]
        expected_error = "Este campo es requerido."
        assert response.data["sale_details"][0]["product"][0] == expected_error

    def test_sale_create_with_inconsistent_total_due_to_sale_type(
        self, api_client, admin_user, customer, product_retail, product_wholesale
    ):
        """Verify that changing sale_type affects the total calculation correctly."""
        # Create a sale as minorista
        sale = Sale.objects.create(
            user=admin_user,
            customer=customer,
            sale_type=Sale.MINORISTA,
            payment_method=Sale.EFECTIVO,
            is_active=True,
        )
        SaleDetail.objects.create(
            sale=sale,
            product=product_retail,
            quantity=Decimal("2"),
            price=product_retail.retail_price,
        )
        sale.calculate_total()

        api_client.force_authenticate(user=admin_user)
        url = reverse("api:sales-detail", args=[sale.id])
        update_data = {
            "sale_type": Sale.MAYORISTA,
            "sale_details": [
                {
                    "id": sale.sale_details.first().id,
                    "product": product_retail.id,
                    "quantity": "3.000",
                },
                {"product": product_wholesale.id, "quantity": "1.000"},
            ],
        }
        response = api_client.put(url, data=update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        sale.refresh_from_db()
        # Calculate expected total based on sale_type=mayorista
        expected_total = (product_retail.wholesale_price * Decimal("3.000")) + (product_wholesale.wholesale_price * Decimal("1.000"))
        assert sale.total == expected_total
        # Check via response data
        assert response.data["total"] == str(expected_total)

    def test_sale_partial_update_with_missing_customer(
        self, api_client, admin_user, customer, sale
    ):
        """Verify that partially updating a sale without providing customer sets it to None."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:sales-detail", args=[sale.id])
        partial_update_data = {"sale_type": Sale.MAYORISTA}
        response = api_client.patch(url, data=partial_update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        sale.refresh_from_db()
        assert sale.sale_type == Sale.MAYORISTA
        assert sale.customer is None
        # Check via response data
        assert response.data["sale_type"] == Sale.MAYORISTA
        assert response.data["customer"] is None

    def test_sale_create_with_negative_total(
        self, api_client, admin_user, customer, product_retail
    ):
        """Verify that creating a sale with a negative total raises an error."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "sale_details": [{"product": product_retail.id, "quantity": "1.000"}],
            "total": "-10.00",
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "total" in response.data
        expected_error = "Ensure this value is greater than or equal to 0.00."
        assert response.data["total"][0] == expected_error

    def test_sale_create_with_high_precision_quantity(
        self, api_client, admin_user, customer, product_retail
    ):
        """Verify that creating a sale with high precision quantity works correctly."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "sale_details": [{"product": product_retail.id, "quantity": "1.123"}],
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        sale = Sale.objects.get(id=response.data["id"])
        assert sale.sale_details.first().quantity == Decimal("1.123")
        expected_total = product_retail.retail_price * Decimal("1.123")
        assert sale.total == expected_total
        assert response.data["total"] == str(expected_total)

    def test_sale_create_with_no_customer(
        self, api_client, admin_user, product_retail
    ):
        """Verify that creating a sale without specifying a customer is allowed."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "sale_details": [{"product": product_retail.id, "quantity": "2.000"}],
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        sale = Sale.objects.get(id=response.data["id"])
        assert sale.customer is None
        expected_total = product_retail.retail_price * Decimal("2.000")
        assert sale.total == expected_total
        assert response.data["total"] == str(expected_total)

    def test_sale_statistics_with_product_filter(
        self, api_client, admin_user, customer, sale, product_retail, product_wholesale
    ):
        """Verify that the statistics endpoint can filter by product_slug."""
        # Create additional sales
        sale2 = Sale.objects.create(
            user=admin_user,
            customer=customer,
            sale_type=Sale.MAYORISTA,
            payment_method=Sale.TARJETA,
            total=Decimal("50.00"),
            is_active=True,
        )
        SaleDetail.objects.create(
            sale=sale2,
            product=product_retail,
            quantity=Decimal("5"),
            price=product_retail.wholesale_price,
        )
        SaleDetail.objects.create(
            sale=sale2,
            product=product_wholesale,
            quantity=Decimal("2"),
            price=product_wholesale.wholesale_price,
        )
        # Create returns and expenses
        Return.objects.create(sale=sale, total=Decimal("5.00"))
        Expense.objects.create(amount=Decimal("10.00"), date=timezone.now())

        # Authenticate as admin
        api_client.force_authenticate(user=admin_user)

        # Define date range covering all sales
        today = timezone.now().date()
        start_date = today - timedelta(days=7)
        end_date = today + timedelta(days=1)

        # Call the statistics endpoint with product_slug filter
        url = reverse("api:sales-statistics")
        response = api_client.get(
            url,
            {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "product_slug": product_retail.slug,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert "statistics" in response.data
        statistics = response.data["statistics"]

        # Verify statistics for the 'custom' period
        assert "custom" in statistics
        custom_stats = statistics["custom"]
        assert custom_stats["total_sales_count"] == 2
        assert custom_stats["total_sales_amount"] == "70.00"  # 20.00 + 50.00
        assert custom_stats["total_returns_amount"] == "5.00"  # Based on created returns
        assert custom_stats["net_revenue"] == "65.00"  # 70.00 - 5.00
        assert custom_stats["total_expenses"] == "10.00"  # Based on created expenses
        assert "product_slug" in custom_stats
        assert custom_stats["product_slug"] == product_retail.slug
        assert custom_stats["product_name"] == product_retail.name
        assert custom_stats["total_quantity_sold"] == "7.000"  # 2 + 5

    def test_sale_create_with_delivery_and_calculate_total_as_admin(
        self, api_client, admin_user, customer, product_retail
    ):
        """Verify that creating a sale with delivery calculates total correctly."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "sale_details": [{"product": product_retail.id, "quantity": "2.000"}],
            "needs_delivery": True,
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        sale = Sale.objects.get(id=response.data["id"])
        assert sale.needs_delivery is True
        assert sale.state_changes.count() == 1
        assert sale.state_changes.first().state == StateChange.CREADA
        expected_total = product_retail.retail_price * Decimal("2.000")
        assert sale.total == expected_total
        assert response.data["total"] == str(expected_total)

    def test_sale_create_with_multiple_sale_details_as_admin(
        self, api_client, admin_user, customer, product_retail, product_wholesale
    ):
        """Verify that an admin user can create a sale with multiple sale details."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MAYORISTA,
            "payment_method": Sale.TRANSFERENCIA,
            "sale_details": [
                {"product": product_retail.id, "quantity": "3.000"},
                {"product": product_wholesale.id, "quantity": "2.000"},
            ],
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        sale = Sale.objects.get(id=response.data["id"])
        assert sale.sale_details.count() == 2
        expected_total = (product_retail.wholesale_price * Decimal("3.000")) + (product_wholesale.wholesale_price * Decimal("2.000"))
        assert sale.total == expected_total
        assert response.data["total"] == str(expected_total)

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
        assert "sale_details" in response.data
        assert "id" in response.data["sale_details"][0]
        assert "product" in response.data["sale_details"][0]
        assert "does not exist" in response.data["sale_details"][0]["product"][0].lower()

    def test_sale_statistics_with_no_sales(
        self, api_client, admin_user
    ):
        """Verify that the statistics endpoint returns zero values when there are no sales."""
        # Ensure no sales exist
        Sale.objects.all().delete()
        api_client.force_authenticate(user=admin_user)

        # Define date range
        today = timezone.now().date()
        start_date = today - timedelta(days=7)
        end_date = today + timedelta(days=1)

        # Call the statistics endpoint
        url = reverse("api:sales-statistics")
        response = api_client.get(
            url,
            {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "statistics" in response.data
        statistics = response.data["statistics"]
        assert "custom" in statistics
        custom_stats = statistics["custom"]
        assert custom_stats["total_sales_count"] == 0
        assert custom_stats["total_sales_amount"] == "0.00"
        assert custom_stats["total_returns_amount"] == "0.00"
        assert custom_stats["net_revenue"] == "0.00"
        assert custom_stats["total_expenses"] == "0.00"
        assert custom_stats["most_sold_products"] == []

    def test_sale_statistics_with_invalid_date_format(
        self, api_client, admin_user, customer, sale
    ):
        """Verify that the statistics endpoint returns an error for invalid date formats."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:sales-statistics")
        response = api_client.get(
            url,
            {"start_date": "2023-13-01", "end_date": "2023-01-32"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data
        expected_error = "Formato de fecha inválido. Use YYYY-MM-DD."
        assert response.data["non_field_errors"][0] == expected_error

    def test_sale_create_with_missing_sale_details_and_total(
        self, api_client, admin_user, customer
    ):
        """Verify that creating a sale without sale details and total raises an error."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data
        expected_error = "La venta debe tener al menos un detalle o el total."
        assert response.data["non_field_errors"][0] == expected_error

    def test_sale_create_with_sale_details_and_total(
        self, api_client, admin_user, customer, product_retail
    ):
        """Verify that creating a sale with both sale details and total raises an error."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "sale_details": [{"product": product_retail.id, "quantity": "2.000"}],
            "total": "20.00",
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data
        expected_error = "La venta no puede tener detalles y total al mismo tiempo."
        assert response.data["non_field_errors"][0] == expected_error

    def test_sale_create_with_missing_payment_method(
        self, api_client, admin_user, customer, product_retail
    ):
        """Verify that creating a sale without specifying a payment method uses the default."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "sale_details": [{"product": product_retail.id, "quantity": "2.000"}],
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        sale = Sale.objects.get(id=response.data["id"])
        assert sale.payment_method == Sale.EFECTIVO  # Default value
        expected_total = product_retail.retail_price * Decimal("2.000")
        assert sale.total == expected_total
        assert response.data["payment_method"] == Sale.EFECTIVO

    def test_sale_create_with_large_total(
        self, api_client, admin_user, customer, product_retail
    ):
        """Verify that creating a sale with a very large total works correctly."""
        api_client.force_authenticate(user=admin_user)
        large_quantity = "1000000.000"
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "sale_details": [{"product": product_retail.id, "quantity": large_quantity}],
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        sale = Sale.objects.get(id=response.data["id"])
        expected_total = product_retail.retail_price * Decimal(large_quantity)
        assert sale.total == expected_total
        assert response.data["total"] == str(expected_total)

    def test_sale_create_with_multiple_states(
        self, api_client, admin_user, customer, sale
    ):
        """Verify that multiple state changes are handled correctly."""
        api_client.force_authenticate(user=admin_user)
        # Initially, sale has CREADA
        StateChange.objects.create(sale=sale, state=StateChange.CREADA)
        # Cancel the sale
        url_cancel = reverse("api:sales-cancel", args=[sale.id])
        response_cancel = api_client.post(url_cancel)
        assert response_cancel.status_code == status.HTTP_200_OK
        sale.refresh_from_db()
        last_state = sale.get_state()
        assert last_state == StateChange.CANCELADA
        # Attempt to mark as delivered after cancellation
        api_client.force_authenticate(user=delivery_user)
        url_delivered = reverse("api:sales-mark-as-delivered", args=[sale.id])
        response_delivered = api_client.post(url_delivered)
        assert response_delivered.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response_delivered.data
        expected_error = "La venta ya ha sido cancelada."
        assert response_delivered.data["non_field_errors"][0] == expected_error

    def test_sale_create_with_same_product_multiple_times(
        self, api_client, admin_user, customer, product_retail
    ):
        """Verify that creating a sale with the same product multiple times aggregates quantities."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "sale_details": [
                {"product": product_retail.id, "quantity": "1.000"},
                {"product": product_retail.id, "quantity": "2.000"},
            ],
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        sale = Sale.objects.get(id=response.data["id"])
        assert sale.sale_details.count() == 2
        expected_total = product_retail.retail_price * (Decimal("1.000") + Decimal("2.000"))
        assert sale.total == expected_total
        assert response.data["total"] == str(expected_total)

    def test_sale_update_without_changing_details_as_admin(
        self, api_client, admin_user, customer, sale, product_retail
    ):
        """Verify that updating a sale without changing sale details maintains the total."""
        api_client.force_authenticate(user=admin_user)
        original_total = sale.total
        update_data = {
            "sale_type": Sale.MINORISTA,  # No actual change
            "sale_details": [
                {
                    "id": sale.sale_details.first().id,
                    "product": product_retail.id,
                    "quantity": "2.000",
                },
            ],
        }
        response = api_client.put(reverse("api:sales-detail", args=[sale.id]), data=update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        sale.refresh_from_db()
        assert sale.total == original_total
        assert response.data["total"] == str(original_total)

    def test_sale_create_with_high_quantity_precision(
        self, api_client, admin_user, customer, product_retail
    ):
        """Verify that creating a sale with high precision quantities works correctly."""
        api_client.force_authenticate(user=admin_user)
        high_precision_quantity = "1.123"
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": Sale.EFECTIVO,
            "sale_details": [{"product": product_retail.id, "quantity": high_precision_quantity}],
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        print(response.data)
        assert response.status_code == status.HTTP_201_CREATED
        sale = Sale.objects.get(id=response.data["id"])
        assert sale.sale_details.first().quantity == Decimal(high_precision_quantity)

        # Calcular el total esperado y cuantizar a dos decimales
        expected_total = (product_retail.retail_price * Decimal(high_precision_quantity)).quantize(Decimal('0.01'))

        # Verificar que el total en el modelo coincide con el esperado
        assert sale.total == expected_total

        # Verificar que el total en la respuesta coincide con el esperado
        assert response.data["total"] == str(expected_total)

    # def test_sale_statistics_with_no_returns_or_expenses(
    #     self, api_client, admin_user, customer, sale, product_retail, product_wholesale
    # ):
    #     """Verify that statistics are calculated correctly when there are no returns or expenses."""
    #     # Create additional sales
    #     sale2 = Sale.objects.create(
    #         user=admin_user,
    #         customer=customer,
    #         sale_type=Sale.MAYORISTA,
    #         payment_method=Sale.TARJETA,
    #         total=Decimal("50.00"),
    #         is_active=True,
    #     )
    #     SaleDetail.objects.create(
    #         sale=sale2,
    #         product=product_retail,
    #         quantity=Decimal("5"),
    #         price=product_retail.wholesale_price,
    #     )
    #     SaleDetail.objects.create(
    #         sale=sale2,
    #         product=product_wholesale,
    #         quantity=Decimal("2"),
    #         price=product_wholesale.wholesale_price,
    #     )
    #     # No returns or expenses created

    #     # Authenticate as admin
    #     api_client.force_authenticate(user=admin_user)

    #     # Define date range covering all sales
    #     today = timezone.now().date()
    #     start_date = today - timedelta(days=7)
    #     end_date = today + timedelta(days=1)

    #     # Call the statistics endpoint with custom date range
    #     url = reverse("api:sales-statistics")
    #     response = api_client.get(
    #         url,
    #         {
    #             "start_date": start_date.isoformat(),
    #             "end_date": end_date.isoformat(),
    #         },
    #     )

    #     assert response.status_code == status.HTTP_200_OK
    #     assert "statistics" in response.data
    #     statistics = response.data["statistics"]
    #     # Verify statistics for the 'custom' period
    #     assert "custom" in statistics
    #     custom_stats = statistics["custom"]
    #     assert custom_stats["total_sales_count"] == 2
    #     assert custom_stats["total_sales_amount"] == "70.00"  # 20.00 + 50.00
    #     assert custom_stats["total_returns_amount"] == "0.00"  # No returns
    #     assert custom_stats["net_revenue"] == "70.00"  # 70.00 - 0.00
    #     assert custom_stats["total_expenses"] == "0.00"  # No expenses
    #     assert "most_sold_products" in custom_stats
    #     assert len(custom_stats["most_sold_products"]) == 2
    #     assert custom_stats["most_sold_products"][0]["product_name"] == "Retail Product"
    #     assert custom_stats["most_sold_products"][0]["total_quantity_sold"] == "7.000"  # 2 + 5
    #     assert custom_stats["most_sold_products"][1]["product_name"] == "Wholesale Product"
    #     assert custom_stats["most_sold_products"][1]["total_quantity_sold"] == "2.000"

    def test_sale_create_with_large_sale_type(
        self, api_client, admin_user, customer, product_retail
    ):
        """Verify that creating a sale with a non-standard sale_type raises an error."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": "invalid_type",
            "payment_method": Sale.EFECTIVO,
            "sale_details": [{"product": product_retail.id, "quantity": "1.000"}],
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "sale_type" in response.data
        expected_error = '"invalid_type" is not a valid choice.'
        assert response.data["sale_type"][0] == expected_error

    def test_sale_create_with_invalid_payment_method(
        self, api_client, admin_user, customer, product_retail
    ):
        """Verify that creating a sale with an invalid payment method raises an error."""
        api_client.force_authenticate(user=admin_user)
        sale_data = {
            "customer": customer.id,
            "sale_type": Sale.MINORISTA,
            "payment_method": "invalid_method",
            "sale_details": [{"product": product_retail.id, "quantity": "1.000"}],
        }
        response = api_client.post(self.list_url, data=sale_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "payment_method" in response.data
        expected_error = '"invalid_method" is not a valid choice.'
        assert response.data["payment_method"][0] == expected_error
