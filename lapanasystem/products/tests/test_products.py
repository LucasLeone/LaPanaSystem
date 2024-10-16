"""Products tests."""

# Django
from django.urls import reverse
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

# Django REST Framework
from rest_framework.test import APIClient
from rest_framework import status

# Models
from lapanasystem.products.models import Product, ProductCategory, ProductBrand
from lapanasystem.users.models import User

# Serializers
from lapanasystem.products.serializers import (
    ProductSerializer,
    ProductBrandSerializer,
    ProductCategorySerializer,
)

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
def category_data():
    return {"name": "Beverages", "description": "Drinks and beverages"}


@pytest.fixture
def brand_data():
    return {"name": "Coca Cola", "description": "Coca Cola brand"}


@pytest.fixture
def category(category_data):
    return ProductCategory.objects.create(**category_data)


@pytest.fixture
def brand(brand_data):
    return ProductBrand.objects.create(**brand_data)


@pytest.fixture
def product_data(category, brand):
    return {
        "barcode": "1234567890123",
        "name": "Coca Cola 1L",
        "retail_price": "1.50",
        "wholesale_price": "1.20",
        "weight": "1.0",
        "weight_unit": "kg",
        "description": "1 liter bottle of Coca Cola",
        "category": category,
        "brand": brand,
    }


@pytest.mark.django_db
class TestProductModel:
    def test_product_str(self, product_data):
        product = Product.objects.create(**product_data)
        assert str(product) == product.name

    def test_product_slug_creation(self, product_data):
        product = Product.objects.create(**product_data)
        assert product.slug == "coca-cola-1l"

    def test_product_slug_uniqueness(self, product_data):
        product1 = Product.objects.create(**product_data)
        product_data["barcode"] = "9876543210987"
        product2 = Product.objects.create(**product_data)
        assert product1.slug == "coca-cola-1l"
        assert product2.slug == "coca-cola-1l-1"


@pytest.mark.django_db
class TestProductSerializer:
    def test_valid_product_serializer(self, product_data):
        product_data["category"] = product_data["category"].id
        product_data["brand"] = product_data["brand"].id
        serializer = ProductSerializer(data=product_data)
        assert serializer.is_valid(), serializer.errors
        product = serializer.save()
        assert product.name == product_data["name"]
        assert product.barcode == product_data["barcode"]
        assert str(product.retail_price) == product_data["retail_price"]
        assert str(product.wholesale_price) == product_data["wholesale_price"]
        assert Decimal(product.weight) == Decimal(product_data["weight"])
        assert product.weight_unit == product_data["weight_unit"]
        assert product.description == product_data["description"]
        assert product.category.id == product_data["category"]
        assert product.brand.id == product_data["brand"]

    def test_invalid_weight_unit(self, product_data):
        product_data["weight_unit"] = "invalid_unit"
        product_data["category"] = product_data["category"].id
        product_data["brand"] = product_data["brand"].id
        serializer = ProductSerializer(data=product_data)
        assert not serializer.is_valid()
        assert "weight_unit" in serializer.errors

    def test_duplicate_product(self, product_data):
        """Verify that creating a duplicate product raises a validation error."""
        product_data_create = product_data.copy()
        product_data_create["category"] = product_data_create["category"].id
        product_data_create["brand"] = product_data_create["brand"].id
        serializer = ProductSerializer(data=product_data_create)
        assert serializer.is_valid(), serializer.errors
        serializer.save()

        product_data_duplicate = product_data.copy()
        product_data_duplicate["category"] = product_data_duplicate["category"].id
        product_data_duplicate["brand"] = product_data_duplicate["brand"].id
        product_data_duplicate["barcode"] = "9876543210987"
        serializer = ProductSerializer(data=product_data_duplicate)
        assert not serializer.is_valid()
        print("Serializer errors:", serializer.errors)
        assert "non_field_errors" in serializer.errors
        expected_error = "Ya existe un producto con este nombre, peso y unidad de peso."
        assert serializer.errors["non_field_errors"][0] == expected_error



