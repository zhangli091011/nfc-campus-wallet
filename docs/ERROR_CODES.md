# Error Codes Reference - NFC Campus E-Wallet System

This document provides a comprehensive reference for all error codes returned by the API.

## Error Response Format

All error responses follow this consistent format:

```json
{
    "error_code": "ERROR_CODE",
    "message": "Human-readable error message"
}
```

For validation errors, additional fields may be included:

```json
{
    "error_code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "field": "field_name",
    "value": "invalid_value"
}
```

---

## HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | OK - Request succeeded |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Validation error or invalid request |
| 401 | Unauthorized - Authentication required or failed |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource does not exist |
| 500 | Internal Server Error - Unexpected server error |

---

## Authentication Errors (401)

### AUTH_ERROR
**Description**: General authentication error

**Common Causes**:
- Missing authentication credentials
- Malformed authentication header
- Authentication system error

**Example**:
```json
{
    "error_code": "AUTH_ERROR",
    "message": "Authentication failed"
}
```

**Resolution**:
- Ensure Authorization header is present
- Check header format: `Authorization: Bearer <token>`
- Verify authentication system is operational

---

### INVALID_CREDENTIALS
**Description**: Invalid username or password

**Common Causes**:
- Incorrect username
- Incorrect password
- User account does not exist

**Example**:
```json
{
    "error_code": "INVALID_CREDENTIALS",
    "message": "Invalid username or password"
}
```

**Resolution**:
- Verify username is correct
- Verify password is correct
- Check if user account exists

---

### TOKEN_EXPIRED
**Description**: JWT token has expired

**Common Causes**:
- Token age exceeds JWT_EXPIRATION_MINUTES
- System time mismatch between client and server

**Example**:
```json
{
    "error_code": "TOKEN_EXPIRED",
    "message": "JWT token has expired"
}
```

**Resolution**:
- Login again to obtain a new token
- Check JWT_EXPIRATION_MINUTES configuration
- Verify system time is synchronized

---

### TOKEN_INVALID
**Description**: JWT token is invalid

**Common Causes**:
- Token signature verification failed
- Token format is malformed
- Token was tampered with
- JWT_SECRET_KEY mismatch

**Example**:
```json
{
    "error_code": "TOKEN_INVALID",
    "message": "Invalid JWT token: Signature verification failed"
}
```

**Resolution**:
- Login again to obtain a valid token
- Verify JWT_SECRET_KEY matches between token creation and validation
- Check token was not modified in transit

---

### TOKEN_MISSING
**Description**: JWT token is missing from request

**Common Causes**:
- Authorization header not included
- Bearer token not provided

**Example**:
```json
{
    "error_code": "TOKEN_MISSING",
    "message": "JWT token is required"
}
```

**Resolution**:
- Include Authorization header: `Authorization: Bearer <token>`
- Ensure token is not empty

---

### AUTHENTICATION_REQUIRED
**Description**: JWT authentication is required for this operation

**Common Causes**:
- Attempting booth operation without JWT token
- Using signature verification for booth management endpoints

**Example**:
```json
{
    "error_code": "AUTHENTICATION_REQUIRED",
    "message": "Booth payments require JWT authentication. Please provide a valid Bearer token in the Authorization header."
}
```

**Resolution**:
- Login to obtain JWT token
- Include token in Authorization header
- Use correct authentication method for the endpoint

---

## Authorization Errors (403)

### PERMISSION_DENIED
**Description**: User lacks required permissions

**Common Causes**:
- User role does not have access to the resource
- Operation requires higher privilege level

**Example**:
```json
{
    "error_code": "PERMISSION_DENIED",
    "message": "Access denied. Required roles: super_admin, event_admin. Your role: booth_cashier"
}
```

**Resolution**:
- Check user role matches required roles
- Request access from administrator
- Use account with appropriate permissions

---

### BOOTH_ACCESS_DENIED
**Description**: User cannot access the specified booth

**Common Causes**:
- Booth cashier attempting to access another booth
- User not assigned to the booth

**Example**:
```json
{
    "error_code": "BOOTH_ACCESS_DENIED",
    "message": "Access denied. You can only access booth 1. Requested booth: 2"
}
```

**Resolution**:
- Verify booth_id matches user's assigned booth
- Request access from event admin
- Use correct booth_id for your account

