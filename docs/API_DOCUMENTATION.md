# API Documentation - NFC Campus E-Wallet System

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
   - [Authentication Endpoints](#authentication-endpoints)
   - [User Management](#user-management)
   - [Booth Management](#booth-management)
   - [Product Management](#product-management)
   - [Transaction Management](#transaction-management)
   - [Payment Processing](#payment-processing)
4. [Error Codes](#error-codes)
5. [Usage Examples](#usage-examples)

---

## Overview

The NFC Campus E-Wallet System provides a RESTful API for managing campus events, booths, products, and transactions. The system supports three operational modes:

- **Booth Mode**: Full booth management with JWT authentication
- **Event Mode**: Event-based participant accounts with NFC cards
- **Legacy Mode**: Traditional UID-based operations (backward compatible)

### Base URL

```
http://localhost:8000
```

### Response Format

All responses are in JSON format. Success responses contain data fields, while error responses follow this structure:

```json
{
    "error_code": "ERROR_CODE",
    "message": "Human-readable error message"
}
```

---

## Authentication

The system supports two authentication methods:

### 1. JWT Authentication (Booth Management)

Used for booth management, user management, and admin operations.

**How to authenticate:**
1. Login with username and password to get JWT token
2. Include token in subsequent requests:
   ```
   Authorization: Bearer <your_jwt_token>
   ```

**Token expiration:** Configurable (default: 24 hours)

### 2. Signature Verification (NFC Client)

Used for NFC client operations (balance query, payment, recharge).

**Signature calculation:**
```
SHA256(uid + amount + timestamp + secret_key)
```

**Required fields:**
- `timestamp`: Unix timestamp (must be within 60 seconds of server time)
- `signature`: SHA256 hash as hexadecimal string

---

## API Endpoints

### Authentication Endpoints

#### POST /auth/login

User login to obtain JWT access token.

**Request Body:**
```json
{
    "username": "admin",
    "password": "password123"
}
```

**Response (200 OK):**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
        "id": 1,
        "username": "admin",
        "role": "super_admin",
        "booth_id": null,
        "status": "active",
        "created_at": "2024-02-01T10:00:00Z"
    }
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials or user blocked
  ```json
  {
      "error_code": "INVALID_CREDENTIALS",
      "message": "Invalid username or password"
  }
  ```

---

#### GET /auth/me

Get current authenticated user information.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
{
    "id": 1,
    "username": "admin",
    "role": "super_admin",
    "booth_id": null,
    "status": "active",
    "created_at": "2024-02-01T10:00:00Z"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired token
- `403 Forbidden`: User blocked or inactive

---

### User Management

#### POST /users

Create a new user account. **Requires: super_admin role**

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
    "username": "cashier01",
    "password": "password123",
    "role": "booth_cashier",
    "booth_id": 1
}
```

**Field Descriptions:**
- `username`: Unique username (1-50 characters)
- `password`: Password (6-100 characters)
- `role`: One of: `super_admin`, `event_admin`, `booth_cashier`, `issuer`, `reviewer`
- `booth_id`: Required for `booth_cashier` role, null for others

**Response (201 Created):**
```json
{
    "id": 5,
    "username": "cashier01",
    "role": "booth_cashier",
    "booth_id": 1,
    "status": "active",
    "created_at": "2024-02-01T12:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Validation error (username exists, invalid role, etc.)
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not super_admin

---

#### GET /users

List all users with optional filtering. **Requires: super_admin role**

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `role` (optional): Filter by role
- `booth_id` (optional): Filter by booth ID
- `status` (optional): Filter by status (active/inactive/blocked)
- `limit` (optional): Max results (default: 100, max: 1000)
- `offset` (optional): Skip results (default: 0)

**Example Request:**
```
GET /users?role=booth_cashier&status=active&limit=10
```

**Response (200 OK):**
```json
[
    {
        "id": 5,
        "username": "cashier01",
        "role": "booth_cashier",
        "booth_id": 1,
        "status": "active",
        "created_at": "2024-02-01T12:00:00Z"
    },
    {
        "id": 6,
        "username": "cashier02",
        "role": "booth_cashier",
        "booth_id": 2,
        "status": "active",
        "created_at": "2024-02-01T12:05:00Z"
    }
]
```

---

#### GET /users/{user_id}

Get user details by ID. **Requires: super_admin role**

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
{
    "id": 5,
    "username": "cashier01",
    "role": "booth_cashier",
    "booth_id": 1,
    "status": "active",
    "created_at": "2024-02-01T12:00:00Z"
}
```

**Error Responses:**
- `404 Not Found`: User does not exist

---

#### PATCH /users/{user_id}/status

Update user status. **Requires: super_admin role**

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `status` (required): New status (`active`, `inactive`, or `blocked`)

**Example Request:**
```
PATCH /users/5/status?status=inactive
```

**Response (200 OK):**
```json
{
    "id": 5,
    "username": "cashier01",
    "role": "booth_cashier",
    "booth_id": 1,
    "status": "inactive",
    "created_at": "2024-02-01T12:00:00Z"
}
```

---

### Booth Management

#### POST /booths

Create a new booth. **Requires: event_admin or super_admin role**

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
    "event_id": 1,
    "name": "美食摊",
    "class_name": "高一(1)班"
}
```

**Response (201 Created):**
```json
{
    "id": 1,
    "event_id": 1,
    "name": "美食摊",
    "class_name": "高一(1)班",
    "status": "active",
    "created_at": "2024-02-01T10:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid event_id
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Insufficient permissions

---

#### GET /booths

List booths with optional filtering. **Requires: event_admin or super_admin role**

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `event_id` (optional): Filter by event ID
- `status` (optional): Filter by status (active/inactive/closed)
- `limit` (optional): Max results (default: 100, max: 1000)
- `offset` (optional): Skip results (default: 0)

**Example Request:**
```
GET /booths?event_id=1&status=active
```

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "event_id": 1,
        "name": "美食摊",
        "class_name": "高一(1)班",
        "status": "active",
        "created_at": "2024-02-01T10:00:00Z"
    },
    {
        "id": 2,
        "event_id": 1,
        "name": "游戏摊",
        "class_name": "高一(2)班",
        "status": "active",
        "created_at": "2024-02-01T10:05:00Z"
    }
]
```

---

#### GET /booths/{booth_id}

Get booth details by ID.

**Permissions:**
- `super_admin`, `event_admin`: Can view all booths
- `booth_cashier`: Can only view their assigned booth

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
{
    "id": 1,
    "event_id": 1,
    "name": "美食摊",
    "class_name": "高一(1)班",
    "status": "active",
    "created_at": "2024-02-01T10:00:00Z"
}
```

**Error Responses:**
- `403 Forbidden`: Booth cashier accessing another booth
- `404 Not Found`: Booth does not exist

---

#### POST /booths/{booth_id}/pay

Process a booth payment transaction.

**Permissions:**
- `super_admin`, `event_admin`: Can process payments for any booth
- `booth_cashier`: Can only process payments for their assigned booth
- `issuer`: Cannot process payments (403 error)

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
    "event_id": 1,
    "card_uid": "A1B2C3D4",
    "amount": 25.00,
    "product_id": 5,
    "remark": "购买奶茶"
}
```

**Field Descriptions:**
- `event_id`: Event ID (required)
- `card_uid`: NFC card UID (required)
- `amount`: Payment amount in yuan (required, must be positive)
- `product_id`: Product ID (optional)
- `remark`: Transaction remark (optional, max 255 characters)

**Response (200 OK):**
```json
{
    "success": true,
    "new_balance": 75.50,
    "transaction_id": 12345,
    "balance_before": 100.50,
    "event_id": 1,
    "participant_id": 1,
    "booth_id": 1,
    "product_id": 5,
    "operator_id": 3
}
```

**Error Responses:**
- `400 Bad Request`: Validation errors (booth not in event, product not in booth, insufficient funds)
- `403 Forbidden`: Booth cashier accessing another booth, issuer attempting payment
- `404 Not Found`: Booth, product, or participant not found

---

#### GET /booths/{booth_id}/transactions

Get transaction history for a booth.

**Permissions:**
- `super_admin`, `event_admin`: Can view all booth transactions
- `booth_cashier`: Can only view their assigned booth transactions

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `start_date` (optional): Start date filter (ISO format: YYYY-MM-DD)
- `end_date` (optional): End date filter (ISO format: YYYY-MM-DD)
- `limit` (optional): Max results (default: 100, max: 1000)
- `offset` (optional): Skip results (default: 0)

**Example Request:**
```
GET /booths/1/transactions?start_date=2024-01-01&limit=10
```

**Response (200 OK):**
```json
{
    "transactions": [
        {
            "id": 12345,
            "type": "pay",
            "amount": 25.00,
            "balance_before": 100.50,
            "balance_after": 75.50,
            "participant_id": 1,
            "card_uid": "A1B2C3D4",
            "booth_id": 1,
            "product_id": 5,
            "operator_id": 3,
            "remark": "购买奶茶",
            "created_at": "2024-01-15T10:30:00Z"
        }
    ],
    "total_count": 1
}
```

---

### Product Management

#### POST /products

Create a new product. **Requires: event_admin or super_admin role**

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
    "booth_id": 1,
    "name": "奶茶",
    "price": 500,
    "cost_price": 300,
    "stock": 100
}
```

**Field Descriptions:**
- `booth_id`: Booth ID (required)
- `name`: Product name (required, 1-100 characters)
- `price`: Selling price in cents (required, non-negative integer)
- `cost_price`: Cost price in cents (optional, non-negative integer)
- `stock`: Stock quantity (optional, non-negative integer or null for unlimited)

**Response (201 Created):**
```json
{
    "id": 1,
    "booth_id": 1,
    "name": "奶茶",
    "price": 500,
    "cost_price": 300,
    "stock": 100,
    "enabled": true,
    "created_at": "2024-02-01T10:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid booth_id, negative price, negative stock
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Insufficient permissions

---

#### GET /products

List products with optional filtering.

**Permissions:**
- `super_admin`, `event_admin`: Can view all products
- `booth_cashier`: Can only view products from their assigned booth

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `booth_id` (optional): Filter by booth ID
- `enabled` (optional): Filter by enabled status (true/false)
- `limit` (optional): Max results (default: 100, max: 1000)
- `offset` (optional): Skip results (default: 0)

**Example Request:**
```
GET /products?booth_id=1&enabled=true
```

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "booth_id": 1,
        "name": "奶茶",
        "price": 500,
        "cost_price": 300,
        "stock": 100,
        "enabled": true,
        "created_at": "2024-02-01T10:00:00Z"
    },
    {
        "id": 2,
        "booth_id": 1,
        "name": "咖啡",
        "price": 600,
        "cost_price": 350,
        "stock": 80,
        "enabled": true,
        "created_at": "2024-02-01T10:05:00Z"
    }
]
```

**Error Responses:**
- `403 Forbidden`: Booth cashier accessing another booth's products

---

#### PATCH /products/{product_id}

Update product information. **Requires: event_admin or super_admin role**

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body (all fields optional):**
```json
{
    "name": "奶茶（大杯）",
    "price": 600,
    "cost_price": 350,
    "stock": 80,
    "enabled": true
}
```

**Response (200 OK):**
```json
{
    "id": 1,
    "booth_id": 1,
    "name": "奶茶（大杯）",
    "price": 600,
    "cost_price": 350,
    "stock": 80,
    "enabled": true,
    "created_at": "2024-02-01T10:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Negative price or stock
- `404 Not Found`: Product does not exist

---

### Transaction Management

#### GET /transactions

Query transaction history with filters.

**Permissions:**
- `super_admin`, `event_admin`: Can view all transactions (must specify event_id or booth_id)
- `booth_cashier`: Can only view their assigned booth transactions
- `issuer`: Can view all transactions for auditing (must specify event_id or booth_id)

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `event_id` (optional): Filter by event ID
- `booth_id` (optional): Filter by booth ID
- `product_id` (optional): Filter by product ID
- `start_date` (optional): Start date filter (ISO format: YYYY-MM-DD)
- `end_date` (optional): End date filter (ISO format: YYYY-MM-DD)
- `limit` (optional): Max results (default: 100, max: 1000)
- `offset` (optional): Skip results (default: 0)

**Example Request:**
```
GET /transactions?event_id=1&booth_id=1&start_date=2024-01-01
```

**Response (200 OK):**
```json
{
    "transactions": [
        {
            "id": 12345,
            "type": "pay",
            "amount": 25.00,
            "balance_before": 100.50,
            "balance_after": 75.50,
            "participant_id": 1,
            "card_uid": "A1B2C3D4",
            "booth_id": 1,
            "product_id": 5,
            "operator_id": 3,
            "merchant_id": null,
            "related_txn_id": null,
            "remark": "购买奶茶",
            "created_at": "2024-01-15T10:30:00Z"
        }
    ],
    "total_count": 1
}
```

**Error Responses:**
- `400 Bad Request`: Missing required filter (event_id or booth_id)
- `403 Forbidden`: Booth cashier accessing another booth's transactions
- `404 Not Found`: Booth or product not found

---

### Payment Processing

#### POST /pay

Process a payment transaction. Supports three modes:

1. **Booth Mode** (requires JWT authentication)
2. **Event Mode** (requires signature verification)
3. **Legacy Mode** (requires signature verification)

**Booth Mode Request:**

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
    "event_id": 1,
    "card_uid": "A1B2C3D4",
    "booth_id": 1,
    "product_id": 5,
    "amount": 25.00,
    "timestamp": 1234567890,
    "signature": "abc123..."
}
```

**Event Mode Request:**

**Request Body:**
```json
{
    "event_id": 1,
    "card_uid": "A1B2C3D4",
    "amount": 25.00,
    "timestamp": 1234567890,
    "signature": "abc123...",
    "merchant_id": "MERCHANT001",
    "remark": "购买商品"
}
```

**Legacy Mode Request:**

**Request Body:**
```json
{
    "uid": "A1B2C3D4",
    "amount": 25.00,
    "timestamp": 1234567890,
    "signature": "abc123...",
    "merchant_id": "MERCHANT001",
    "remark": "购买商品"
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "new_balance": 75.50,
    "transaction_id": 12345,
    "balance_before": 100.50,
    "booth_id": 1,
    "product_id": 5,
    "operator_id": 3
}
```

**Error Responses:**
- `400 Bad Request`: Validation errors, insufficient funds
- `401 Unauthorized`: JWT authentication required for booth mode
- `403 Forbidden`: Permission denied

---

## Error Codes

### Authentication Errors (401)

| Error Code | Description |
|------------|-------------|
| `AUTH_ERROR` | General authentication error |
| `INVALID_CREDENTIALS` | Invalid username or password |
| `TOKEN_EXPIRED` | JWT token has expired |
| `TOKEN_INVALID` | JWT token is invalid |
| `TOKEN_MISSING` | JWT token is missing |
| `AUTHENTICATION_REQUIRED` | JWT authentication required for this operation |

### Authorization Errors (403)

| Error Code | Description |
|------------|-------------|
| `PERMISSION_DENIED` | Insufficient permissions |
| `BOOTH_ACCESS_DENIED` | Cannot access this booth |
| `ROLE_NOT_ALLOWED` | Role not allowed for this operation |

### Validation Errors (400)

| Error Code | Description |
|------------|-------------|
| `VALIDATION_ERROR` | General validation error |
| `INVALID_BOOTH_ID` | Invalid booth ID |
| `INVALID_PRODUCT_ID` | Invalid product ID |
| `INVALID_EVENT_ID` | Invalid event ID |
| `PRODUCT_NOT_IN_BOOTH` | Product does not belong to booth |
| `BOOTH_NOT_IN_EVENT` | Booth does not belong to event |
| `INSUFFICIENT_STOCK` | Product stock insufficient |
| `NEGATIVE_PRICE` | Price cannot be negative |
| `NEGATIVE_STOCK` | Stock cannot be negative |
| `INSUFFICIENT_FUNDS` | Insufficient balance |
| `EVENT_INACTIVE` | Event is not active |
| `BOOTH_INACTIVE` | Booth is not active |
| `PRODUCT_DISABLED` | Product is disabled |
| `USER_BLOCKED` | User account is blocked |
| `MISSING_FILTER` | Required filter parameter missing |

### Resource Not Found (404)

| Error Code | Description |
|------------|-------------|
| `BOOTH_NOT_FOUND` | Booth not found |
| `PRODUCT_NOT_FOUND` | Product not found |
| `USER_NOT_FOUND` | User not found |
| `EVENT_NOT_FOUND` | Event not found |
| `PARTICIPANT_NOT_FOUND` | Participant not found |

### Internal Errors (500)

| Error Code | Description |
|------------|-------------|
| `INTERNAL_ERROR` | Internal server error |

---

## Usage Examples

### Example 1: Complete Booth Operation Flow

```bash
# 1. Login as event admin
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "event_admin",
    "password": "password123"
  }'

# Response: Save the access_token
# TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# 2. Create a booth
curl -X POST http://localhost:8000/booths \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "name": "美食摊",
    "class_name": "高一(1)班"
  }'

# Response: Save the booth id
# BOOTH_ID=1

# 3. Create products for the booth
curl -X POST http://localhost:8000/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booth_id": 1,
    "name": "奶茶",
    "price": 500,
    "cost_price": 300,
    "stock": 100
  }'

# 4. Create a booth cashier user
curl -X POST http://localhost:8000/users \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "cashier01",
    "password": "password123",
    "role": "booth_cashier",
    "booth_id": 1
  }'

# 5. Login as booth cashier
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "cashier01",
    "password": "password123"
  }'

# CASHIER_TOKEN="..."

# 6. View booth products
curl -X GET "http://localhost:8000/products?booth_id=1" \
  -H "Authorization: Bearer $CASHIER_TOKEN"

# 7. Process a booth payment
curl -X POST http://localhost:8000/booths/1/pay \
  -H "Authorization: Bearer $CASHIER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "card_uid": "A1B2C3D4",
    "amount": 5.00,
    "product_id": 1,
    "remark": "购买奶茶"
  }'

