"""
Signature generation and verification utilities for NFC Campus E-Wallet System.

Implements SHA256 signature generation and verification with constant-time comparison
to prevent timing attacks. Validates timestamps within a 60-second window using UTC.
"""

import hashlib
import hmac
from datetime import datetime, timezone
from typing import Optional, Tuple

from core.timezone import CST


class SignatureError(Exception):
    """Base exception for signature-related errors."""
    pass


class TimestampExpiredError(SignatureError):
    """Raised when request timestamp is too old."""
    pass


class TimestampInvalidError(SignatureError):
    """Raised when request timestamp is in the future."""
    pass


class SignatureVerificationError(SignatureError):
    """Raised when signature verification fails."""
    pass


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
    current_time = datetime.now(CST).timestamp()
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
