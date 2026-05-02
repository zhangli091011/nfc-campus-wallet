"""
Unit tests for ProductService.

Tests product management functionality including creation, retrieval,
listing, updates, and validation.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

from core.database import Base
from models.product import Product
from models.booth import Booth
from models.event import Event
from services.product_service import (
    ProductService,
    ProductNotFoundError,
    InvalidBoothError,
    ProductNotInBoothError,
    NegativePriceError,
    NegativeStockError
)


# Test database setup
@pytest.fixture
def test_db():
    """Create a test database session."""
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestSessionLocal()
    
    yield db
    
    db.close()


@pytest.fixture
def product_service(test_db):
    """Create ProductService instance with test database."""
    return ProductService(test_db)


@pytest.fixture
def test_event(test_db):
    """Create a test event in the database."""
    event = Event(
        name="Test Event",
        start_time=datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 1, 18, 0, 0, tzinfo=timezone.utc),
        status="active",
        recharge_enabled=True,
        consume_enabled=True,
        expire_rule="event_end",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)
    return event


@pytest.fixture
def test_booth(test_db, test_event):
    """Create a test booth in the database."""
    booth = Booth(
        event_id=test_event.id,
        name="Test Booth",
        class_name="Class 1A",
        status="active",
        created_at=datetime.now(timezone.utc)
    )
    test_db.add(booth)
    test_db.commit()
    test_db.refresh(booth)
    return booth


@pytest.fixture
def test_booth2(test_db, test_event):
    """Create a second test booth in the database."""
    booth = Booth(
        event_id=test_event.id,
        name="Test Booth 2",
        class_name="Class 2B",
        status="active",
        created_at=datetime.now(timezone.utc)
    )
    test_db.add(booth)
    test_db.commit()
    test_db.refresh(booth)
    return booth


@pytest.fixture
def test_product(test_db, test_booth):
    """Create a test product in the database."""
    product = Product(
        booth_id=test_booth.id,
        name="Test Product",
        price=500,
        cost_price=300,
        stock=100,
        enabled=True,
        created_at=datetime.now(timezone.utc)
    )
    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)
    return product


@pytest.fixture
def disabled_product(test_db, test_booth):
    """Create a disabled test product."""
    product = Product(
        booth_id=test_booth.id,
        name="Disabled Product",
        price=300,
        cost_price=200,
        stock=50,
        enabled=False,
        created_at=datetime.now(timezone.utc)
    )
    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)
    return product


class TestProductServiceCreateProduct:
    """Test ProductService.create_product method."""
    
    def test_create_product_success(self, product_service, test_booth):
        """Test successful product creation with valid booth_id."""
        product = product_service.create_product(
            booth_id=test_booth.id,
            name="奶茶",
            price=500,
            cost_price=300,
            stock=100
        )
        
        # Verify product was created
        assert product.id is not None
        assert product.booth_id == test_booth.id
        assert product.name == "奶茶"
        assert product.price == 500
        assert product.cost_price == 300
        assert product.stock == 100
        assert product.enabled is True
        assert product.created_at is not None
    
    def test_create_product_without_cost_price(self, product_service, test_booth):
        """Test product creation without cost_price."""
        product = product_service.create_product(
            booth_id=test_booth.id,
            name="汉堡",
            price=800
        )
        
        assert product.cost_price is None
        assert product.stock is None
    
    def test_create_product_unlimited_stock(self, product_service, test_booth):
        """Test product creation with unlimited stock (stock=None)."""
        product = product_service.create_product(
            booth_id=test_booth.id,
            name="饮料",
            price=300,
            stock=None
        )
        
        assert product.stock is None
    
    def test_create_product_disabled(self, product_service, test_booth):
        """Test product creation with enabled=False."""
        product = product_service.create_product(
            booth_id=test_booth.id,
            name="Disabled Item",
            price=200,
            enabled=False
        )
        
        assert product.enabled is False
    
    def test_create_product_invalid_booth_id(self, product_service):
        """Test product creation with non-existent booth_id."""
        with pytest.raises(InvalidBoothError) as exc_info:
            product_service.create_product(
                booth_id=99999,
                name="Invalid Product",
                price=500
            )
        
        assert exc_info.value.error_code == "INVALID_BOOTH_ID"
        assert exc_info.value.booth_id == 99999
    
    def test_create_product_negative_price(self, product_service, test_booth):
        """Test product creation with negative price."""
        with pytest.raises(NegativePriceError) as exc_info:
            product_service.create_product(
                booth_id=test_booth.id,
                name="Negative Price Product",
                price=-100
            )
        
        assert exc_info.value.error_code == "NEGATIVE_PRICE"
        assert exc_info.value.field_name == "price"
        assert exc_info.value.value == -100
    
    def test_create_product_negative_cost_price(self, product_service, test_booth):
        """Test product creation with negative cost_price."""
        with pytest.raises(NegativePriceError) as exc_info:
            product_service.create_product(
                booth_id=test_booth.id,
                name="Negative Cost Product",
                price=500,
                cost_price=-200
            )
        
        assert exc_info.value.error_code == "NEGATIVE_PRICE"
        assert exc_info.value.field_name == "cost_price"
        assert exc_info.value.value == -200
    
    def test_create_product_negative_stock(self, product_service, test_booth):
        """Test product creation with negative stock."""
        with pytest.raises(NegativeStockError) as exc_info:
            product_service.create_product(
                booth_id=test_booth.id,
                name="Negative Stock Product",
                price=500,
                stock=-10
            )
        
        assert exc_info.value.error_code == "NEGATIVE_STOCK"
        assert exc_info.value.value == -10
    
    def test_create_product_zero_price(self, product_service, test_booth):
        """Test product creation with zero price (should be allowed)."""
        product = product_service.create_product(
            booth_id=test_booth.id,
            name="Free Item",
            price=0
        )
        
        assert product.price == 0


class TestProductServiceGetProduct:
    """Test ProductService.get_product method."""
    
    def test_get_product_success(self, product_service, test_product):
        """Test retrieving existing product."""
        product = product_service.get_product(test_product.id)
        
        assert product.id == test_product.id
        assert product.name == "Test Product"
        assert product.price == 500
        assert product.cost_price == 300
        assert product.stock == 100
        assert product.enabled is True
    
    def test_get_product_not_found(self, product_service):
        """Test retrieving non-existent product."""
        with pytest.raises(ProductNotFoundError) as exc_info:
            product_service.get_product(99999)
        
        assert exc_info.value.error_code == "PRODUCT_NOT_FOUND"
        assert exc_info.value.product_id == 99999


class TestProductServiceListProducts:
    """Test ProductService.list_products method."""
    
    def test_list_all_products(self, product_service, test_product, disabled_product):
        """Test listing all products without filters."""
        products = product_service.list_products()
        
        assert len(products) == 2
        product_ids = [p.id for p in products]
        assert test_product.id in product_ids
        assert disabled_product.id in product_ids
    
    def test_list_products_by_booth_id(self, product_service, test_booth, test_booth2, test_product):
        """Test listing products filtered by booth_id."""
        # Create product for booth2
        product2 = Product(
            booth_id=test_booth2.id,
            name="Product in Booth 2",
            price=600,
            enabled=True,
            created_at=datetime.now(timezone.utc)
        )
        product_service.db.add(product2)
        product_service.db.commit()
        
        # List products for test_booth only
        products = product_service.list_products(booth_id=test_booth.id)
        
        assert len(products) >= 1
        for product in products:
            assert product.booth_id == test_booth.id
    
    def test_list_products_by_enabled_status(self, product_service, test_product, disabled_product):
        """Test listing products filtered by enabled status."""
        # List only enabled products
        enabled_products = product_service.list_products(enabled=True)
        
        assert len(enabled_products) >= 1
        for product in enabled_products:
            assert product.enabled is True
        
        # List only disabled products
        disabled_products = product_service.list_products(enabled=False)
        
        assert len(disabled_products) >= 1
        for product in disabled_products:
            assert product.enabled is False
    
    def test_list_products_with_limit_and_offset(self, product_service, test_product, disabled_product):
        """Test listing products with pagination."""
        # Get first product
        products_page1 = product_service.list_products(limit=1, offset=0)
        assert len(products_page1) == 1
        
        # Get second product
        products_page2 = product_service.list_products(limit=1, offset=1)
        assert len(products_page2) == 1
        
        # Verify they are different products
        assert products_page1[0].id != products_page2[0].id
    
    def test_list_products_empty_result(self, product_service):
        """Test listing products when no products exist."""
        products = product_service.list_products(booth_id=99999)
        
        assert len(products) == 0


class TestProductServiceUpdateProduct:
    """Test ProductService.update_product method."""
    
    def test_update_product_name(self, product_service, test_product):
        """Test updating product name."""
        updated_product = product_service.update_product(
            product_id=test_product.id,
            name="Updated Product Name"
        )
        
        assert updated_product.id == test_product.id
        assert updated_product.name == "Updated Product Name"
        # Other fields should remain unchanged
        assert updated_product.price == 500
        assert updated_product.cost_price == 300
    
    def test_update_product_price(self, product_service, test_product):
        """Test updating product price."""
        updated_product = product_service.update_product(
            product_id=test_product.id,
            price=600
        )
        
        assert updated_product.price == 600
        # Other fields should remain unchanged
        assert updated_product.name == "Test Product"
    
    def test_update_product_cost_price(self, product_service, test_product):
        """Test updating product cost_price."""
        updated_product = product_service.update_product(
            product_id=test_product.id,
            cost_price=350
        )
        
        assert updated_product.cost_price == 350
    
    def test_update_product_stock(self, product_service, test_product):
        """Test updating product stock."""
        updated_product = product_service.update_product(
            product_id=test_product.id,
            stock=80
        )
        
        assert updated_product.stock == 80
    
    def test_update_product_enabled(self, product_service, test_product):
        """Test updating product enabled status."""
        updated_product = product_service.update_product(
            product_id=test_product.id,
            enabled=False
        )
        
        assert updated_product.enabled is False
    
    def test_update_product_multiple_fields(self, product_service, test_product):
        """Test updating multiple product fields at once."""
        updated_product = product_service.update_product(
            product_id=test_product.id,
            name="Multi-Update Product",
            price=700,
            cost_price=400,
            stock=50,
            enabled=False
        )
        
        assert updated_product.name == "Multi-Update Product"
        assert updated_product.price == 700
        assert updated_product.cost_price == 400
        assert updated_product.stock == 50
        assert updated_product.enabled is False
    
    def test_update_product_not_found(self, product_service):
        """Test updating non-existent product."""
        with pytest.raises(ProductNotFoundError) as exc_info:
            product_service.update_product(
                product_id=99999,
                name="Non-existent Product"
            )
        
        assert exc_info.value.error_code == "PRODUCT_NOT_FOUND"
    
    def test_update_product_negative_price(self, product_service, test_product):
        """Test updating product with negative price."""
        with pytest.raises(NegativePriceError) as exc_info:
            product_service.update_product(
                product_id=test_product.id,
                price=-100
            )
        
        assert exc_info.value.error_code == "NEGATIVE_PRICE"
        assert exc_info.value.field_name == "price"
    
    def test_update_product_negative_cost_price(self, product_service, test_product):
        """Test updating product with negative cost_price."""
        with pytest.raises(NegativePriceError) as exc_info:
            product_service.update_product(
                product_id=test_product.id,
                cost_price=-200
            )
        
        assert exc_info.value.error_code == "NEGATIVE_PRICE"
        assert exc_info.value.field_name == "cost_price"
    
    def test_update_product_negative_stock(self, product_service, test_product):
        """Test updating product with negative stock."""
        with pytest.raises(NegativeStockError) as exc_info:
            product_service.update_product(
                product_id=test_product.id,
                stock=-10
            )
        
        assert exc_info.value.error_code == "NEGATIVE_STOCK"
    
    def test_update_product_no_changes(self, product_service, test_product):
        """Test updating product with no fields specified."""
        updated_product = product_service.update_product(
            product_id=test_product.id
        )
        
        # Product should remain unchanged
        assert updated_product.name == "Test Product"
        assert updated_product.price == 500
        assert updated_product.cost_price == 300


class TestProductServiceValidateProductBelongsToBooth:
    """Test ProductService.validate_product_belongs_to_booth method."""
    
    def test_validate_product_belongs_to_booth_success(self, product_service, test_product, test_booth):
        """Test validation succeeds when product belongs to booth."""
        product = product_service.validate_product_belongs_to_booth(
            product_id=test_product.id,
            booth_id=test_booth.id
        )
        
        assert product.id == test_product.id
        assert product.booth_id == test_booth.id
    
    def test_validate_product_belongs_to_booth_wrong_booth(self, product_service, test_product, test_booth2):
        """Test validation fails when product belongs to different booth."""
        with pytest.raises(ProductNotInBoothError) as exc_info:
            product_service.validate_product_belongs_to_booth(
                product_id=test_product.id,
                booth_id=test_booth2.id
            )
        
        assert exc_info.value.error_code == "PRODUCT_NOT_IN_BOOTH"
        assert exc_info.value.product_id == test_product.id
        assert exc_info.value.booth_id == test_booth2.id
    
    def test_validate_product_belongs_to_booth_product_not_found(self, product_service, test_booth):
        """Test validation fails when product doesn't exist."""
        with pytest.raises(ProductNotFoundError) as exc_info:
            product_service.validate_product_belongs_to_booth(
                product_id=99999,
                booth_id=test_booth.id
            )
        
        assert exc_info.value.error_code == "PRODUCT_NOT_FOUND"