@pytest.mark.django_db
class TestProductAPI:
    """Product API tests."""

    @pytest.fixture(autouse=True)
    def setup_urls(self):
        self.list_url = reverse("api:products-list")

    def test_product_create_as_admin(self, api_client, admin_user, product_data):
        """Verify that an admin user can create a product."""
        api_client.force_authenticate(user=admin_user)
        product_data_api = product_data.copy()
        product_data_api["category"] = product_data_api["category"].id
        product_data_api["brand"] = product_data_api["brand"].id
        response = api_client.post(self.list_url, data=product_data_api)
        assert response.status_code == status.HTTP_201_CREATED
        assert Product.objects.count() == 1
        product = Product.objects.first()
        assert product.name == product_data["name"]

    def test_product_create_as_seller(self, api_client, seller_user, product_data):
        """Verify that a seller user can create a product."""
        api_client.force_authenticate(user=seller_user)
        product_data_api = product_data.copy()
        product_data_api["category"] = product_data_api["category"].id
        product_data_api["brand"] = product_data_api["brand"].id
        response = api_client.post(self.list_url, data=product_data_api)
        assert response.status_code == status.HTTP_201_CREATED
        assert Product.objects.count() == 1

    def test_product_create_unauthenticated(self, api_client, product_data):
        """Verify that an unauthenticated user cannot create a product."""
        product_data_api = product_data.copy()
        product_data_api["category"] = product_data_api["category"].id
        product_data_api["brand"] = product_data_api["brand"].id
        response = api_client.post(self.list_url, data=product_data_api)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_product_list(self, api_client, admin_user, product_data):
        """Verify that an admin user can list products."""
        Product.objects.create(**product_data)
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == product_data['name']

    def test_product_retrieve(self, api_client, admin_user, product_data):
        """Verify that an admin user can retrieve a product."""
        product = Product.objects.create(**product_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:products-detail", args=[product.slug])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == product_data["name"]

    def test_product_update(self, api_client, admin_user, product_data, category, brand):
        """Verify that an admin user can update a product."""
        product = Product.objects.create(**product_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:products-detail", args=[product.slug])
        updated_data = product_data.copy()
        updated_data["name"] = "Coca Cola 2L"
        updated_data["category"] = category.id
        updated_data["brand"] = brand.id
        response = api_client.put(url, data=updated_data)
        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert product.name == "Coca Cola 2L"

    def test_product_partial_update(self, api_client, admin_user, product_data):
        """Verify that an admin user can partially update a product."""
        product = Product.objects.create(**product_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:products-detail", args=[product.slug])
        response = api_client.patch(url, data={"name": "Coca Cola Zero"})
        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert product.name == "Coca Cola Zero"

    def test_product_delete_as_admin(self, api_client, admin_user, product_data):
        """Verify that an admin user can soft delete a product."""
        product = Product.objects.create(**product_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:products-detail", args=[product.slug])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert not product.is_active
        response = api_client.get(self.list_url)
        assert len(response.data['results']) == 0

    def test_product_delete_as_seller(self, api_client, seller_user, product_data):
        """Verify that a seller user cannot delete a product."""
        product = Product.objects.create(**product_data)
        api_client.force_authenticate(user=seller_user)
        url = reverse("api:products-detail", args=[product.slug])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_product_filter_by_category(self, api_client, admin_user, brand):
        """Verify that an admin user can filter products by category."""
        category1 = ProductCategory.objects.create(name="Beverages", description="Drinks")
        category2 = ProductCategory.objects.create(name="Snacks", description="Snacks")

        Product.objects.create(
            barcode="1111111111111",
            name="Product A",
            retail_price="1.00",
            wholesale_price="0.80",
            category=category1,
            brand=brand,
        )
        Product.objects.create(
            barcode="2222222222222",
            name="Product B",
            retail_price="2.00",
            wholesale_price="1.60",
            category=category2,
            brand=brand,
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {"category": category1.id})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]["name"] == "Product A"

    def test_product_search(self, api_client, admin_user, category, brand):
        """Verify that an admin user can search products by name or barcode."""
        Product.objects.create(
            barcode="1234567890123",
            name="Coca Cola",
            retail_price="1.50",
            wholesale_price="1.20",
            category=category,
            brand=brand,
        )
        Product.objects.create(
            barcode="9876543210987",
            name="Pepsi",
            retail_price="1.40",
            wholesale_price="1.10",
            category=category,
            brand=brand,
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {"search": "Coca"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]["name"] == "Coca Cola"

    def test_product_ordering(self, api_client, admin_user, category, brand):
        """Verify that an admin user can order products by name."""
        Product.objects.create(
            barcode="1111111111111",
            name="B Product",
            retail_price="1.00",
            wholesale_price="0.80",
            category=category,
            brand=brand,
        )
        Product.objects.create(
            barcode="2222222222222",
            name="A Product",
            retail_price="2.00",
            wholesale_price="1.60",
            category=category,
            brand=brand,
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url, {"ordering": "name"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'][0]["name"] == "A Product"
        assert response.data['results'][1]["name"] == "B Product"

    def test_permissions_create(self, api_client, product_data):
        """Verify that an unauthenticated user cannot create a product."""
        product_data_api = product_data.copy()
        product_data_api["category"] = product_data_api["category"].id
        product_data_api["brand"] = product_data_api["brand"].id
        response = api_client.post(self.list_url, data=product_data_api)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_permissions_list(self, api_client):
        """Verify that an unauthenticated user cannot list products."""
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_permissions_update(self, api_client, product_data):
        """Verify that an unauthenticated user cannot update a product."""
        product = Product.objects.create(**product_data)
        url = reverse("api:products-detail", args=[product.slug])
        product_data_api = product_data.copy()
        product_data_api["category"] = product_data_api["category"].id
        product_data_api["brand"] = product_data_api["brand"].id
        response = api_client.put(url, data=product_data_api)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_permissions_delete(self, api_client, product_data):
        """Verify that an unauthenticated user cannot delete a product."""
        product = Product.objects.create(**product_data)
        url = reverse("api:products-detail", args=[product.slug])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestProductBrandModel:
    def test_brand_str(self, brand_data):
        brand = ProductBrand.objects.create(**brand_data)
        assert str(brand) == brand.name


@pytest.mark.django_db
class TestProductBrandSerializer:
    def test_valid_brand_serializer(self, brand_data):
        serializer = ProductBrandSerializer(data=brand_data)
        assert serializer.is_valid(), serializer.errors
        brand = serializer.save()
        assert brand.name == brand_data["name"]
        assert brand.description == brand_data["description"]

    def test_duplicate_brand_name(self, brand_data):
        """Verify that duplicate brand names are not allowed."""
        serializer = ProductBrandSerializer(data=brand_data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        serializer = ProductBrandSerializer(data=brand_data)
        assert not serializer.is_valid()
        assert "name" in serializer.errors
        expected_error = "Ya existe una marca con este nombre."
        assert serializer.errors["name"][0] == expected_error


@pytest.mark.django_db
class TestProductBrandAPI:
    """ProductBrand API tests."""

    @pytest.fixture(autouse=True)
    def setup_urls(self):
        self.list_url = reverse("api:product-brands-list")

    def test_brand_create_as_admin(self, api_client, admin_user, brand_data):
        """Verify that an admin user can create a brand."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(self.list_url, data=brand_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert ProductBrand.objects.count() == 1
        brand = ProductBrand.objects.first()
        assert brand.name == brand_data["name"]

    def test_brand_create_as_seller(self, api_client, seller_user, brand_data):
        """Verify that a seller user can create a brand."""
        api_client.force_authenticate(user=seller_user)
        response = api_client.post(self.list_url, data=brand_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert ProductBrand.objects.count() == 1

    def test_brand_create_unauthenticated(self, api_client, brand_data):
        """Verify that an unauthenticated user cannot create a brand."""
        response = api_client.post(self.list_url, data=brand_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_brand_list(self, api_client, admin_user, brand_data):
        """Verify that an admin user can list brands."""
        ProductBrand.objects.create(**brand_data)
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_brand_retrieve(self, api_client, admin_user, brand_data):
        """Verify that an admin user can retrieve a brand."""
        brand = ProductBrand.objects.create(**brand_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:product-brands-detail", args=[brand.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == brand_data["name"]

    def test_brand_update(self, api_client, admin_user, brand_data):
        """Verify that an admin user can update a brand."""
        brand = ProductBrand.objects.create(**brand_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:product-brands-detail", args=[brand.id])
        updated_data = brand_data.copy()
        updated_data["name"] = "Pepsi"
        response = api_client.put(url, data=updated_data)
        assert response.status_code == status.HTTP_200_OK
        brand.refresh_from_db()
        assert brand.name == "Pepsi"

    def test_brand_partial_update(self, api_client, admin_user, brand_data):
        """Verify that an admin user can partially update a brand."""
        brand = ProductBrand.objects.create(**brand_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:product-brands-detail", args=[brand.id])
        response = api_client.patch(url, data={"name": "Pepsi"})
        assert response.status_code == status.HTTP_200_OK
        brand.refresh_from_db()
        assert brand.name == "Pepsi"

    def test_brand_delete_as_admin(self, api_client, admin_user, brand_data):
        """Verify that an admin user can soft delete a brand."""
        brand = ProductBrand.objects.create(**brand_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:product-brands-detail", args=[brand.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        brand.refresh_from_db()
        assert not brand.is_active
        response = api_client.get(self.list_url)
        assert len(response.data['results']) == 0

    def test_brand_delete_as_seller(self, api_client, seller_user, brand_data):
        """Verify that a seller user cannot delete a brand."""
        brand = ProductBrand.objects.create(**brand_data)
        api_client.force_authenticate(user=seller_user)
        url = reverse("api:product-brands-detail", args=[brand.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestProductCategoryModel:
    def test_category_str(self, category_data):
        category = ProductCategory.objects.create(**category_data)
        assert str(category) == category.name


@pytest.mark.django_db
class TestProductCategorySerializer:
    def test_valid_category_serializer(self, category_data):
        serializer = ProductCategorySerializer(data=category_data)
        assert serializer.is_valid(), serializer.errors
        category = serializer.save()
        assert category.name == category_data["name"]
        assert category.description == category_data["description"]

    def test_duplicate_category_name(self, category_data):
        """Verify that duplicate category names are not allowed."""
        serializer = ProductCategorySerializer(data=category_data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        serializer = ProductCategorySerializer(data=category_data)
        assert not serializer.is_valid()
        assert "name" in serializer.errors
        expected_error = "Ya existe una categoría con este nombre."
        assert serializer.errors["name"][0] == expected_error


@pytest.mark.django_db
class TestProductCategoryAPI:
    """ProductCategory API tests."""

    @pytest.fixture(autouse=True)
    def setup_urls(self):
        self.list_url = reverse("api:product-categories-list")

    def test_category_create_as_admin(self, api_client, admin_user, category_data):
        """Verify that an admin user can create a category."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(self.list_url, data=category_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert ProductCategory.objects.count() == 1
        category = ProductCategory.objects.first()
        assert category.name == category_data["name"]

    def test_category_create_as_seller(self, api_client, seller_user, category_data):
        """Verify that a seller user can create a category."""
        api_client.force_authenticate(user=seller_user)
        response = api_client.post(self.list_url, data=category_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert ProductCategory.objects.count() == 1

    def test_category_create_unauthenticated(self, api_client, category_data):
        """Verify that an unauthenticated user cannot create a category."""
        response = api_client.post(self.list_url, data=category_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_category_list(self, api_client, admin_user, category_data):
        """Verify that an admin user can list categories."""
        ProductCategory.objects.create(**category_data)
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_category_retrieve(self, api_client, admin_user, category_data):
        """Verify that an admin user can retrieve a category."""
        category = ProductCategory.objects.create(**category_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:product-categories-detail", args=[category.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == category_data["name"]

    def test_category_update(self, api_client, admin_user, category_data):
        """Verify that an admin user can update a category."""
        category = ProductCategory.objects.create(**category_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:product-categories-detail", args=[category.id])
        updated_data = category_data.copy()
        updated_data["name"] = "Snacks"
        response = api_client.put(url, data=updated_data)
        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert category.name == "Snacks"

    def test_category_partial_update(self, api_client, admin_user, category_data):
        """Verify that an admin user can partially update a category."""
        category = ProductCategory.objects.create(**category_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:product-categories-detail", args=[category.id])
        response = api_client.patch(url, data={"name": "Snacks"})
        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert category.name == "Snacks"

    def test_category_delete_as_admin(self, api_client, admin_user, category_data):
        """Verify that an admin user can soft delete a category."""
        category = ProductCategory.objects.create(**category_data)
        api_client.force_authenticate(user=admin_user)
        url = reverse("api:product-categories-detail", args=[category.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert not category.is_active
        response = api_client.get(self.list_url)
        assert len(response.data['results']) == 0

    def test_category_delete_as_seller(self, api_client, seller_user, category_data):
        """Verify that a seller user cannot delete a category."""
        category = ProductCategory.objects.create(**category_data)
        api_client.force_authenticate(user=seller_user)
        url = reverse("api:product-categories-detail", args=[category.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
