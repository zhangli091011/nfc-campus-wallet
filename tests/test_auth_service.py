"""
Unit tests for AuthService.

Tests authentication functionality including login, token verification,
and user retrieval.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timezone

from core.database import Base
from models.user import User
from services.auth_service import (
    AuthService,
    InvalidCredentialsError,
    UserBlockedError,
    UserInactiveError,
    TokenExpiredError,
    TokenInvalidError
)
from core.security import hash_password
from core.config import Settings


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
def auth_service(test_db, test_settings):
    """Create AuthService instance with test database."""
    return AuthService(test_db)


@pytest.fixture
def test_user(test_db):
    """Create a test user in the database."""
    user = User(
        username="testuser",
        password_hash=hash_password("password123"),
        role="booth_cashier",
        booth_id=1,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def blocked_user(test_db):
    """Create a blocked test user."""
    user = User(
        username="blockeduser",
        password_hash=hash_password("password123"),
        role="booth_cashier",
        booth_id=1,
        status="blocked",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def inactive_user(test_db):
    """Create an inactive test user."""
    user = User(
        username="inactiveuser",
        password_hash=hash_password("password123"),
        role="issuer",
        booth_id=None,
        status="inactive",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


class TestAuthServiceLogin:
    """Test AuthService.login method."""
    
    def test_login_success(self, auth_service, test_user):
        """Test successful login with valid credentials."""
        result = auth_service.login("testuser", "password123")
        
        # Verify response structure
        assert "access_token" in result
        assert "token_type" in result
        assert "user" in result
        
        # Verify token type
        assert result["token_type"] == "bearer"
        
        # Verify user information
        user_info = result["user"]
        assert user_info["id"] == test_user.id
        assert user_info["username"] == "testuser"
        assert user_info["role"] == "booth_cashier"
        assert user_info["booth_id"] == 1
        assert user_info["status"] == "active"
        
        # Verify token is a non-empty string
        assert isinstance(result["access_token"], str)
        assert len(result["access_token"]) > 0
    
    def test_login_invalid_username(self, auth_service):
        """Test login with non-existent username."""
        with pytest.raises(InvalidCredentialsError) as exc_info:
            auth_service.login("nonexistent", "password123")
        
        assert exc_info.value.error_code == "INVALID_CREDENTIALS"
    
    def test_login_invalid_password(self, auth_service, test_user):
        """Test login with incorrect password."""
        with pytest.raises(InvalidCredentialsError) as exc_info:
            auth_service.login("testuser", "wrongpassword")
        
        assert exc_info.value.error_code == "INVALID_CREDENTIALS"
    
    def test_login_blocked_user(self, auth_service, blocked_user):
        """Test login with blocked user account."""
        with pytest.raises(UserBlockedError) as exc_info:
            auth_service.login("blockeduser", "password123")
        
        assert exc_info.value.error_code == "USER_BLOCKED"
        assert exc_info.value.username == "blockeduser"
    
    def test_login_inactive_user(self, auth_service, inactive_user):
        """Test login with inactive user account."""
        with pytest.raises(UserInactiveError) as exc_info:
            auth_service.login("inactiveuser", "password123")
        
        assert exc_info.value.error_code == "USER_INACTIVE"
        assert exc_info.value.username == "inactiveuser"


class TestAuthServiceGetCurrentUser:
    """Test AuthService.get_current_user method."""
    
    def test_get_current_user_success(self, auth_service, test_user):
        """Test retrieving existing active user."""
        user = auth_service.get_current_user(test_user.id)
        
        assert user.id == test_user.id
        assert user.username == "testuser"
        assert user.role == "booth_cashier"
        assert user.booth_id == 1
        assert user.status == "active"
    
    def test_get_current_user_not_found(self, auth_service):
        """Test retrieving non-existent user."""
        with pytest.raises(InvalidCredentialsError) as exc_info:
            auth_service.get_current_user(99999)
        
        assert exc_info.value.error_code == "INVALID_CREDENTIALS"
    
    def test_get_current_user_blocked(self, auth_service, blocked_user):
        """Test retrieving blocked user."""
        with pytest.raises(UserBlockedError) as exc_info:
            auth_service.get_current_user(blocked_user.id)
        
        assert exc_info.value.error_code == "USER_BLOCKED"
    
    def test_get_current_user_inactive(self, auth_service, inactive_user):
        """Test retrieving inactive user."""
        with pytest.raises(UserInactiveError) as exc_info:
            auth_service.get_current_user(inactive_user.id)
        
        assert exc_info.value.error_code == "USER_INACTIVE"


class TestAuthServiceVerifyToken:
    """Test AuthService.verify_token method."""
    
    def test_verify_token_success(self, auth_service, test_user):
        """Test verifying valid JWT token."""
        # First login to get a token
        login_result = auth_service.login("testuser", "password123")
        token = login_result["access_token"]
        
        # Verify the token
        payload = auth_service.verify_token(token)
        
        # Check payload contents
        assert payload["user_id"] == test_user.id
        assert payload["username"] == "testuser"
        assert payload["role"] == "booth_cashier"
        assert payload["booth_id"] == 1
        assert "exp" in payload
        assert "iat" in payload
    
    def test_verify_token_invalid(self, auth_service):
        """Test verifying invalid JWT token."""
        with pytest.raises(TokenInvalidError) as exc_info:
            auth_service.verify_token("invalid.token.string")
        
        assert exc_info.value.error_code == "TOKEN_INVALID"
    
    def test_verify_token_malformed(self, auth_service):
        """Test verifying malformed JWT token."""
        with pytest.raises(TokenInvalidError) as exc_info:
            auth_service.verify_token("not-a-jwt-token")
        
        assert exc_info.value.error_code == "TOKEN_INVALID"


class TestAuthServiceIntegration:
    """Integration tests for complete authentication flow."""
    
    def test_complete_auth_flow(self, auth_service, test_user):
        """Test complete authentication flow: login -> verify token -> get user."""
        # Step 1: Login
        login_result = auth_service.login("testuser", "password123")
        token = login_result["access_token"]
        
        # Step 2: Verify token
        payload = auth_service.verify_token(token)
        user_id = payload["user_id"]
        
        # Step 3: Get current user
        user = auth_service.get_current_user(user_id)
        
        # Verify complete flow
        assert user.id == test_user.id
        assert user.username == "testuser"
        assert user.role == "booth_cashier"
        assert user.is_active()
