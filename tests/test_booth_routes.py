"""
Integration tests for booth routes.

Tests booth management API endpoints including authentication,
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


class TestCreateBooth:
    """Test POST /booths endpoint."""
    
    def test_create_booth_as_super_admin(self, client, test_event, super_admin_user):
        """Test super_admin can create booth."""
        headers = get_auth_header(super_admin_user)
        
        response = client.post(
            "/booths",
            json={
                "event_id": test_event.id,
                "name": "Food Stall",
                "class_name": "Class 2B"
            },
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Food Stall"
        assert data["class_name"] == "Class 2B"
        assert data["event_id"] == test_event.id
        assert data["status"] == "active"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_booth_as_event_admin(self, client, test_event, event_admin_user):
        """Test event_admin can create booth."""
        headers = get_auth_header(event_admin_user)
        
        response = client.post(
            "/booths",
            json={
                "event_id": test_event.id,
                "name": "Drink Stand",
                "class_name": "Class 3C"
            },
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Drink Stand"
        assert data["class_name"] == "Class 3C"
    
    def test_create_booth_as_booth_cashier_forbidden(self, client, test_event, booth_cashier_user):
        """Test booth_cashier cannot create booth."""
        headers = get_auth_header(booth_cashier_user)
        
        response = client.post(
            "/booths",
            json={
                "event_id": test_event.id,
                "name": "Unauthorized Booth",
                "class_name": "Class 4D"
            },
            headers=headers
        )
        
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "booth_cashier" in data["detail"]
    
    def test_create_booth_as_issuer_forbidden(self, client, test_event, issuer_user):
        """Test issuer cannot create booth."""
        headers = get_auth_header(issuer_user)
        
        response = client.post(
            "/booths",
            json={
                "event_id": test_event.id,
                "name": "Unauthorized Booth",
                "class_name": "Class 5E"
            },
            headers=headers
        )
        
        assert response.status_code == 403
    
    def test_create_booth_without_auth(self, client, test_event):
        """Test creating booth without authentication fails."""
        response = client.post(
            "/booths",
            json={
                "event_id": test_event.id,
                "name": "Unauthorized Booth",
                "class_name": "Class 6F"
            }
        )
        
        assert response.status_code == 403  # No Authorization header
    
    def test_create_booth_invalid_event_id(self, client, super_admin_user):
        """Test creating booth with non-existent event_id."""
        headers = get_auth_header(super_admin_user)
        
        response = client.post(
            "/booths",
            json={
                "event_id": 99999,
                "name": "Invalid Booth",
                "class_name": "Class 7G"
            },
            headers=headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INVALID_EVENT_ID"


class TestListBooths:
    """Test GET /booths endpoint."""
    
    def test_list_booths_as_super_admin(self, client, test_booth, super_admin_user):
        """Test super_admin can list booths."""
        headers = get_auth_header(super_admin_user)
        
        response = client.get("/booths", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Verify booth data structure
        booth = data[0]
        assert "id" in booth
        assert "name" in booth
        assert "class_name" in booth
        assert "event_id" in booth
        assert "status" in booth
        assert "created_at" in booth
    
    def test_list_booths_as_event_admin(self, client, test_booth, event_admin_user):
        """Test event_admin can list booths."""
        headers = get_auth_header(event_admin_user)
        
        response = client.get("/booths", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_list_booths_filter_by_event_id(self, client, test_event, test_booth, super_admin_user):
        """Test listing booths filtered by event_id."""
        headers = get_auth_header(super_admin_user)
        
        response = client.get(f"/booths?event_id={test_event.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # All booths should belong to the specified event
        for booth in data:
            assert booth["event_id"] == test_event.id
    
    def test_list_booths_filter_by_status(self, client, test_booth, super_admin_user):
        """Test listing booths filtered by status."""
        headers = get_auth_header(super_admin_user)
        
        response = client.get("/booths?status=active", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # All booths should have active status
        for booth in data:
            assert booth["status"] == "active"
    
    def test_list_booths_as_booth_cashier_forbidden(self, client, booth_cashier_user):
        """Test booth_cashier cannot list all booths."""
        headers = get_auth_header(booth_cashier_user)
        
        response = client.get("/booths", headers=headers)
        
        assert response.status_code == 403
    
    def test_list_booths_without_auth(self, client):
        """Test listing booths without authentication fails."""
        response = client.get("/booths")
        
        assert response.status_code == 403


class TestGetBooth:
    """Test GET /booths/{booth_id} endpoint."""
    
    def test_get_booth_as_super_admin(self, client, test_booth, super_admin_user):
        """Test super_admin can get booth details."""
        headers = get_auth_header(super_admin_user)
        
        response = client.get(f"/booths/{test_booth.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_booth.id
        assert data["name"] == "Test Booth"
        assert data["class_name"] == "Class 1A"
        assert data["status"] == "active"
    
    def test_get_booth_as_event_admin(self, client, test_booth, event_admin_user):
        """Test event_admin can get booth details."""
        headers = get_auth_header(event_admin_user)
        
        response = client.get(f"/booths/{test_booth.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_booth.id
    
    def test_get_booth_as_booth_cashier_own_booth(self, client, test_booth, booth_cashier_user):
        """Test booth_cashier can get their own booth details."""
        headers = get_auth_header(booth_cashier_user)
        
        response = client.get(f"/booths/{test_booth.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_booth.id
    
    def test_get_booth_as_booth_cashier_other_booth_forbidden(
        self, client, test_db, test_event, booth_cashier_user
    ):
        """Test booth_cashier cannot get other booth details."""
        # Create another booth
        other_booth = Booth(
            event_id=test_event.id,
            name="Other Booth",
            class_name="Class 8H",
            status="active",
            created_at=datetime.now(timezone.utc)
        )
        test_db.add(other_booth)
        test_db.commit()
        test_db.refresh(other_booth)
        
        headers = get_auth_header(booth_cashier_user)
        
        response = client.get(f"/booths/{other_booth.id}", headers=headers)
        
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "Access denied" in data["detail"]
    
    def test_get_booth_as_issuer_forbidden(self, client, test_booth, issuer_user):
        """Test issuer cannot get booth details."""
        headers = get_auth_header(issuer_user)
        
        response = client.get(f"/booths/{test_booth.id}", headers=headers)
        
        assert response.status_code == 403
    
    def test_get_booth_not_found(self, client, super_admin_user):
        """Test getting non-existent booth returns 404."""
        headers = get_auth_header(super_admin_user)
        
        response = client.get("/booths/99999", headers=headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "BOOTH_NOT_FOUND"
    
    def test_get_booth_without_auth(self, client, test_booth):
        """Test getting booth without authentication fails."""
        response = client.get(f"/booths/{test_booth.id}")
        
        assert response.status_code == 403


class TestBoothRoutesIntegration:
    """Integration tests for complete booth management flow."""
    
    def test_complete_booth_management_flow(
        self, client, test_event, super_admin_user, booth_cashier_user
    ):
        """Test complete flow: create booth -> list booths -> get booth details."""
        admin_headers = get_auth_header(super_admin_user)
        
        # Step 1: Create booth
        create_response = client.post(
            "/booths",
            json={
                "event_id": test_event.id,
                "name": "Integration Test Booth",
                "class_name": "Class 9I"
            },
            headers=admin_headers
        )
        assert create_response.status_code == 201
        booth_id = create_response.json()["id"]
        
        # Step 2: List booths
        list_response = client.get("/booths", headers=admin_headers)
        assert list_response.status_code == 200
        booths = list_response.json()
        booth_ids = [b["id"] for b in booths]
        assert booth_id in booth_ids
        
        # Step 3: Get booth details
        get_response = client.get(f"/booths/{booth_id}", headers=admin_headers)
        assert get_response.status_code == 200
        booth_data = get_response.json()
        assert booth_data["name"] == "Integration Test Booth"
        assert booth_data["class_name"] == "Class 9I"
