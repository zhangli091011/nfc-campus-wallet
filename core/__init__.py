"""
Core module for NFC Campus E-Wallet System.

Contains configuration, database, security, and exception definitions.
"""

from core.config import Settings, load_settings, get_settings
from core.database import Base, init_database, get_db, create_tables
from core.security import (
    generate_signature,
    verify_signature,
    validate_timestamp,
    verify_request
)
from core.exceptions import (
    BusinessException,
    UserNotFoundError,
    InsufficientFundsError,
    MerchantNotFoundError,
    MerchantInactiveError,
    SignatureError,
    TimestampExpiredError,
    TimestampInvalidError,
    SignatureVerificationError
)

__all__ = [
    # Config
    'Settings',
    'load_settings',
    'get_settings',
    # Database
    'Base',
    'init_database',
    'get_db',
    'create_tables',
    # Security
    'generate_signature',
    'verify_signature',
    'validate_timestamp',
    'verify_request',
    # Exceptions
    'BusinessException',
    'UserNotFoundError',
    'InsufficientFundsError',
    'MerchantNotFoundError',
    'MerchantInactiveError',
    'SignatureError',
    'TimestampExpiredError',
    'TimestampInvalidError',
    'SignatureVerificationError',
]
