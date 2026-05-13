"""
Security utilities for NFC Campus E-Wallet System.

Implements:
1. SHA256 signature generation and verification with constant-time comparison
2. Password hashing and verification using bcrypt with cost factor 12
3. Timestamp validation within a 60-second window using UTC
4. JWT token generation and verification for authentication
5. FastAPI authentication dependency for JWT token validation
"""

import hashlib
import hmac
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from core.exceptions import (
    SignatureError,
    TimestampExpiredError,
    TimestampInvalidError,
    SignatureVerificationError
)


def generate_signature(
    uid: str,
    timestamp: int,
    secret_key: str,
    amount: Optional[float] = None
) -> str:
    """
    Generate SHA256 signature for API request authentication.
    
    For balance queries: SHA256(uid + timestamp + secret_key)
    For transactions: SHA256(uid + amount + timestamp + secret_key)
    
    Args:
        uid: User identifier (hexadecimal string)
        timestamp: Unix timestamp in seconds
        secret_key: Shared secret key
        amount: Transaction amount (optional, for payment/recharge requests)
        
    Returns:
        Hexadecimal signature string
    """
    if amount is not None:
        # Transaction signature: uid + amount + timestamp + secret_key
        message = f"{uid}{amount}{timestamp}{secret_key}"
    else:
        # Balance query signature: uid + timestamp + secret_key
        message = f"{uid}{timestamp}{secret_key}"
    
    # Compute SHA256 hash
    hash_obj = hashlib.sha256(message.encode('utf-8'))
    return hash_obj.hexdigest()


def verify_signature(
    uid: str,
    timestamp: int,
    signature: str,
    secret_key: str,
    amount: Optional[float] = None
) -> bool:
    """
    Verify request signature using constant-time comparison.
    
    Args:
        uid: User identifier from request
        timestamp: Unix timestamp from request
        signature: Signature from request
        secret_key: Shared secret key
        amount: Transaction amount (optional, for payment/recharge requests)
        
    Returns:
        True if signature is valid
        
    Raises:
        SignatureVerificationError: If signature verification fails
    """
    # Compute expected signature
    expected_signature = generate_signature(uid, timestamp, secret_key, amount)
    
    # Use constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(signature, expected_signature):
        raise SignatureVerificationError("Signature verification failed")
    
    return True


def validate_timestamp(timestamp: int, time_window: int = 60) -> Tuple[bool, Optional[str]]:
    """
    Validate that timestamp is within acceptable window of server time.
    
    Args:
        timestamp: Unix timestamp in seconds from request
        time_window: Maximum allowed time difference in seconds (default: 60)
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Raises:
        TimestampExpiredError: If timestamp is too old
        TimestampInvalidError: If timestamp is in the future
    """
    # Get current server time in UTC
    current_time = datetime.now(timezone.utc).timestamp()
    time_diff = current_time - timestamp
    
    # Check if timestamp is too old (expired)
    # Use > not >= to allow exactly time_window seconds
    if time_diff > time_window:
        raise TimestampExpiredError(
            f"Request timestamp expired. Time difference: {time_diff:.0f} seconds"
        )
    
    # Check if timestamp is in the future (invalid)
    # Use < not <= to allow exactly time_window seconds in future
    if time_diff < -time_window:
        raise TimestampInvalidError(
            f"Request timestamp is in the future. Time difference: {abs(time_diff):.0f} seconds"
        )
    
    return True, None


def verify_request(
    uid: str,
    timestamp: int,
    signature: str,
    secret_key: str,
    time_window: int = 60,
    amount: Optional[float] = None
) -> bool:
    """
    Complete request verification: timestamp validation + signature verification.
    
    Args:
        uid: User identifier from request
        timestamp: Unix timestamp from request
        signature: Signature from request
        secret_key: Shared secret key
        time_window: Maximum allowed time difference in seconds (default: 60)
        amount: Transaction amount (optional, for payment/recharge requests)
        
    Returns:
        True if request is valid
        
    Raises:
        TimestampExpiredError: If timestamp is too old
        TimestampInvalidError: If timestamp is in the future
        SignatureVerificationError: If signature verification fails
    """
    # Validate timestamp first (fail fast)
    validate_timestamp(timestamp, time_window)
    
    # Verify signature
    verify_signature(uid, timestamp, signature, secret_key, amount)
    
    return True