---

### ROLE_NOT_ALLOWED
**Description**: User role is not allowed for this operation

**Common Causes**:
- Issuer attempting payment operation
- Booth cashier attempting recharge operation
- Reviewer attempting management operation

**Example**:
```json
{
    "error_code": "ROLE_NOT_ALLOWED",
    "message": "Access denied. Issuers can only process recharge transactions, not payments"
}
```

**Resolution**:
- Use account with appropriate role
- Check operation requirements
- Request role change from administrator

---

## Validation Errors (400)

### VALIDATION_ERROR
**Description**: General validation error

**Common Causes**:
- Invalid field value
- Missing required field
- Field format incorrect

**Example**:
```json
{
    "error_code": "VALIDATION_ERROR",
    "message": "Invalid request: must specify either event_id or booth_id to filter transactions"
}
```

**Resolution**:
- Check request body matches schema
- Verify all required fields are present
- Validate field formats and values

---

### INVALID_BOOTH_ID
**Description**: Booth ID is invalid or does not exist

**Common Causes**:
- Booth does not exist in database
- Booth ID is negative or zero
- Booth was deleted

**Example**:
```json
{
    "error_code": "INVALID_BOOTH_ID",
    "message": "Booth with id 999 not found"
}
```

**Resolution**:
- Verify booth exists
- Check booth_id is correct
- Query booth list to find valid IDs

---

### INVALID_PRODUCT_ID
**Description**: Product ID is invalid or does not exist

**Common Causes**:
- Product does not exist in database
- Product ID is negative or zero
- Product was deleted

**Example**:
```json
{
    "error_code": "INVALID_PRODUCT_ID",
    "message": "Product with id 999 not found"
}
```

**Resolution**:
- Verify product exists
- Check product_id is correct
- Query product list to find valid IDs

---

### INVALID_EVENT_ID
**Description**: Event ID is invalid or does not exist

**Common Causes**:
- Event does not exist in database
- Event ID is negative or zero
- Event was deleted

**Example**:
```json
{
    "error_code": "INVALID_EVENT_ID",
    "message": "Event with id 999 not found"
}
```

**Resolution**:
- Verify event exists
- Check event_id is correct
- Query event list to find valid IDs

---

### PRODUCT_NOT_IN_BOOTH
**Description**: Product does not belong to the specified booth

**Common Causes**:
- Product belongs to different booth
- Product and booth IDs mismatched
- Attempting cross-booth product sale

**Example**:
```json
{
    "error_code": "PRODUCT_NOT_IN_BOOTH",
    "message": "Product 5 does not belong to booth 1"
}
```

**Resolution**:
- Verify product belongs to booth
- Check product_id and booth_id match
- Query products for the booth

---

### BOOTH_NOT_IN_EVENT
**Description**: Booth does not belong to the specified event

**Common Causes**:
- Booth belongs to different event
- Booth and event IDs mismatched
- Attempting cross-event booth operation

**Example**:
```json
{
    "error_code": "BOOTH_NOT_IN_EVENT",
    "message": "Booth 1 does not belong to event 2"
}
```

**Resolution**:
- Verify booth belongs to event
- Check booth_id and event_id match
- Query booths for the event

---

### INSUFFICIENT_STOCK
**Description**: Product stock is insufficient

**Common Causes**:
- Product out of stock
- Stock quantity less than requested
- Concurrent stock depletion

**Example**:
```json
{
    "error_code": "INSUFFICIENT_STOCK",
    "message": "Insufficient stock for product 'Milk Tea'. Available: 0, required: 1"
}
```

**Resolution**:
- Check product stock availability
- Restock product
- Choose different product

---

### NEGATIVE_PRICE
**Description**: Price cannot be negative

**Common Causes**:
- Negative value provided for price
- Invalid price calculation

**Example**:
```json
{
    "error_code": "NEGATIVE_PRICE",
    "message": "Price cannot be negative: -500"
}
```

**Resolution**:
- Provide non-negative price value
- Check price calculation logic

---

### NEGATIVE_STOCK
**Description**: Stock cannot be negative

**Common Causes**:
- Negative value provided for stock
- Invalid stock calculation

**Example**:
```json
{
    "error_code": "NEGATIVE_STOCK",
    "message": "Stock cannot be negative: -10"
}
```

