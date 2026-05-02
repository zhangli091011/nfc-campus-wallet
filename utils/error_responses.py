"""
Error response formatting utilities for NFC Campus E-Wallet System.

Provides centralized error response formatting with consistent structure
and HTTP status code mapping.

Validates:
    - Requirements 15.1: HTTP status codes appropriate to error type
    - Requirements 15.2: Error code and message in all error responses
    - Requirements 15.3: Status code 400 for validation errors
    - Requirements 15.4: Status code 401 for authentication errors
    - Requirements 15.5: Status code 500 for internal server errors
"""

from typing import Dict, Any, Optional
from fastapi.responses import JSONResponse


class ErrorCode:
    """Standard error codes used across the system."""
    
    # Validation errors (HTTP 400)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    MERCHANT_NOT_FOUND = "MERCHANT_NOT_FOUND"
    
    # Authentication errors (HTTP 401)
    AUTH_ERROR = "AUTH_ERROR"
    SIGNATURE_INVALID = "SIGNATURE_INVALID"
    TIMESTAMP_EXPIRED = "TIMESTAMP_EXPIRED"
    TIMESTAMP_INVALID = "TIMESTAMP_INVALID"
    
    # Internal errors (HTTP 500)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"


def create_error_response(
    error_code: str,
    message: str,
    status_code: int,
    **additional_fields
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        error_code: Machine-readable error code
        message: Human-readable error message
        status_code: HTTP status code
        **additional_fields: Optional additional fields to include in response
        
    Returns:
        JSONResponse with standardized error structure
        
    Example:
        >>> create_error_response(
        ...     ErrorCode.VALIDATION_ERROR,
        ...     "Amount must be positive",
        ...     400,
        ...     field="amount",
        ...     value=-10.0
        ... )
    """
    content = {
        "error_code": error_code,
        "message": message
    }
    
    # Add any additional fields
    content.update(additional_fields)
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )


def validation_error(
    message: str,
    field: Optional[str] = None,
    value: Optional[Any] = None
) -> JSONResponse:
    """
    Create a validation error response (HTTP 400).
    
    Args:
        message: Description of the validation error
        field: Optional field name that failed validation
        value: Optional value that failed validation
        
    Returns:
        JSONResponse with HTTP 400 status
        
    Validates: Requirements 15.3
    """
    additional_fields = {}
    if field is not None:
        additional_fields["field"] = field
    if value is not None:
        additional_fields["value"] = value
    
    return create_error_response(
        ErrorCode.VALIDATION_ERROR,
        message,
        400,
        **additional_fields
    )


def insufficient_funds_error(
    message: str,
    current_balance: Optional[float] = None,
    requested_amount: Optional[float] = None
) -> JSONResponse:
    """
    Create an insufficient funds error response (HTTP 400).
    
    Args:
        message: Description of the error
        current_balance: Optional current account balance
        requested_amount: Optional requested transaction amount
        
    Returns:
        JSONResponse with HTTP 400 status
    """
    additional_fields = {}
    if current_balance is not None:
        additional_fields["current_balance"] = current_balance
    if requested_amount is not None:
        additional_fields["requested_amount"] = requested_amount
    
    return create_error_response(
        ErrorCode.INSUFFICIENT_FUNDS,
        message,
        400,
        **additional_fields
    )


def user_not_found_error(uid: str) -> JSONResponse:
    """
    Create a user not found error response (HTTP 400).
    
    Args:
        uid: The UID that was not found
        
    Returns:
        JSONResponse with HTTP 400 status
    """
    return create_error_response(
        ErrorCode.USER_NOT_FOUND,
        f"User with UID '{uid}' does not exist",
        400
    )


def authentication_error(
    message: str = "Request authentication failed",
    error_code: str = ErrorCode.AUTH_ERROR
) -> JSONResponse:
    """
    Create an authentication error response (HTTP 401).
    
    Args:
        message: Description of the authentication error
        error_code: Specific authentication error code
        
    Returns:
        JSONResponse with HTTP 401 status
        
    Validates: Requirements 15.4
    """
    return create_error_response(
        error_code,
        message,
        401
    )


def internal_error(
    message: str = "An internal error occurred. Please try again later.",
    request_id: Optional[str] = None
) -> JSONResponse:
    """
    Create an internal server error response (HTTP 500).
    
    Args:
        message: Generic error message (should not expose internal details)
        request_id: Optional request ID for tracking
        
    Returns:
        JSONResponse with HTTP 500 status
        
    Validates: Requirements 15.5
    """
    additional_fields = {}
    if request_id is not None:
        additional_fields["request_id"] = request_id
    
    return create_error_response(
        ErrorCode.INTERNAL_ERROR,
        message,
        500,
        **additional_fields
    )


def map_exception_to_response(exception: Exception) -> JSONResponse:
    """
    Map common exception types to appropriate error responses.
    
    This function provides a centralized way to convert exceptions
    into standardized error responses with correct HTTP status codes.
    
    Args:
        exception: The exception to map
        
    Returns:
        JSONResponse with appropriate status code and error structure
        
    Example:
        >>> try:
        ...     validate_amount(-10.0)
        ... except ValueError as e:
        ...     return map_exception_to_response(e)
    """
    exception_name = type(exception).__name__
    error_message = str(exception)
    
    # Map known exception types to error responses
    if exception_name == "ValueError":
        # Validation errors
        return validation_error(error_message)
    
    elif exception_name in ["UserNotFoundError", "InsufficientFundsError"]:
        # Business logic errors
        if "not found" in error_message.lower() or "does not exist" in error_message.lower():
            return create_error_response(
                ErrorCode.USER_NOT_FOUND,
                error_message,
                400
            )
        elif "insufficient" in error_message.lower():
            return create_error_response(
                ErrorCode.INSUFFICIENT_FUNDS,
                error_message,
                400
            )
        else:
            return validation_error(error_message)
    
    elif exception_name in ["SignatureError", "SignatureVerificationError", 
                           "TimestampExpiredError", "TimestampInvalidError"]:
        # Authentication errors
        if "timestamp" in error_message.lower() and "expired" in error_message.lower():
            return authentication_error("Request timestamp expired", ErrorCode.TIMESTAMP_EXPIRED)
        elif "timestamp" in error_message.lower():
            return authentication_error("Request timestamp is invalid", ErrorCode.TIMESTAMP_INVALID)
        elif "signature" in error_message.lower():
            return authentication_error("Request signature verification failed", ErrorCode.SIGNATURE_INVALID)
        else:
            return authentication_error()
    
    else:
        # Unknown exceptions map to internal error
        return internal_error()