# ============================================================================
# Password Hashing Functions (for JWT Authentication System)
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with cost factor 12.
    
    Uses bcrypt's built-in salt generation for security.
    Cost factor of 12 provides strong security while maintaining
    reasonable performance (approximately 0.3 seconds per hash).
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Bcrypt hash string (includes salt and cost factor)
        
    Example:
        >>> hashed = hash_password("my_secure_password")
        >>> hashed.startswith("$2b$12$")
        True
    """
    # Encode password to bytes
    password_bytes = password.encode('utf-8')
    
    # Generate salt with cost factor 12 (2^12 = 4096 rounds)
    # bcrypt.gensalt() automatically includes the cost factor in the salt
    salt = bcrypt.gensalt(rounds=12)
    
    # Hash password with salt
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string (bcrypt returns bytes)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a bcrypt hash using constant-time comparison.
    
    bcrypt.checkpw() internally uses constant-time comparison to prevent
    timing attacks. This is critical for security as it prevents attackers
    from using timing information to guess passwords.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hash to verify against
        
    Returns:
        True if password matches hash, False otherwise
        
    Example:
        >>> hashed = hash_password("my_password")
        >>> verify_password("my_password", hashed)
        True
        >>> verify_password("wrong_password", hashed)
        False
    """
    # Encode both password and hash to bytes
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    
    # Verify password using bcrypt's constant-time comparison
    # This prevents timing attacks by always taking the same amount of time
    # regardless of where the password differs from the hash
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# ============================================================================
# JWT Token Functions (for JWT Authentication System)
# ============================================================================

def create_access_token(
    user: Any,
    jwt_secret_key: str,
    jwt_algorithm: str,
    jwt_expiration_minutes: int
) -> str:
    """
    Create a JWT access token for authenticated user.
    
    Generates a JWT token containing user identification and role information.
    The token is signed with the configured secret key and includes an
    expiration time.
    
    Token payload includes:
    - user_id: User's database ID
    - username: User's username
    - role: User's role (super_admin, event_admin, booth_cashier, issuer, reviewer)
    - booth_id: User's assigned booth ID (for booth_cashier role, null otherwise)
    - exp: Token expiration timestamp (UTC)
    - iat: Token issued at timestamp (UTC)
    
    Args:
        user: User object with id, username, role, and booth_id attributes
        jwt_secret_key: Secret key for signing the token
        jwt_algorithm: JWT signing algorithm (e.g., "HS256")
        jwt_expiration_minutes: Token expiration time in minutes
        
    Returns:
        JWT token string
        
    Example:
        >>> from models.user import User
        >>> user = User(id=1, username="admin", role="super_admin", booth_id=None)
        >>> token = create_access_token(user, "secret", "HS256", 1440)
        >>> # Returns a JWT token string like "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    
    Validates Requirements:
        - Requirement 4.3: Include user_id, username, and role in JWT token payload
        - Requirement 4.4: Sign JWT tokens with secret key from configuration
        - Requirement 4.5: Set JWT token expiration time based on configuration
    """
    # Calculate expiration time
    now = datetime.now(timezone.utc)
    expiration = now + timedelta(minutes=jwt_expiration_minutes)
    
    # Build token payload
    payload: Dict[str, Any] = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "booth_id": user.booth_id,
        "exp": expiration,
        "iat": now
    }
    
    # Encode and sign the token
    token = jwt.encode(payload, jwt_secret_key, algorithm=jwt_algorithm)
    
    return token


