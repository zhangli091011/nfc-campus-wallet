"""
Input validation utilities for NFC Campus E-Wallet System.

Provides centralized validation functions that can be reused across endpoints.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from app.config import get_settings


def validate_amount(amount: float) -> None:
    """
    Validate that an amount is positive and within maximum transaction limit.
    
    Args:
        amount: The transaction amount to validate
        
    Raises:
        ValueError: If amount is not positive or exceeds maximum limit
        
    Validates:
        - Requirements 10.1: Amount must be positive
        - Requirements 10.2: Amount must not exceed maximum transaction limit
    """
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    settings = get_settings()
    if amount > settings.max_transaction_amount:
        raise ValueError(
            f"Amount exceeds maximum transaction limit of {settings.max_transaction_amount}"
        )


def validate_uid_format(uid: str) -> None:
    """
    Validate that a UID matches the expected hexadecimal format.
    
    Args:
        uid: The user identifier to validate
        
    Raises:
        ValueError: If UID is empty or contains non-hexadecimal characters
        
    Validates:
        - Requirements 10.3: UID format must match hexadecimal pattern
    """
    if not uid:
        raise ValueError("UID cannot be empty")
    
    # Check if string contains only valid hex characters
    if not all(c in "0123456789ABCDEFabcdef" for c in uid):
        raise ValueError("UID must be a hexadecimal string")


def validate_required_fields(request: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that all required parameters are present in a request.
    
    Args:
        request: Dictionary containing request parameters
        required_fields: List of field names that must be present
        
    Raises:
        ValueError: If any required field is missing
        
    Validates:
        - Requirements 10.4: All required request parameters must be present
        - Requirements 10.5: Descriptive error message identifying missing field
    """
    missing_fields = [field for field in required_fields if field not in request or request[field] is None]
    
    if missing_fields:
        if len(missing_fields) == 1:
            raise ValueError(f"Missing required field: {missing_fields[0]}")
        else:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
