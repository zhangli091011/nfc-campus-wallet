"""
Integration tests for product routes.

Tests product management API endpoints including authentication,
authorization, and error handling.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

from app.main import create_app
from core.database import Base, get_db
from core.security import create_access_token
from core.config import get_settings
from models.user import User
from models.event import Event
from models.booth import Booth
from models.product import Product


# Test database setup
@pytest.fixture
def test_db():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestSessionLocal()
    
    yield db
    
    db.close()


@pytest.fixture
def app(test_db):
    """Create FastAPI test application."""
    app = create_app()
    
    # Override database dependency
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_event(test_db):
    """Create a test event."""
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
    """Create a test booth."""
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
def test_product(test_db, test_booth):
    """Create a test product."""
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
def super_admin_user(test_db):
    """Create a super admin user."""
    from core.security import hash_password
    user = User(
        username="super_admin",
        password_hash=hash_password("password123"),
        role="super_admin",
        booth_id=None,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def event_admin_user(test_db):
    """Create an event admin user."""
    from core.security import hash_password
    user = User(
        username="event_admin",
        password_hash=hash_password("password123"),
        role="event_admin",
        booth_id=None,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def booth_cashier_user(test_db, test_booth):
    """Create a booth cashier user."""
    from core.security import hash_password
    user = User(
        username="booth_cashier",
        password_hash=hash_password("password123"),
        role="booth_cashier",
        booth_id=test_booth.id,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def issuer_user(test_db):
    """Create an issuer user."""
    from core.security import hash_password
    user = User(
        username="issuer",
        password_hash=hash_password("password123"),
        role="issuer",
        booth_id=None,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


def get_auth_header(user: User) -> dict:
    """Generate authorization header for user."""
    settings = get_settings()
    token = create_access_token(
        user=user,
        jwt_secret_key=settings.jwt_secret_key,
        jwt_algorithm=settings.jwt_algorithm,
        jwt_expiration_minutes=settings.jwt_expiration_minutes
    )
    return {"Authorization": f"Bearer {token}"}


class TestCreateProduct:
    """Test POST /products endpoint."""
    
    def test_create_product_as_super_admin(self, client, test_booth, super_admin_user):
        """Test super_admin can create product."""
        headers = get_auth_header(super_admin_user)
        
        response = client.post(
            "/products",
            json={
                "booth_id": test_booth.id,
                "name": "奶茶",
                "price": 500,
                "cost_price": 300,
                "stock": 100
            },
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "奶茶"
        assert data["price"] == 500
        assert data["cost_price"] == 300
        assert data["stock"] == 100
        assert data["booth_id"] == test_booth.id
        assert data["enabled"] is True
        assert "id" in data
        assert "created_at" in data
    
    def test_create_product_as_event_admin(self, client, test_booth, event_admin_user):
        """Test event_admin can create product."""
        headers = get_auth_header(event_admin_user)
        
        response = client.post(
            "/products",
            json={
                "booth_id": test_booth.id,
                "name": "汉堡",
                "price": 800,
                "cost_price": 500,
                "stock": 50
            },
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "汉堡"
        assert data["price"] == 800
    
    def test_create_product_as_booth_cashier_forbidden(self, client, test_booth, booth_cashier_user):
        """Test booth_cashier cannot create product."""
        headers = get_auth_header(booth_cashier_user)
        
        response = client.post(
            "/products",
            json={
                "booth_id": test_booth.id,
                "name": "Unauthorized Product",
                "price": 600
            },
            headers=headers
        )
        
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "booth_cashier" in data["detail"]
    
    def test_create_product_as_issuer_forbidden(self, client, test_booth, issuer_user):
        """Test issuer cannot create product."""
        headers = get_auth_header(issuer_user)
        
        response = client.post(
            "/products",
            json={
                "booth_id": test_booth.id,
                "name": "Unauthorized Product",
                "price": 600
            },
            headers=headers
        )
        
        assert response.status_code == 403
    
    def test_create_product_without_auth(self, client, test_booth):
        """Test creating product without authentication fails."""
        response = client.post(
            "/products",
            json={
                "booth_id": test_booth.id,
                "name": "Unauthorized Product",
                "price": 600
            }
        )
        
        assert response.status_code == 403
    
    def test_create_product_invalid_booth_id(self, client, super_admin_user):
        """Test creating product with non-existent booth_id."""
        headers = get_auth_header(super_admin_user)
        
        response = client.post(
            "/products",
            json={
                "booth_id": 99999,
                "name": "Invalid Product",
                "price": 600
            },
            headers=headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INVALID_BOOTH_ID"
    
    def test_create_product_negative_price(self, client, test_booth, super_admin_user):
        """Test creating product with negative price fails."""
        headers = get_auth_header(super_admin_user)
        
        response = client.post(
            "/products",
            json={
                "booth_id": test_booth.id,
                "name": "Invalid Product",
                "price": -100
            },
            headers=headers
        )
        
        assert response.status_code == 422  # Pydantic validation error
    
    def test_create_product_with_unlimited_stock(self, client, test_booth, super_admin_user):
        """Test creating product with unlimited stock (stock=null)."""
        headers = get_auth_header(super_admin_user)
        
        response = client.post(
            "/products",
            json={
                "booth_id": test_booth.id,
                "name": "Unlimited Product",
                "price": 500,
                "stock": None
            },
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["stock"] is None


class TestListProducts:
    """Test GET /products endpoint."""
    
    def test_list_products_as_super_admin(self, client, test_product, super_admin_user):
        """Test super_admin can list products."""
        headers = get_auth_header(super_admin_user)
        
        response = client.get("/products", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Verify product data structure
        product = data[0]
        assert "id" in product
        assert "name" in product
        assert "price" in product
        assert "booth_id" in product
        assert "enabled" in product
        assert "created_at" in product
    
    def test_list_products_as_event_admin(self, client, test_product, event_admin_user):
        """Test event_admin can list products."""
        headers = get_auth_header(event_admin_user)
        
        response = client.get("/products", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_list_products_as_booth_cashier_own_booth(self, client, test_product, booth_cashier_user):
        """Test booth_cashier can list their own booth products."""
        headers = get_auth_header(booth_cashier_user)
        
        response = client.get("/products", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # All products should belong to cashier's booth
        for product in data:
            assert product["booth_id"] == booth_cashier_user.booth_id
    
    def test_list_products_as_booth_cashier_other_booth_forbidden(
        self, client, test_db, test_event, booth_cashier_user
    ):
        """Test booth_cashier cannot list other booth products."""
        # Create another booth
        other_booth = Booth(
            event_id=test_event.id,
            name="Other Booth",
            class_name="Class 2B",
            status="active",
            created_at=datetime.now(timezone.utc)
        )
        test_db.add(other_booth)
        test_db.commit()
        test_db.refresh(other_booth)
        
        headers = get_auth_header(booth_cashier_user)
        
        response = client.get(f"/products?booth_id={other_booth.id}", headers=headers)
        
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "Access denied" in data["detail"]
    
    def test_list_products_filter_by_booth_id(self, client, test_booth, test_product, super_admin_user):
        """Test listing products filtered by booth_id."""
        headers = get_auth_header(super_admin_user)
        
        response = client.get(f"/products?booth_id={test_booth.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # All products should belong to the specified booth
        for product in data:
            assert product["booth_id"] == test_booth.id
    
    def test_list_products_filter_by_enabled(self, client, test_product, super_admin_user):
        """Test listing products filtered by enabled status."""
        headers = get_auth_header(super_admin_user)
        
        response = client.get("/products?enabled=true", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # All products should be enabled
        for product in data:
            assert product["enabled"] is True
    
    def test_list_products_as_issuer_forbidden(self, client, issuer_user):
        """Test issuer cannot list products."""
        headers = get_auth_header(issuer_user)
        
        response = client.get("/products", headers=headers)
        
        assert response.status_code == 403
    
    def test_list_products_without_auth(self, client):
        """Test listing products without authentication fails."""
        response = client.get("/products")
        
        assert response.status_code == 403


class TestUpdateProduct:
    """Test PATCH /products/{product_id} endpoint."""
    
    def test_update_product_as_super_admin(self, client, test_product, super_admin_user):
        """Test super_admin can update product."""
        headers = get_auth_header(super_admin_user)
        
        response = client.patch(
            f"/products/{test_product.id}",
            json={
                "price": 600,
                "stock": 80,
                "enabled": True
            },
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_product.id
        assert data["price"] == 600
        assert data["stock"] == 80
        assert data["enabled"] is True
    
    def test_update_product_as_event_admin(self, client, test_product, event_admin_user):
        """Test event_admin can update product."""
        headers = get_auth_header(event_admin_user)
        
        response = client.patch(
            f"/products/{test_product.id}",
            json={
                "name": "Updated Product",
                "price": 700
            },
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Product"
        assert data["price"] == 700
    
    def test_update_product_as_booth_cashier_forbidden(self, client, test_product, booth_cashier_user):
        """Test booth_cashier cannot update product."""
        headers = get_auth_header(booth_cashier_user)
        
        response = client.patch(
            f"/products/{test_product.id}",
            json={
                "price": 600
            },
            headers=headers
        )
        
        assert response.status_code == 403
    
    def test_update_product_as_issuer_forbidden(self, client, test_product, issuer_user):
        """Test issuer cannot update product."""
        headers = get_auth_header(issuer_user)
        
        response = client.patch(
            f"/products/{test_product.id}",
            json={
                "price": 600
            },
            headers=headers
        )
        
        assert response.status_code == 403
    
    def test_update_product_not_found(self, client, super_admin_user):
        """Test updating non-existent product returns 404."""
        headers = get_auth_header(super_admin_user)
        
        response = client.patch(
            "/products/99999",
            json={
                "price": 600
            },
            headers=headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "PRODUCT_NOT_FOUND"
    
    def test_update_product_negative_price(self, client, test_product, super_admin_user):
        """Test updating product with negative price fails."""
        headers = get_auth_header(super_admin_user)
        
        response = client.patch(
            f"/products/{test_product.id}",
            json={
                "price": -100
            },
            headers=headers
        )
        
        assert response.status_code == 422  # Pydantic validation error
    
    def test_update_product_partial_update(self, client, test_product, super_admin_user):
        """Test partial update of product."""
        headers = get_auth_header(super_admin_user)
        
        # Only update price, leave other fields unchanged
        response = client.patch(
            f"/products/{test_product.id}",
            json={
                "price": 550
            },
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == 550
        assert data["name"] == test_product.name  # Unchanged
        assert data["stock"] == test_product.stock  # Unchanged
    
    def test_update_product_without_auth(self, client, test_product):
        """Test updating product without authentication fails."""
        response = client.patch(
            f"/products/{test_product.id}",
            json={
                "price": 600
            }
        )
        
        assert response.status_code == 403


class TestProductRoutesIntegration:
    """Integration tests for complete product management flow."""
    
    def test_complete_product_management_flow(
        self, client, test_booth, super_admin_user, booth_cashier_user
    ):
        """Test complete flow: create product -> list products -> update product."""
        admin_headers = get_auth_header(super_admin_user)
        cashier_headers = get_auth_header(booth_cashier_user)
        
        # Step 1: Create product
        create_response = client.post(
            "/products",
            json={
                "booth_id": test_booth.id,
                "name": "Integration Test Product",
                "price": 500,
                "cost_price": 300,
                "stock": 100
            },
            headers=admin_headers
        )
        assert create_response.status_code == 201
        product_id = create_response.json()["id"]
        
        # Step 2: List products as admin
        list_response = client.get("/products", headers=admin_headers)
        assert list_response.status_code == 200
        products = list_response.json()
        product_ids = [p["id"] for p in products]
        assert product_id in product_ids
        
        # Step 3: List products as booth cashier (should see own booth products)
        cashier_list_response = client.get("/products", headers=cashier_headers)
        assert cashier_list_response.status_code == 200
        cashier_products = cashier_list_response.json()
        cashier_product_ids = [p["id"] for p in cashier_products]
        assert product_id in cashier_product_ids
        
        # Step 4: Update product
        update_response = client.patch(
            f"/products/{product_id}",
            json={
                "price": 600,
                "stock": 80
            },
            headers=admin_headers
        )
        assert update_response.status_code == 200
        updated_product = update_response.json()
        assert updated_product["price"] == 600
        assert updated_product["stock"] == 80