def decode_access_token(
    token: str,
    jwt_secret_key: str,
    jwt_algorithm: str
) -> Dict[str, Any]:
    """
    Decode and verify a JWT access token.
    
    Verifies the token signature and expiration, then returns the payload.
    Raises exceptions for invalid or expired tokens.
    
    Args:
        token: JWT token string to decode
        jwt_secret_key: Secret key for verifying the token signature
        jwt_algorithm: JWT signing algorithm (e.g., "HS256")
        
    Returns:
        Dictionary containing token payload with keys:
        - user_id: User's database ID
        - username: User's username
        - role: User's role
        - booth_id: User's assigned booth ID (may be null)
        - exp: Token expiration timestamp
        - iat: Token issued at timestamp
        
    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid or signature verification fails
        
    Example:
        >>> token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        >>> payload = decode_access_token(token, "secret", "HS256")
        >>> payload["user_id"]
        1
        >>> payload["role"]
        'super_admin'
    
    Validates Requirements:
        - Requirement 4.4: Verify JWT token signature with secret key
        - Requirement 4.5: Validate JWT token expiration
    """
    try:
        # Decode and verify the token
        # jwt.decode automatically verifies signature and expiration
        payload = jwt.decode(token, jwt_secret_key, algorithms=[jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        # Token has expired
        raise jwt.ExpiredSignatureError("JWT token has expired")
    except jwt.InvalidTokenError as e:
        # Token is invalid (bad signature, malformed, etc.)
        raise jwt.InvalidTokenError(f"Invalid JWT token: {str(e)}")


# ============================================================================
# FastAPI Authentication Dependency (for JWT Authentication System)
# ============================================================================

# HTTPBearer security scheme for extracting Bearer token from Authorization header
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Any:
    """
    FastAPI dependency for JWT authentication.
    
    Extracts JWT token from Authorization header, verifies it, and returns
    the current authenticated user from the database.
    
    This dependency should be used in route handlers that require authentication:
    
    Example:
        @app.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id, "username": current_user.username}
    
    Authentication Flow:
        1. Extract Bearer token from Authorization header
        2. Decode and verify JWT token (signature and expiration)
        3. Extract user_id from token payload
        4. Query user from database
        5. Validate user status (active, not blocked)
        6. Return User object
    
    Args:
        credentials: HTTPAuthorizationCredentials from Authorization header
        
    Returns:
        User object from database
        
    Raises:
        HTTPException(401): If token is missing, invalid, or expired
        HTTPException(401): If user does not exist
        HTTPException(403): If user is blocked or inactive
        
    Validates Requirements:
        - Requirement 4.7: Extract Bearer token from Authorization header
        - Requirement 12.1: Provide JWT authentication dependency
        - Requirement 12.2: Raise 401 for invalid/expired tokens
        - Requirement 12.7: Extract user information from JWT token
    """
    # Import here to avoid circular dependency
    from core.config import get_settings
    from core.database import get_db
    from models.user import User
    
    # Get database session
    db = next(get_db())
    
    # Extract token from credentials
    token = credentials.credentials
    
    # Get settings for JWT configuration
    settings = get_settings()
    
    try:
        # Decode and verify JWT token
        payload = decode_access_token(
            token=token,
            jwt_secret_key=settings.jwt_secret_key,
            jwt_algorithm=settings.jwt_algorithm
        )
        
        # Extract user_id from payload
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
    except jwt.ExpiredSignatureError:
        # Token has expired
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError as e:
        # Token is invalid (bad signature, malformed, etc.)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Query user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    # Check if user exists
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check user status - blocked users cannot access the system
    if user.status == 'blocked':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User account is blocked"
        )
    
    # Check user status - inactive users cannot access the system
    if user.status == 'inactive':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User account is inactive"
        )
    
    # Return authenticated user
    return user


class RoleChecker:
    """
    Role-based authorization dependency for FastAPI routes.
    
    This class implements a callable dependency that verifies the current user
    has one of the allowed roles. It should be used in combination with the
    get_current_user dependency to enforce role-based access control (RBAC).
    
    Special behavior for 'school_inspector' role:
        - Automatically allowed on all read-only requests (GET/HEAD/OPTIONS)
        - Denied on all write requests (POST/PUT/PATCH/DELETE) unless
          'school_inspector' is explicitly listed in allowed_roles
    
    Example Usage:
        # Allow only super_admin and event_admin
        @app.get("/booths")
        def list_booths(
            current_user: User = Depends(get_current_user),
            _: None = Depends(RoleChecker(["super_admin", "event_admin"]))
        ):
            return {"booths": [...]}
        
        # Allow only super_admin
        @app.post("/users")
        def create_user(
            user_data: UserCreate,
            current_user: User = Depends(get_current_user),
            _: None = Depends(RoleChecker(["super_admin"]))
        ):
            return {"user": {...}}
    
    Validates Requirements:
        - Requirement 12.3: Provide role-based authorization dependency
        - Requirement 12.4: Raise 403 when user lacks required role
    """
    
    # 只读 HTTP 方法：允许 school_inspector (校方巡查) 访问
    _READ_ONLY_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
    
    def __init__(self, allowed_roles: list[str]):
        """
        Initialize the RoleChecker with a list of allowed roles.
        
        Args:
            allowed_roles: List of role strings that are allowed to access the route.
                          Valid roles: 'super_admin', 'event_admin', 'booth_cashier',
                          'issuer', 'reviewer', 'bank_clerk', 'school_inspector'
        
        Example:
            >>> checker = RoleChecker(["super_admin", "event_admin"])
            >>> checker.allowed_roles
            ['super_admin', 'event_admin']
        """
        self.allowed_roles = allowed_roles
    
    def __call__(
        self,
        request: Request,
        current_user: Any = Depends(get_current_user)
    ) -> None:
        """
        Verify that the current user's role is in the allowed roles list.
        
        This method is called by FastAPI's dependency injection system.
        It automatically receives the current user via the get_current_user dependency
        and checks if their role is allowed.
        
        Special handling for 'school_inspector' (校方巡查):
            - For read-only HTTP methods (GET/HEAD/OPTIONS), access is granted
              automatically, so this role can view all data without needing to
              be listed in each endpoint's allowed_roles.
            - For write HTTP methods (POST/PUT/PATCH/DELETE), access is denied
              unless 'school_inspector' is explicitly included in allowed_roles.
        
        Args:
            request: FastAPI Request object (auto-injected)
            current_user: User object from get_current_user dependency (auto-injected)
            
        Returns:
            None (dependency succeeds silently if role is allowed)
            
        Raises:
            HTTPException(403): If user's role is not in allowed_roles list
            
        Validates Requirements:
            - Requirement 12.3: Check user roles against allowed list
            - Requirement 12.4: Raise 403 Forbidden for unauthorized roles
        """
        # 校方巡查：只读方法（GET/HEAD/OPTIONS）自动放行
        if (
            current_user.role == "school_inspector"
            and request.method.upper() in self._READ_ONLY_METHODS
        ):
            return None
        
        # Check if user's role is in the allowed roles list
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(self.allowed_roles)}. Your role: {current_user.role}"
            )
        
        # Role is allowed, dependency succeeds
        return None