class TestProductServiceIntegration:
    """Integration tests for complete product management flow."""
    
    def test_complete_product_lifecycle(self, product_service, test_booth):
        """Test complete product lifecycle: create -> get -> update -> validate."""
        # Step 1: Create product
        product = product_service.create_product(
            booth_id=test_booth.id,
            name="Lifecycle Test Product",
            price=500,
            cost_price=300,
            stock=100
        )
        product_id = product.id
        
        # Step 2: Get product
        retrieved_product = product_service.get_product(product_id)
        assert retrieved_product.name == "Lifecycle Test Product"
        assert retrieved_product.enabled is True
        
        # Step 3: Validate product belongs to booth
        product_service.validate_product_belongs_to_booth(product_id, test_booth.id)
        
        # Step 4: Update product price and stock
        updated_product = product_service.update_product(
            product_id=product_id,
            price=600,
            stock=80
        )
        assert updated_product.price == 600
        assert updated_product.stock == 80
        
        # Step 5: Disable product
        disabled_product = product_service.update_product(
            product_id=product_id,
            enabled=False
        )
        assert disabled_product.enabled is False
    
    def test_list_products_multiple_booths(self, product_service, test_booth, test_booth2):
        """Test listing products across multiple booths."""
        # Create products for each booth
        product1 = product_service.create_product(test_booth.id, "Product 1", 500)
        product2 = product_service.create_product(test_booth.id, "Product 2", 600)
        product3 = product_service.create_product(test_booth2.id, "Product 3", 700)
        
        # List all products
        all_products = product_service.list_products()
        assert len(all_products) == 3
        
        # List products for booth1
        booth1_products = product_service.list_products(booth_id=test_booth.id)
        assert len(booth1_products) == 2
        
        # List products for booth2
        booth2_products = product_service.list_products(booth_id=test_booth2.id)
        assert len(booth2_products) == 1
    
    def test_product_validation_across_booths(self, product_service, test_booth, test_booth2):
        """Test product validation fails when accessing product from wrong booth."""
        # Create product in booth1
        product = product_service.create_product(test_booth.id, "Booth 1 Product", 500)
        
        # Validation should succeed for booth1
        product_service.validate_product_belongs_to_booth(product.id, test_booth.id)
        
        # Validation should fail for booth2
        with pytest.raises(ProductNotInBoothError):
            product_service.validate_product_belongs_to_booth(product.id, test_booth2.id)