**Resolution**:
- Provide non-negative stock value
- Use null for unlimited stock
- Check stock calculation logic

---

### INSUFFICIENT_FUNDS
**Description**: Account balance is insufficient

**Common Causes**:
- Payment amount exceeds balance
- Account has zero balance
- Concurrent transactions depleted balance

**Example**:
```json
{
    "error_code": "INSUFFICIENT_FUNDS",
    "message": "Insufficient balance. Current balance: 10.00, required: 25.00"
}
```

**Resolution**:
- Check account balance
- Recharge account
- Reduce payment amount

---

### EVENT_INACTIVE
**Description**: Event is not active

**Common Causes**:
- Event status is not 'active'
- Event has ended
- Event not yet started
- Event was cancelled

**Example**:
```json
{
    "error_code": "EVENT_INACTIVE",
    "message": "Event 'Campus Festival' is not active. Current status: ended"
}
```

**Resolution**:
- Check event status
- Wait for event to start
- Use active event

---

### BOOTH_INACTIVE
**Description**: Booth is not active

**Common Causes**:
- Booth status is not 'active'
- Booth was closed
- Booth was deactivated

**Example**:
```json
{
    "error_code": "BOOTH_INACTIVE",
    "message": "Booth 'Food Stall' is not active. Current status: closed"
}
```

**Resolution**:
- Check booth status
- Reactivate booth
- Use active booth

---

### PRODUCT_DISABLED
**Description**: Product is disabled

**Common Causes**:
- Product enabled flag is false
- Product was temporarily disabled
- Product out of season

**Example**:
```json
{
    "error_code": "PRODUCT_DISABLED",
    "message": "Product 'Milk Tea' is currently disabled"
}
```

**Resolution**:
- Enable product
- Choose different product
- Check product availability

---

### USER_BLOCKED
**Description**: User account is blocked

**Common Causes**:
- User violated policies
- Account was suspended
- Security measure

**Example**:
```json
{
    "error_code": "USER_BLOCKED",
    "message": "User account is blocked"
}
```

**Resolution**:
- Contact administrator
- Resolve account issues
- Use different account

---

### MISSING_FILTER
**Description**: Required filter parameter is missing

**Common Causes**:
- Query requires event_id or booth_id
- Filter parameter not provided
- Attempting unfiltered query

**Example**:
```json
{
    "error_code": "MISSING_FILTER",
    "message": "Please specify either event_id or booth_id to filter transactions"
}
```

**Resolution**:
- Provide required filter parameter
- Check query parameter requirements
- Add event_id or booth_id to query

---

## Resource Not Found (404)

### BOOTH_NOT_FOUND
**Description**: Booth does not exist

**Common Causes**:
- Booth ID does not exist in database
- Booth was deleted
- Incorrect booth ID

**Example**:
```json
{
    "error_code": "BOOTH_NOT_FOUND",
    "message": "Booth with id 999 not found"
}
```

**Resolution**:
- Verify booth ID is correct
- Query booth list
- Create booth if needed

---

### PRODUCT_NOT_FOUND
**Description**: Product does not exist

**Common Causes**:
- Product ID does not exist in database
- Product was deleted
- Incorrect product ID

**Example**:
```json
{
    "error_code": "PRODUCT_NOT_FOUND",
    "message": "Product with id 999 not found"
}
```

**Resolution**:
- Verify product ID is correct
- Query product list
- Create product if needed

---

### USER_NOT_FOUND
**Description**: User does not exist

**Common Causes**:
- User ID does not exist in database
- User was deleted
- Incorrect user ID

**Example**:
```json
{
    "error_code": "USER_NOT_FOUND",
    "message": "User with id 999 not found"
}
```

**Resolution**:
- Verify user ID is correct
- Query user list
- Create user if needed

---

### EVENT_NOT_FOUND
**Description**: Event does not exist

**Common Causes**:
- Event ID does not exist in database
- Event was deleted
- Incorrect event ID

**Example**:
```json
{
    "error_code": "EVENT_NOT_FOUND",
    "message": "Event with id 999 not found"
}
```

**Resolution**:
- Verify event ID is correct
- Query event list
- Create event if needed

---

