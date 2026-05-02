"""
Authentication and authorization middleware for NFC Campus E-Wallet System.

Provides JWT token verification and role-based access control.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Callable
import jwt
import logging

from core.config import get_settings
from core.database import get_db
from models.user import User

logger = logging.getLogger(__name__)

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
    
    Returns:
        User: Current authenticated user
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    settings = get_settings()
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


def require_role(allowed_roles: List[str]) -> Callable:
    """
    Create a dependency that requires specific roles.
    
    Args:
        allowed_roles: List of allowed role names
    
    Returns:
        Callable: Dependency function that checks user role
    
    Example:
        @router.get("/admin")
        async def admin_endpoint(
            current_user = Depends(require_role(["super_admin", "event_admin"]))
        ):
            pass
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        """
        Check if current user has required role.
        
        Args:
            current_user: Current authenticated user
        
        Returns:
            User: Current user if authorized
        
        Raises:
            HTTPException: If user doesn't have required role
        """
        if current_user.role not in allowed_roles:
            logger.warning(
                f"User {current_user.username} (role={current_user.role}) "
                f"attempted to access endpoint requiring roles: {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}"
            )
        
        return current_user
    
    return role_checker


def require_booth_access(booth_id: int) -> Callable:
    """
    Create a dependency that requires access to a specific booth.
    
    Args:
        booth_id: Booth ID to check access for
    
    Returns:
        Callable: Dependency function that checks booth access
    
    Example:
        @router.get("/booths/{booth_id}")
        async def get_booth(
            booth_id: int,
            current_user = Depends(require_booth_access(booth_id))
        ):
            pass
    """
    def booth_access_checker(current_user: User = Depends(get_current_user)) -> User:
        """
        Check if current user can access the booth.
        
        Args:
            current_user: Current authenticated user
        
        Returns:
            User: Current user if authorized
        
        Raises:
            HTTPException: If user doesn't have access to the booth
        """
        if not current_user.can_access_booth(booth_id):
            logger.warning(
                f"User {current_user.username} (role={current_user.role}) "
                f"attempted to access booth {booth_id} without permission"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this booth"
            )
        
        return current_user
    
    return booth_access_checker