# ============================================================================
# Booth Ownership Validation Dependency (for Booth Management System)
# ============================================================================

def validate_booth_ownership(
    booth_id: int,
    current_user: Any = Depends(get_current_user)
) -> None:
    """
    FastAPI dependency for booth ownership validation.
    
    Validates that booth_cashier users can only access their assigned booth,
    while event_admin and super_admin can access all booths.
    
    This dependency should be used in route handlers that require booth-specific
    access control:
    
    Example:
        @app.get("/booths/{booth_id}/products")
        def get_booth_products(
            booth_id: int,
            current_user: User = Depends(get_current_user),
            _: None = Depends(validate_booth_ownership)
        ):
            return {"products": [...]}
    
    Authorization Rules:
        - super_admin: Can access all booths
        - event_admin: Can access all booths
        - booth_cashier: Can only access their assigned booth (user.booth_id == booth_id)
        - issuer: Cannot access booth-specific data (403 Forbidden)
        - reviewer: Cannot access booth-specific data (403 Forbidden)
    
    Args:
        booth_id: The booth ID to validate access for (from path parameter)
        current_user: User object from get_current_user dependency (auto-injected)
        
    Returns:
        None (dependency succeeds silently if access is allowed)
        
    Raises:
        HTTPException(403): If user does not have permission to access the booth
        HTTPException(404): If booth does not exist
        
    Validates Requirements:
        - Requirement 5.1: booth_cashier can only access products from their assigned booth
        - Requirement 5.2: booth_cashier can only create payment transactions for their booth
        - Requirement 5.3: booth_cashier attempting to access another booth gets 403 error
        - Requirement 12.5: Provide booth ownership validation dependency
        - Requirement 12.6: Raise 403 when booth_cashier accesses booth they don't own
    """
    # Import here to avoid circular dependency
    from core.database import get_db
    from models.booth import Booth
    
    # Get database session
    db = next(get_db())
    
    # Admins (super_admin and event_admin) can access all booths
    if current_user.role in ('super_admin', 'event_admin'):
        # Verify booth exists
        booth = db.query(Booth).filter(Booth.id == booth_id).first()
        if booth is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booth with id {booth_id} not found"
            )
        return None
    
    # Booth cashiers can only access their assigned booth
    if current_user.role == 'booth_cashier':
        # Verify booth exists
        booth = db.query(Booth).filter(Booth.id == booth_id).first()
        if booth is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booth with id {booth_id} not found"
            )
        
        # Check if booth_cashier owns this booth
        if current_user.booth_id != booth_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. You can only access booth {current_user.booth_id}. Requested booth: {booth_id}"
            )
        
        return None
    
    # Other roles (issuer, reviewer) cannot access booth-specific data
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Access denied. Role '{current_user.role}' cannot access booth-specific data"
    )


# ============================================================================
# Permission Validation Utility Functions (for Service Layer)
# ============================================================================

