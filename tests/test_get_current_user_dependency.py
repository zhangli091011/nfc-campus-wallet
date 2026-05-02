"""
Unit tests for get_current_user FastAPI dependency.

Tests JWT authentication dependency including token extraction,
verification, and user retrieval.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from core.database import Base
from models.user import User
from core.security import hash_password, create_access_token, get_current_user
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


@pytest.fixture
def valid_token(test_user, test_settings):
    """Create a valid JWT token for test user."""
    token = create_access_token(
        user=test_user,
        jwt_secret_key=test_settings.jwt_secret_key,
        jwt_algorithm=test_settings.jwt_algorithm,
        jwt_expiration_minutes=test_settings.jwt_expiration_minutes
    )
    return token


class TestGetCurrentUserDependency:
    """Test get_current_user FastAPI dependency."""
    
    def test_get_current_user_success(self, test_db, test_user, valid_token, test_settings):
        """Test successful authentication with valid token."""
        # Create HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=valid_token
        )
        
        # Call get_current_user dependency
        user = get_current_user(credentials=credentials, db=test_db)
        
        # Verify returned user
        assert user.id == test_user.id
        assert user.username == "testuser"
        assert user.role == "booth_cashier"
        assert user.booth_id == 1
        assert user.status == "active"
    
    def test_get_current_user_invalid_token(self, test_db, test_settings):
        """Test authentication with invalid token."""
        # Create credentials with invalid token
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.token.string"
        )
        
        # Should raise 401 Unauthorized
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=credentials, db=test_db)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail
    
    def test_get_current_user_malformed_token(self, test_db, test_settings):
        """Test authentication with malformed token."""
        # Create credentials with malformed token
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="not-a-jwt-token"
        )
        
        # Should raise 401 Unauthorized
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=credentials, db=test_db)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail
    
    def test_get_current_user_expired_token(self, test_db, test_user, test_settings):
        """Test authentication with expired token."""
        # Create an expired token (expiration time = -1 minutes)
        import jwt
        from datetime import timedelta
        
        now = datetime.now(timezone.utc)
        expiration = now - timedelta(minutes=1)  # Already expired
        
        payload = {
            "user_id": test_user.id,
            "username": test_user.username,
            "role": test_user.role,
            "booth_id": test_user.booth_id,
            "exp": expiration,
            "iat": now - timedelta(minutes=2)
        }
        
        expired_token = jwt.encode(
            payload,
            test_settings.jwt_secret_key,
            algorithm=test_settings.jwt_algorithm
        )
        
        # Create credentials with expired token
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=expired_token
        )
        
        # Should raise 401 Unauthorized
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=credentials, db=test_db)
        
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()
    
    def test_get_current_user_token_missing_user_id(self, test_db, test_settings):
        """Test authentication with token missing user_id."""
        import jwt
        from datetime import timedelta
        
        now = datetime.now(timezone.utc)
        expiration = now + timedelta(minutes=30)
        
        # Create token without user_id
        payload = {
            "username": "testuser",
            "role": "booth_cashier",
            "exp": expiration,
            "iat": now
        }
        
        token = jwt.encode(
            payload,
            test_settings.jwt_secret_key,
            algorithm=test_settings.jwt_algorithm
        )
        
        # Create credentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        # Should raise 401 Unauthorized
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=credentials, db=test_db)
        
        assert exc_info.value.status_code == 401
        assert "missing user_id" in exc_info.value.detail
    
    def test_get_current_user_user_not_found(self, test_db, test_settings):
        """Test authentication when user does not exist in database."""
        # Create token for non-existent user
        import jwt
        from datetime import timedelta
        
        now = datetime.now(timezone.utc)
        expiration = now + timedelta(minutes=30)
        
        payload = {
            "user_id": 99999,  # Non-existent user ID
            "username": "nonexistent",
            "role": "booth_cashier",
            "booth_id": 1,
            "exp": expiration,
            "iat": now
        }
        
        token = jwt.encode(
            payload,
            test_settings.jwt_secret_key,
            algorithm=test_settings.jwt_algorithm
        )
        
        # Create credentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        # Should raise 401 Unauthorized
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=credentials, db=test_db)
        
        assert exc_info.value.status_code == 401
        assert "User not found" in exc_info.value.detail
    
    def test_get_current_user_blocked_user(self, test_db, blocked_user, test_settings):
        """Test authentication with blocked user."""
        # Create token for blocked user
        token = create_access_token(
            user=blocked_user,
            jwt_secret_key=test_settings.jwt_secret_key,
            jwt_algorithm=test_settings.jwt_algorithm,
            jwt_expiration_minutes=test_settings.jwt_expiration_minutes
        )
        
        # Create credentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        # Should raise 403 Forbidden
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=credentials, db=test_db)
        
        assert exc_info.value.status_code == 403
        assert "blocked" in exc_info.value.detail.lower()
    
    def test_get_current_user_inactive_user(self, test_db, inactive_user, test_settings):
        """Test authentication with inactive user."""
        # Create token for inactive user
        token = create_access_token(
            user=inactive_user,
            jwt_secret_key=test_settings.jwt_secret_key,
            jwt_algorithm=test_settings.jwt_algorithm,
            jwt_expiration_minutes=test_settings.jwt_expiration_minutes
        )
        
        # Create credentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        # Should raise 403 Forbidden
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=credentials, db=test_db)
        
        assert exc_info.value.status_code == 403
        assert "inactive" in exc_info.value.detail.lower()


class TestGetCurrentUserIntegration:
    """Integration tests for get_current_user dependency."""
    
    def test_complete_authentication_flow(self, test_db, test_user, test_settings):
        """Test complete authentication flow with get_current_user dependency."""
        # Step 1: Create JWT token
        token = create_access_token(
            user=test_user,
            jwt_secret_key=test_settings.jwt_secret_key,
            jwt_algorithm=test_settings.jwt_algorithm,
            jwt_expiration_minutes=test_settings.jwt_expiration_minutes
        )
        
        # Step 2: Create credentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        # Step 3: Call get_current_user dependency
        user = get_current_user(credentials=credentials, db=test_db)
        
        # Verify complete flow
        assert user.id == test_user.id
        assert user.username == "testuser"
        assert user.role == "booth_cashier"
        assert user.booth_id == 1
        assert user.is_active()
    
    def test_different_user_roles(self, test_db, test_settings):
        """Test authentication with different user roles."""
        roles = [
            ("super_admin", None),
            ("event_admin", None),
            ("booth_cashier", 1),
            ("issuer", None),
            ("reviewer", None)
        ]
        
        for role, booth_id in roles:
            # Create user with specific role
            user = User(
                username=f"{role}_user",
                password_hash=hash_password("password123"),
                role=role,
                booth_id=booth_id,
                status="active",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            test_db.add(user)
            test_db.commit()
            test_db.refresh(user)
            
            # Create token
            token = create_access_token(
                user=user,
                jwt_secret_key=test_settings.jwt_secret_key,
                jwt_algorithm=test_settings.jwt_algorithm,
                jwt_expiration_minutes=test_settings.jwt_expiration_minutes
            )
            
            # Create credentials
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=token
            )
            
            # Call get_current_user
            authenticated_user = get_current_user(credentials=credentials, db=test_db)
            
            # Verify user
            assert authenticated_user.id == user.id
            assert authenticated_user.role == role
            assert authenticated_user.booth_id == booth_id
