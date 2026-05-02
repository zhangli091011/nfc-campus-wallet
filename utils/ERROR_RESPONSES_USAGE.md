# Error Response Utilities - Usage Guide

This document explains how to use the centralized error response formatting utilities in the NFC Campus E-Wallet System.

## Overview

The `utils/error_responses.py` module provides standardized error response formatting that ensures:
- Consistent error structure across all endpoints
- Correct HTTP status code mapping (400, 401, 500)
- Machine-readable error codes for client handling
- Human-readable error messages

## Quick Start

### Import the utilities

```python
from utils.error_responses import (
    validation_error,
    user_not_found_error,
    insufficient_funds_error,
    authentication_error,
    internal_error
)
```

### Basic Usage in Endpoints

```python
@router.post("/pay")
async def process_payment(request: PaymentRequest, db: Session = Depends(get_db)):
    try:
        # Validation
        if request.amount <= 0:
            return validation_error(
                "Amount must be positive",
                field="amount",
                value=request.amount
            )
        
        # Business logic
        result = transaction_service.process_payment(...)
        return {"success": True, "new_balance": result.new_balance}
        
    except UserNotFoundError:
        return user_not_found_error(request.uid)
    
    except InsufficientFundsError as e:
        return insufficient_funds_error(str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return internal_error()
```

## Available Functions

### 1. validation_error()

**Use for:** Input validation failures (HTTP 400)

```python
# Basic validation error
return validation_error("Amount must be positive")

# With field information
return validation_error(
    "Amount must be positive",
    field="amount",
    value=-10.0
)
```

**Response format:**
```json
{
    "error_code": "VALIDATION_ERROR",
    "message": "Amount must be positive",
    "field": "amount",
    "value": -10.0
}
```

### 2. insufficient_funds_error()

**Use for:** Payment failures due to insufficient balance (HTTP 400)

```python
return insufficient_funds_error(
    "Account balance is insufficient for payment amount",
    current_balance=25.00,
    requested_amount=50.00
)
```

**Response format:**
```json
{
    "error_code": "INSUFFICIENT_FUNDS",
    "message": "Account balance is insufficient for payment amount",
    "current_balance": 25.00,
    "requested_amount": 50.00
}
```

### 3. user_not_found_error()

**Use for:** Operations on non-existent users (HTTP 400)

```python
return user_not_found_error("A1B2C3D4")
```

**Response format:**
```json
{
    "error_code": "USER_NOT_FOUND",
    "message": "User with UID 'A1B2C3D4' does not exist"
}
```

### 4. authentication_error()

**Use for:** Authentication failures (HTTP 401)

```python
# Generic authentication error
return authentication_error()

# Specific authentication error
return authentication_error(
    "Request signature verification failed",
    ErrorCode.SIGNATURE_INVALID
)
```

**Response format:**
```json
{
    "error_code": "SIGNATURE_INVALID",
    "message": "Request signature verification failed"
}
```

### 5. internal_error()

**Use for:** Unexpected server errors (HTTP 500)

```python
# Basic internal error (generic message)
return internal_error()

# With request ID for tracking
return internal_error(
    "An internal error occurred. Please try again later.",
    request_id="abc123-def456"
)
```

**Response format:**
```json
{
    "error_code": "INTERNAL_ERROR",
    "message": "An internal error occurred. Please try again later.",
    "request_id": "abc123-def456"
}
```

## Error Codes

The `ErrorCode` class defines standard error codes:

### Validation Errors (HTTP 400)
- `VALIDATION_ERROR` - General validation failure
- `INSUFFICIENT_FUNDS` - Payment amount exceeds balance
- `USER_NOT_FOUND` - User does not exist
- `MERCHANT_NOT_FOUND` - Merchant does not exist

### Authentication Errors (HTTP 401)
- `AUTH_ERROR` - General authentication failure
- `SIGNATURE_INVALID` - Signature verification failed
- `TIMESTAMP_EXPIRED` - Request timestamp too old
- `TIMESTAMP_INVALID` - Request timestamp invalid

### Internal Errors (HTTP 500)
- `INTERNAL_ERROR` - General internal server error
- `DATABASE_ERROR` - Database operation failed

## Advanced Usage

### Custom Error Responses

For custom error scenarios, use `create_error_response()`:

```python
from utils.error_responses import create_error_response

return create_error_response(
    error_code="CUSTOM_ERROR",
    message="Custom error message",
    status_code=400,
    additional_field="additional_value"
)
```

### Exception Mapping

Use `map_exception_to_response()` to automatically map exceptions:

```python
from utils.error_responses import map_exception_to_response

try:
    validate_amount(amount)
except Exception as e:
    return map_exception_to_response(e)
```

## Best Practices

1. **Use specific error functions** instead of generic ones when possible
2. **Include field information** in validation errors to help clients highlight issues
3. **Log errors** before returning error responses
4. **Never expose internal details** in error messages (especially for 500 errors)
5. **Use consistent error codes** so clients can handle errors programmatically

## Migration Guide

### Before (inline error responses)

```python
return JSONResponse(
    status_code=400,
    content={
        "error_code": "VALIDATION_ERROR",
        "message": "Amount must be positive"
    }
)
```

### After (using utilities)

```python
return validation_error("Amount must be positive")
```

## Testing

The error response utilities are fully tested. See:
- `tests/test_error_responses.py` - Unit tests
- `tests/test_error_responses_integration.py` - Integration examples

## Requirements Validation

These utilities validate the following requirements:
- **15.1**: HTTP status codes appropriate to error type
- **15.2**: Error code and message in all error responses
- **15.3**: Status code 400 for validation errors
- **15.4**: Status code 401 for authentication errors
- **15.5**: Status code 500 for internal server errors
