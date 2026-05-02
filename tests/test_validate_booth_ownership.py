"""
Unit tests for validate_booth_ownership FastAPI dependency.

Tests booth ownership validation including access control for different roles.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from fastapi import HTTPException

from core.database import Base
from models.user import User
from models.event import Event
from models.booth import Booth
from core.security import hash_password, validate_booth_ownership


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
def test_settings(monkeypatch):
    """Mock settings for testing."""
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-signature-verification-at-least-32-chars")
    monkeypatch.setenv("DATABASE_USER", "test_user")
    monkeypatch.setenv("DATABASE_PASSWORD", "test_password")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key-must-be-at-least-32-characters-long")
    
    from core.config import load_settings
    settings = load_settings()
    return settings


@pytest.fixture
def test_event(test_db):
    """Create a test event."""
    event = Event(
        name="Test Event",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        status="active",
        recharge_enabled=True,
        consume_enabled=True,
        created_at=datetime.now(timezone.utc)
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)
    return event


@pytest.fixture
def test_booth_1(test_db, test_event):
    """Create test booth 1."""
    booth = Booth(
        event_id=test_event.id,
        name="Booth 1",
        class_name="Class 1",
        status="active",
        created_at=datetime.now(timezone.utc)
    )
    test_db.add(booth)
    test_db.commit()
    test_db.refresh(booth)
    return booth


@pytest.fixture
def test_booth_2(test_db, test_event):
    """Create test booth 2."""
    booth = Booth(
        event_id=test_event.id,
        name="Booth 2",
        class_name="Class 2",
        status="active",
        created_at=datetime.now(timezone.utc)
    )
    test_db.add(booth)
    test_db.commit()
    test_db.refresh(booth)
    return booth


@pytest.fixture
def super_admin_user(test_db):
    """Create a super_admin user."""
    user = User(
        username="superadmin",
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
    """Create an event_admin user."""
    user = User(
        username="eventadmin",
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
def booth_cashier_1(test_db, test_booth_1):
    """Create a booth_cashier for booth 1."""
    user = User(
        username="cashier1",
        password_hash=hash_password("password123"),
        role="booth_cashier",
        booth_id=test_booth_1.id,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def booth_cashier_2(test_db, test_booth_2):
    """Create a booth_cashier for booth 2."""
    user = User(
        username="cashier2",
        password_hash=hash_password("password123"),
        role="booth_cashier",
        booth_id=test_booth_2.id,
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


@pytest.fixture
def reviewer_user(test_db):
    """Create a reviewer user."""
    user = User(
        username="reviewer",
        password_hash=hash_password("password123"),
        role="reviewer",
        booth_id=None,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


class TestValidateBoothOwnershipSuperAdmin:
    """Test validate_booth_ownership with super_admin role."""
    
    def test_super_admin_can_access_any_booth(self, test_db, super_admin_user, test_booth_1, test_booth_2):
        """Test super_admin can access any booth."""
        # Should not raise exception for booth 1
        result = validate_booth_ownership(
            booth_id=test_booth_1.id,
            current_user=super_admin_user,
            db=test_db
        )
        assert result is None
        
        # Should not raise exception for booth 2
        result = validate_booth_ownership(
            booth_id=test_booth_2.id,
            current_user=super_admin_user,
            db=test_db
        )
        assert result is None
    
    def test_super_admin_gets_404_for_nonexistent_booth(self, test_db, super_admin_user):
        """Test super_admin gets 404 for non-existent booth."""
        with pytest.raises(HTTPException) as exc_info:
            validate_booth_ownership(
                booth_id=99999,
                current_user=super_admin_user,
                db=test_db
            )
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()


class TestValidateBoothOwnershipEventAdmin:
    """Test validate_booth_ownership with event_admin role."""
    
    def test_event_admin_can_access_any_booth(self, test_db, event_admin_user, test_booth_1, test_booth_2):
        """Test event_admin can access any booth."""
        # Should not raise exception for booth 1
        result = validate_booth_ownership(
            booth_id=test_booth_1.id,
            current_user=event_admin_user,
            db=test_db
        )
        assert result is None
        
        # Should not raise exception for booth 2
        result = validate_booth_ownership(
            booth_id=test_booth_2.id,
            current_user=event_admin_user,
            db=test_db
        )
        assert result is None
    
    def test_event_admin_gets_404_for_nonexistent_booth(self, test_db, event_admin_user):
        """Test event_admin gets 404 for non-existent booth."""
        with pytest.raises(HTTPException) as exc_info:
            validate_booth_ownership(
                booth_id=99999,
                current_user=event_admin_user,
                db=test_db
            )
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()


class TestValidateBoothOwnershipBoothCashier:
    """Test validate_booth_ownership with booth_cashier role."""
    
    def test_booth_cashier_can_access_own_booth(self, test_db, booth_cashier_1, test_booth_1):
        """Test booth_cashier can access their own booth."""
        result = validate_booth_ownership(
            booth_id=test_booth_1.id,
            current_user=booth_cashier_1,
            db=test_db
        )
        assert result is None
    
    def test_booth_cashier_cannot_access_other_booth(self, test_db, booth_cashier_1, test_booth_2):
        """Test booth_cashier cannot access another booth."""
        with pytest.raises(HTTPException) as exc_info:
            validate_booth_ownership(
                booth_id=test_booth_2.id,
                current_user=booth_cashier_1,
                db=test_db
            )
        
        assert exc_info.value.status_code == 403
        assert "access denied" in exc_info.value.detail.lower()
        assert str(booth_cashier_1.booth_id) in exc_info.value.detail
        assert str(test_booth_2.id) in exc_info.value.detail
    
    def test_booth_cashier_gets_404_for_nonexistent_booth(self, test_db, booth_cashier_1):
        """Test booth_cashier gets 404 for non-existent booth."""
        with pytest.raises(HTTPException) as exc_info:
            validate_booth_ownership(
                booth_id=99999,
                current_user=booth_cashier_1,
                db=test_db
            )
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()


class TestValidateBoothOwnershipIssuer:
    """Test validate_booth_ownership with issuer role."""
    
    def test_issuer_cannot_access_booth_data(self, test_db, issuer_user, test_booth_1):
        """Test issuer cannot access booth-specific data."""
        with pytest.raises(HTTPException) as exc_info:
            validate_booth_ownership(
                booth_id=test_booth_1.id,
                current_user=issuer_user,
                db=test_db
            )
        
        assert exc_info.value.status_code == 403
        assert "access denied" in exc_info.value.detail.lower()
        assert "issuer" in exc_info.value.detail.lower()


class TestValidateBoothOwnershipReviewer:
    """Test validate_booth_ownership with reviewer role."""
    
    def test_reviewer_cannot_access_booth_data(self, test_db, reviewer_user, test_booth_1):
        """Test reviewer cannot access booth-specific data."""
        with pytest.raises(HTTPException) as exc_info:
            validate_booth_ownership(
                booth_id=test_booth_1.id,
                current_user=reviewer_user,
                db=test_db
            )
        
        assert exc_info.value.status_code == 403
        assert "access denied" in exc_info.value.detail.lower()
        assert "reviewer" in exc_info.value.detail.lower()


class TestValidateBoothOwnershipIntegration:
    """Integration tests for validate_booth_ownership."""
    
    def test_multiple_cashiers_different_booths(self, test_db, booth_cashier_1, booth_cashier_2, test_booth_1, test_booth_2):
        """Test multiple cashiers can access their respective booths."""
        # Cashier 1 can access booth 1
        result = validate_booth_ownership(
            booth_id=test_booth_1.id,
            current_user=booth_cashier_1,
            db=test_db
        )
        assert result is None
        
        # Cashier 2 can access booth 2
        result = validate_booth_ownership(
            booth_id=test_booth_2.id,
            current_user=booth_cashier_2,
            db=test_db
        )
        assert result is None
        
        # Cashier 1 cannot access booth 2
        with pytest.raises(HTTPException) as exc_info:
            validate_booth_ownership(
                booth_id=test_booth_2.id,
                current_user=booth_cashier_1,
                db=test_db
            )
        assert exc_info.value.status_code == 403
        
        # Cashier 2 cannot access booth 1
        with pytest.raises(HTTPException) as exc_info:
            validate_booth_ownership(
                booth_id=test_booth_1.id,
                current_user=booth_cashier_2,
                db=test_db
            )
        assert exc_info.value.status_code == 403
    
    def test_admin_hierarchy(self, test_db, super_admin_user, event_admin_user, booth_cashier_1, test_booth_1):
        """Test admin hierarchy: super_admin and event_admin have more access than booth_cashier."""
        # All can access booth 1
        for user in [super_admin_user, event_admin_user, booth_cashier_1]:
            result = validate_booth_ownership(
                booth_id=test_booth_1.id,
                current_user=user,
                db=test_db
            )
            assert result is None