# 8. View booth transactions
curl -X GET "http://localhost:8000/booths/1/transactions?limit=10" \
  -H "Authorization: Bearer $CASHIER_TOKEN"
```

### Example 2: User Management

```bash
# Login as super admin
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "super_admin",
    "password": "admin_password"
  }'

# TOKEN="..."

# List all users
curl -X GET "http://localhost:8000/users?limit=50" \
  -H "Authorization: Bearer $TOKEN"

# Get specific user
curl -X GET http://localhost:8000/users/5 \
  -H "Authorization: Bearer $TOKEN"

# Update user status
curl -X PATCH "http://localhost:8000/users/5/status?status=inactive" \
  -H "Authorization: Bearer $TOKEN"
```

### Example 3: Transaction Query

```bash
# Login as event admin
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "event_admin",
    "password": "password123"
  }'

# TOKEN="..."

# Query transactions by event
curl -X GET "http://localhost:8000/transactions?event_id=1&start_date=2024-01-01&limit=100" \
  -H "Authorization: Bearer $TOKEN"

# Query transactions by booth
curl -X GET "http://localhost:8000/transactions?booth_id=1&start_date=2024-01-01" \
  -H "Authorization: Bearer $TOKEN"

# Query transactions by product
curl -X GET "http://localhost:8000/transactions?booth_id=1&product_id=5" \
  -H "Authorization: Bearer $TOKEN"
```

### Example 4: Product Management

```bash
# Login as event admin
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "event_admin",
    "password": "password123"
  }'

# TOKEN="..."

# Create product
curl -X POST http://localhost:8000/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booth_id": 1,
    "name": "咖啡",
    "price": 600,
    "cost_price": 350,
    "stock": 80
  }'

# Update product
curl -X PATCH http://localhost:8000/products/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 650,
    "stock": 70
  }'

# List products
curl -X GET "http://localhost:8000/products?booth_id=1&enabled=true" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Notes

1. **Timestamps**: All timestamps are in UTC and follow ISO 8601 format
2. **Amounts**: Payment amounts are in yuan (元), but stored internally in cents (分)
3. **Pagination**: Use `limit` and `offset` parameters for pagination
4. **Filtering**: Most list endpoints support filtering by relevant fields
5. **Authentication**: JWT tokens expire after configured time (default: 24 hours)
6. **Permissions**: Each endpoint documents required roles and permissions
7. **Error Handling**: All errors return consistent JSON format with error_code and message

For more information, see the main README.md or contact the development team.
