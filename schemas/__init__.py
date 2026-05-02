"""
Schemas module for NFC Campus E-Wallet System.

Contains Pydantic DTO models for request/response validation.
"""

from schemas.common import ErrorResponse, SuccessResponse
from schemas.user import (
    BalanceResponse,
    UserRole,
    UserStatus,
    UserCreate,
    UserResponse,
    UserLogin,
    TokenResponse
)
from schemas.booth import (
    BoothStatus,
    BoothCreate,
    BoothUpdate,
    BoothResponse
)
from schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse
)
from schemas.transaction import (
    PaymentRequest,
    RechargeRequest,
    BalanceQueryRequest,
    TransactionResponse,
    TransactionItem,
    TransactionHistoryResponse
)

__all__ = [
    # Common
    'ErrorResponse',
    'SuccessResponse',
    # User
    'BalanceResponse',
    'UserRole',
    'UserStatus',
    'UserCreate',
    'UserResponse',
    'UserLogin',
    'TokenResponse',
    # Booth
    'BoothStatus',
    'BoothCreate',
    'BoothUpdate',
    'BoothResponse',
    # Product
    'ProductCreate',
    'ProductUpdate',
    'ProductResponse',
    # Transaction
    'PaymentRequest',
    'RechargeRequest',
    'BalanceQueryRequest',
    'TransactionResponse',
    'TransactionItem',
    'TransactionHistoryResponse',
]