def can_manage_booths(user: Any) -> bool:
    """
    Check if user has permission to manage booths (create, update, delete).
    
    Permission Rules:
        - super_admin: Can manage all booths
        - event_admin: Can manage all booths
        - booth_cashier: Cannot manage booths
        - issuer: Cannot manage booths
        - reviewer: Cannot manage booths
    
    This utility function is intended for use in service layers to check
    permissions before performing booth management operations.
    
    Args:
        user: User object with role attribute
        
    Returns:
        True if user can manage booths, False otherwise
        
    Example:
        >>> from models.user import User
        >>> admin = User(role="super_admin")
        >>> can_manage_booths(admin)
        True
        >>> cashier = User(role="booth_cashier")
        >>> can_manage_booths(cashier)
        False
    
    Validates Requirements:
        - Requirement 5.4: Provide permission validation utilities
        - Requirement 7.1: event_admin can create booths
        - Requirement 7.2: event_admin can update products
    """
    return user.role in ('super_admin', 'event_admin')


def can_manage_products(user: Any) -> bool:
    """
    Check if user has permission to manage products (create, update, delete).
    
    Permission Rules:
        - super_admin: Can manage all products
        - event_admin: Can manage all products
        - booth_cashier: Cannot manage products (read-only access to own booth products)
        - issuer: Cannot manage products
        - reviewer: Cannot manage products
    
    This utility function is intended for use in service layers to check
    permissions before performing product management operations.
    
    Args:
        user: User object with role attribute
        
    Returns:
        True if user can manage products, False otherwise
        
    Example:
        >>> from models.user import User
        >>> admin = User(role="event_admin")
        >>> can_manage_products(admin)
        True
        >>> cashier = User(role="booth_cashier")
        >>> can_manage_products(cashier)
        False
    
    Validates Requirements:
        - Requirement 5.4: Provide permission validation utilities
        - Requirement 7.2: event_admin can create and update products
        - Requirement 7.3: event_admin can view activity-wide statistics
    """
    return user.role in ('super_admin', 'event_admin')


def can_process_payment(user: Any, booth_id: Optional[int] = None) -> bool:
    """
    Check if user has permission to process payment transactions.
    
    Permission Rules:
        - super_admin: Can process payments for any booth
        - event_admin: Can process payments for any booth
        - booth_cashier: Can only process payments for their assigned booth
        - issuer: Cannot process payments (can only process recharges)
        - reviewer: Cannot process payments
    
    This utility function is intended for use in service layers to check
    permissions before processing payment transactions.
    
    Args:
        user: User object with role and booth_id attributes
        booth_id: Optional booth ID to check ownership for booth_cashier role
        
    Returns:
        True if user can process payment, False otherwise
        
    Example:
        >>> from models.user import User
        >>> admin = User(role="super_admin", booth_id=None)
        >>> can_process_payment(admin)
        True
        >>> cashier = User(role="booth_cashier", booth_id=1)
        >>> can_process_payment(cashier, booth_id=1)
        True
        >>> can_process_payment(cashier, booth_id=2)
        False
        >>> issuer = User(role="issuer", booth_id=None)
        >>> can_process_payment(issuer)
        False
    
    Validates Requirements:
        - Requirement 5.4: Provide permission validation utilities
        - Requirement 6.1: issuer can perform recharge but not payment
        - Requirement 6.2: issuer attempting payment gets 403 error
    """
    # Admins can process payments for any booth
    if user.role in ('super_admin', 'event_admin'):
        return True
    
    # Booth cashiers can only process payments for their assigned booth
    if user.role == 'booth_cashier':
        # If no booth_id provided, allow (will be validated later in the flow)
        if booth_id is None:
            return True
        # Check if booth_cashier owns this booth
        return user.booth_id == booth_id
    
    # Other roles (issuer, reviewer) cannot process payments
    return False


def can_process_recharge(user: Any) -> bool:
    """
    Check if user has permission to process recharge transactions.
    
    Permission Rules:
        - super_admin: Can process recharges
        - event_admin: Can process recharges
        - booth_cashier: Cannot process recharges (can only process payments)
        - issuer: Can process recharges
        - reviewer: Cannot process recharges
    
    This utility function is intended for use in service layers to check
    permissions before processing recharge transactions.
    
    Args:
        user: User object with role attribute
        
    Returns:
        True if user can process recharge, False otherwise
        
    Example:
        >>> from models.user import User
        >>> admin = User(role="super_admin")
        >>> can_process_recharge(admin)
        True
        >>> issuer = User(role="issuer")
        >>> can_process_recharge(issuer)
        True
        >>> cashier = User(role="booth_cashier")
        >>> can_process_recharge(cashier)
        False
    
    Validates Requirements:
        - Requirement 5.4: Provide permission validation utilities
        - Requirement 6.1: issuer can perform recharge operations
        - Requirement 6.3: Record issuer's user_id as operator_id in recharge transactions
        - Requirement 7.4: event_admin can view activity-wide statistics
    """
    return user.role in ('super_admin', 'event_admin', 'issuer')
