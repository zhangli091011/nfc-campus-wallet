"""
Authentication service for Booth Management System.

Handles user authentication, JWT token generation and verification.
Implements Requirements 4.1, 4.2, 4.6.
"""

from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
import jwt

from models.user import User
from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)
from core.config import get_settings
from core.exceptions import BusinessException

logger = logging.getLogger(__name__)


class AuthenticationError(BusinessException):
    """Authentication related errors."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Invalid username or password."""
    
    def __init__(self):
        super().__init__(
            message="Invalid username or password",
            error_code="INVALID_CREDENTIALS"
        )


class UserBlockedError(AuthenticationError):
    """User account is blocked."""
    
    def __init__(self, username: str):
        super().__init__(
            message=f"User account '{username}' is blocked",
            error_code="USER_BLOCKED"
        )
        self.username = username


class UserInactiveError(AuthenticationError):
    """User account is inactive."""
    
    def __init__(self, username: str):
        super().__init__(
            message=f"User account '{username}' is inactive",
            error_code="USER_INACTIVE"
        )
        self.username = username


class TokenExpiredError(AuthenticationError):
    """JWT token has expired."""
    
    def __init__(self):
        super().__init__(
            message="JWT token has expired",
            error_code="TOKEN_EXPIRED"
        )


class TokenInvalidError(AuthenticationError):
    """JWT token is invalid."""
    
    def __init__(self, detail: str = "Invalid JWT token"):
        super().__init__(
            message=detail,
            error_code="TOKEN_INVALID"
        )


class AuthService:
    """
    Authentication service for booth management system.
    
    Provides user authentication and JWT token management.
    
    Validates Requirements:
        - Requirement 4.1: User login with username and password
        - Requirement 4.2: Return JWT token and user information on successful login
        - Requirement 4.6: Handle authentication errors (invalid credentials, user blocked)
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize authentication service.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self.settings = get_settings()
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and generate JWT token.
        
        Validates Requirements:
            - Requirement 4.1: Verify username and password
            - Requirement 4.2: Return JWT token and user information
            - Requirement 4.6: Handle invalid credentials and blocked users
        
        Args:
            username: User's username
            password: User's plain text password
            
        Returns:
            Dictionary containing:
                - access_token: JWT token string
                - token_type: "bearer"
                - user: User information dict with id, username, role, booth_id
                
        Raises:
            InvalidCredentialsError: If username or password is incorrect
            UserBlockedError: If user account is blocked
            UserInactiveError: If user account is inactive
            
        Example:
            >>> auth_service = AuthService(db_session)
            >>> result = auth_service.login("admin", "password123")
            >>> result["access_token"]
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
            >>> result["user"]["role"]
            'super_admin'
        """
        # Query user by username
        user = self.db.query(User).filter(User.username == username).first()
        
        # Check if user exists
        if user is None:
            logger.warning(f"Login failed: User '{username}' not found")
            raise InvalidCredentialsError()
        
        # Verify password
        if not verify_password(password, user.password_hash):
            logger.warning(f"Login failed: Invalid password for user '{username}'")
            raise InvalidCredentialsError()
        
        # Check user status
        if user.status == 'blocked':
            logger.warning(f"Login failed: User '{username}' is blocked")
            raise UserBlockedError(username)
        
        if user.status == 'inactive':
            logger.warning(f"Login failed: User '{username}' is inactive")
            raise UserInactiveError(username)
        
        # Generate JWT token
        access_token = create_access_token(
            user=user,
            jwt_secret_key=self.settings.jwt_secret_key,
            jwt_algorithm=self.settings.jwt_algorithm,
            jwt_expiration_minutes=self.settings.jwt_expiration_minutes
        )
        
        logger.info(f"Login successful: user_id={user.id}, username={username}, role={user.role}")
        
        # Return token and user information
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "booth_id": user.booth_id,
                "staff_name": user.staff_name,
                "status": user.status,
                "created_at": user.created_at
            }
        }
    
    def get_current_user(self, user_id: int) -> User:
        """
        Get user information from database by user ID.
        
        This method is typically called after JWT token verification to fetch
        the complete user object from the database.
        
        Validates Requirements:
            - Requirement 4.6: Handle user not found error
        
        Args:
            user_id: User's database ID (extracted from JWT token)
            
        Returns:
            User object from database
            
        Raises:
            InvalidCredentialsError: If user does not exist
            UserBlockedError: If user account is blocked
            UserInactiveError: If user account is inactive
            
        Example:
            >>> auth_service = AuthService(db_session)
            >>> user = auth_service.get_current_user(1)
            >>> user.username
            'admin'
            >>> user.role
            'super_admin'
        """
        # Query user by ID
        user = self.db.query(User).filter(User.id == user_id).first()
        
        # Check if user exists
        if user is None:
            logger.warning(f"User not found: user_id={user_id}")
            raise InvalidCredentialsError()
        
        # Check user status
        if user.status == 'blocked':
            logger.warning(f"User is blocked: user_id={user_id}, username={user.username}")
            raise UserBlockedError(user.username)
        
        if user.status == 'inactive':
            logger.warning(f"User is inactive: user_id={user_id}, username={user.username}")
            raise UserInactiveError(user.username)
        
        logger.debug(f"User retrieved: user_id={user_id}, username={user.username}, role={user.role}")
        
        return user
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token and extract payload.
        
        This method decodes and validates the JWT token, checking both
        the signature and expiration time.
        
        Args:
            token: JWT token string
            
        Returns:
            Dictionary containing token payload with keys:
                - user_id: User's database ID
                - username: User's username
                - role: User's role
                - booth_id: User's assigned booth ID (may be null)
                - exp: Token expiration timestamp
                - iat: Token issued at timestamp
                
        Raises:
            TokenExpiredError: If token has expired
            TokenInvalidError: If token is invalid or signature verification fails
            
        Example:
            >>> auth_service = AuthService(db_session)
            >>> payload = auth_service.verify_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
            >>> payload["user_id"]
            1
            >>> payload["role"]
            'super_admin'
        """
        try:
            # Decode and verify token
            payload = decode_access_token(
                token=token,
                jwt_secret_key=self.settings.jwt_secret_key,
                jwt_algorithm=self.settings.jwt_algorithm
            )
            
            logger.debug(f"Token verified: user_id={payload.get('user_id')}, role={payload.get('role')}")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token verification failed: Token has expired")
            raise TokenExpiredError()
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token verification failed: {str(e)}")
            raise TokenInvalidError(str(e))