### PARTICIPANT_NOT_FOUND
**Description**: Participant does not exist

**Common Causes**:
- Participant not registered for event
- Card UID not found
- Incorrect card UID

**Example**:
```json
{
    "error_code": "PARTICIPANT_NOT_FOUND",
    "message": "Participant with card_uid 'A1B2C3D4' not found in event 1"
}
```

**Resolution**:
- Verify card UID is correct
- Register participant for event
- Check participant exists

---

## Internal Errors (500)

### INTERNAL_ERROR
**Description**: Internal server error

**Common Causes**:
- Unexpected exception
- Database connection error
- System malfunction

**Example**:
```json
{
    "error_code": "INTERNAL_ERROR",
    "message": "An internal error occurred. Please try again later."
}
```

**Resolution**:
- Retry the request
- Check server logs
- Contact system administrator
- Report bug if persistent

---

## Error Handling Best Practices

### 1. Check HTTP Status Code First

```python
response = requests.post(url, json=data, headers=headers)

if response.status_code == 200:
    # Success
    result = response.json()
elif response.status_code == 401:
    # Authentication error - login again
    handle_auth_error(response.json())
elif response.status_code == 403:
    # Permission error - check user role
    handle_permission_error(response.json())
elif response.status_code == 400:
    # Validation error - fix request
    handle_validation_error(response.json())
elif response.status_code == 404:
    # Resource not found
    handle_not_found_error(response.json())
else:
    # Other error
    handle_generic_error(response.json())
```

### 2. Parse Error Code for Specific Handling

```python
def handle_error(response):
    error_data = response.json()
    error_code = error_data.get('error_code')
    message = error_data.get('message')
    
    if error_code == 'TOKEN_EXPIRED':
        # Refresh token and retry
        refresh_token()
        retry_request()
    elif error_code == 'INSUFFICIENT_FUNDS':
        # Prompt user to recharge
        prompt_recharge(message)
    elif error_code == 'BOOTH_ACCESS_DENIED':
        # Show permission error
        show_permission_error(message)
    else:
        # Generic error handling
        show_error(message)
```

### 3. Log Errors for Debugging

```python
import logging

def make_api_request(url, data):
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        error_data = e.response.json()
        logging.error(
            f"API Error: {error_data['error_code']} - {error_data['message']}"
        )
        raise
```

### 4. Provide User-Friendly Messages

```python
ERROR_MESSAGES = {
    'INVALID_CREDENTIALS': '用户名或密码错误，请重试',
    'TOKEN_EXPIRED': '登录已过期，请重新登录',
    'INSUFFICIENT_FUNDS': '余额不足，请充值',
    'BOOTH_ACCESS_DENIED': '无权访问该摊位',
    'PRODUCT_NOT_FOUND': '商品不存在',
}

def get_user_message(error_code):
    return ERROR_MESSAGES.get(error_code, '操作失败，请稍后重试')
```

---

## Quick Reference Table

| Error Code | Status | Category | Common Resolution |
|------------|--------|----------|-------------------|
| AUTH_ERROR | 401 | Authentication | Check authentication credentials |
| INVALID_CREDENTIALS | 401 | Authentication | Verify username and password |
| TOKEN_EXPIRED | 401 | Authentication | Login again |
| TOKEN_INVALID | 401 | Authentication | Login again |
| AUTHENTICATION_REQUIRED | 401 | Authentication | Include JWT token |
| PERMISSION_DENIED | 403 | Authorization | Check user role |
| BOOTH_ACCESS_DENIED | 403 | Authorization | Verify booth ownership |
| ROLE_NOT_ALLOWED | 403 | Authorization | Use correct role |
| VALIDATION_ERROR | 400 | Validation | Fix request data |
| INSUFFICIENT_FUNDS | 400 | Business Logic | Recharge account |
| PRODUCT_NOT_IN_BOOTH | 400 | Validation | Check product-booth relationship |
| BOOTH_NOT_FOUND | 404 | Resource | Verify booth exists |
| PRODUCT_NOT_FOUND | 404 | Resource | Verify product exists |
| USER_NOT_FOUND | 404 | Resource | Verify user exists |
| INTERNAL_ERROR | 500 | System | Retry or contact admin |

---

For more information, see the main API documentation at `docs/API_DOCUMENTATION.md`.
