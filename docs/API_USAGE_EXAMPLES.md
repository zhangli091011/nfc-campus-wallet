# API Usage Examples - Booth Management System

This document provides practical examples for using the NFC Campus E-Wallet API with the Booth Management System.

## Table of Contents

1. [Authentication Flow](#authentication-flow)
2. [Booth Management Workflow](#booth-management-workflow)
3. [Product Management](#product-management)
4. [Payment Processing](#payment-processing)
5. [Transaction Queries](#transaction-queries)
6. [User Management](#user-management)
7. [Error Handling](#error-handling)

---

## Authentication Flow

### Example 1: User Login

```bash
# Login request
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password123"
  }'
```

**Response:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6InN1cGVyX2FkbWluIiwiYm9vdGhfaWQiOm51bGwsImV4cCI6MTcwNzIzNDU2NywiaWF0IjoxNzA3MTQ4MTY3fQ.abc123...",
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

**Save the token for subsequent requests:**
```bash
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Example 2: Get Current User Info

```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
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

---

## Booth Management Workflow

### Example 3: Create Event and Booth

```bash
# Step 1: Create an event (assuming event creation endpoint exists)
curl -X POST http://localhost:8000/events \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "校园文化节",
    "start_time": "2024-03-01T09:00:00Z",
    "end_time": "2024-03-01T18:00:00Z",
    "allow_recharge": true,
    "allow_payment": true
  }'

# Step 2: Create a booth for the event
curl -X POST http://localhost:8000/booths \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "name": "美食摊",
    "class_name": "高一(1)班"
  }'
```

**Response:**
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

### Example 4: List Booths for an Event

```bash
curl -X GET "http://localhost:8000/booths?event_id=1&status=active" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
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

### Example 5: Get Booth Details

```bash
curl -X GET http://localhost:8000/booths/1 \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
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

---

## Product Management

### Example 6: Create Products for a Booth

```bash
# Create product 1: 奶茶
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

# Create product 2: 咖啡
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

# Create product 3: 蛋糕 (unlimited stock)
curl -X POST http://localhost:8000/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booth_id": 1,
    "name": "蛋糕",
    "price": 800,
    "cost_price": 450,
    "stock": null
  }'
```

**Response (Product 1):**
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

### Example 7: List Products for a Booth

```bash
curl -X GET "http://localhost:8000/products?booth_id=1&enabled=true" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
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
    },
    {
        "id": 3,
        "booth_id": 1,
        "name": "蛋糕",
        "price": 800,
        "cost_price": 450,
        "stock": null,
        "enabled": true,
        "created_at": "2024-02-01T10:10:00Z"
    }
]
```

### Example 8: Update Product

```bash
# Update price and stock
curl -X PATCH http://localhost:8000/products/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 550,
    "stock": 90
  }'

# Disable a product
curl -X PATCH http://localhost:8000/products/2 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": false
  }'
```

**Response:**
```json
{
    "id": 1,
    "booth_id": 1,
    "name": "奶茶",
    "price": 550,
    "cost_price": 300,
    "stock": 90,
    "enabled": true,
    "created_at": "2024-02-01T10:00:00Z"
}
```

---

## Payment Processing

### Example 9: Booth Payment with Product

```bash
# Login as booth cashier
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "cashier01",
    "password": "password123"
  }'

# Save cashier token
export CASHIER_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Process payment
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
```

**Response:**
```json
{
    "success": true,
    "new_balance": 95.00,
    "transaction_id": 12345,
    "balance_before": 100.00,
    "event_id": 1,
    "participant_id": 1,
    "booth_id": 1,
    "product_id": 1,
    "operator_id": 5
}
```

### Example 10: Booth Payment without Product

```bash
# Payment without specifying product
curl -X POST http://localhost:8000/booths/1/pay \
  -H "Authorization: Bearer $CASHIER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "card_uid": "A1B2C3D4",
    "amount": 10.00,
    "remark": "综合消费"
  }'
```

**Response:**
```json
{
    "success": true,
    "new_balance": 85.00,
    "transaction_id": 12346,
    "balance_before": 95.00,
    "event_id": 1,
    "participant_id": 1,
    "booth_id": 1,
    "product_id": null,
    "operator_id": 5
}
```

### Example 11: Generic Payment Endpoint (Booth Mode)

```bash
# Using the generic /pay endpoint with booth information
curl -X POST http://localhost:8000/pay \
  -H "Authorization: Bearer $CASHIER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "card_uid": "A1B2C3D4",
    "booth_id": 1,
    "product_id": 1,
    "amount": 5.00,
    "timestamp": 1707148167,
    "signature": "abc123..."
  }'
```

---

## Transaction Queries

### Example 12: Query Booth Transactions

```bash
# Get all transactions for a booth
curl -X GET "http://localhost:8000/booths/1/transactions?limit=10" \
  -H "Authorization: Bearer $CASHIER_TOKEN"

# Get transactions with date filter
curl -X GET "http://localhost:8000/booths/1/transactions?start_date=2024-02-01&end_date=2024-02-28&limit=50" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
    "transactions": [
        {
            "id": 12345,
            "type": "pay",
            "amount": 5.00,
            "balance_before": 100.00,
            "balance_after": 95.00,
            "participant_id": 1,
            "card_uid": "A1B2C3D4",
            "booth_id": 1,
            "product_id": 1,
            "operator_id": 5,
            "merchant_id": null,
            "related_txn_id": null,
            "remark": "购买奶茶",
            "created_at": "2024-02-01T10:30:00Z"
        },
        {
            "id": 12346,
            "type": "pay",
            "amount": 10.00,
            "balance_before": 95.00,
            "balance_after": 85.00,
            "participant_id": 1,
            "card_uid": "A1B2C3D4",
            "booth_id": 1,
            "product_id": null,
            "operator_id": 5,
            "merchant_id": null,
            "related_txn_id": null,
            "remark": "综合消费",
            "created_at": "2024-02-01T10:35:00Z"
        }
    ],
    "total_count": 2
}
```

### Example 13: Query Transactions by Event

```bash
# Login as event admin
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "event_admin",
    "password": "password123"
  }'

export ADMIN_TOKEN="..."

# Query all transactions for an event
curl -X GET "http://localhost:8000/transactions?event_id=1&limit=100" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Example 14: Query Transactions by Product

```bash
# Query transactions for a specific product
curl -X GET "http://localhost:8000/transactions?booth_id=1&product_id=1&start_date=2024-02-01" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Response:**
```json
{
    "transactions": [
        {
            "id": 12345,
            "type": "pay",
            "amount": 5.00,
            "balance_before": 100.00,
            "balance_after": 95.00,
            "participant_id": 1,
            "card_uid": "A1B2C3D4",
            "booth_id": 1,
            "product_id": 1,
            "operator_id": 5,
            "remark": "购买奶茶",
            "created_at": "2024-02-01T10:30:00Z"
        }
    ],
    "total_count": 1
}
```

---

## User Management

### Example 15: Create Booth Cashier User

```bash
# Login as super admin
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "super_admin",
    "password": "admin_password"
  }'

export SUPER_ADMIN_TOKEN="..."

# Create booth cashier
curl -X POST http://localhost:8000/users \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "cashier01",
    "password": "password123",
    "role": "booth_cashier",
    "booth_id": 1
  }'
```

**Response:**
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

### Example 16: Create Event Admin User

```bash
curl -X POST http://localhost:8000/users \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "event_admin01",
    "password": "password123",
    "role": "event_admin",
    "booth_id": null
  }'
```

### Example 17: Create Issuer User

```bash
curl -X POST http://localhost:8000/users \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "issuer01",
    "password": "password123",
    "role": "issuer",
    "booth_id": null
  }'
```

### Example 18: List Users by Role

```bash
# List all booth cashiers
curl -X GET "http://localhost:8000/users?role=booth_cashier&status=active" \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN"

# List all event admins
curl -X GET "http://localhost:8000/users?role=event_admin" \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN"
```

### Example 19: Update User Status

```bash
# Deactivate a user
curl -X PATCH "http://localhost:8000/users/5/status?status=inactive" \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN"

# Block a user
curl -X PATCH "http://localhost:8000/users/6/status?status=blocked" \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN"

# Reactivate a user
curl -X PATCH "http://localhost:8000/users/5/status?status=active" \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN"
```

---

## Error Handling

### Example 20: Handling Authentication Errors

```bash
# Invalid credentials
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "wrong_password"
  }'
```

**Error Response (401):**
```json
{
    "error_code": "INVALID_CREDENTIALS",
    "message": "Invalid username or password"
}
```

### Example 21: Handling Authorization Errors

```bash
# Booth cashier trying to access another booth
curl -X GET http://localhost:8000/booths/2 \
  -H "Authorization: Bearer $CASHIER_TOKEN"
```

**Error Response (403):**
```json
{
    "error_code": "BOOTH_ACCESS_DENIED",
    "message": "Access denied. You can only access booth 1. Requested booth: 2"
}
```

### Example 22: Handling Validation Errors

```bash
# Product not in booth
curl -X POST http://localhost:8000/booths/1/pay \
  -H "Authorization: Bearer $CASHIER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "card_uid": "A1B2C3D4",
    "amount": 5.00,
    "product_id": 999,
    "remark": "购买商品"
  }'
```

**Error Response (400):**
```json
{
    "error_code": "PRODUCT_NOT_FOUND",
    "message": "Product with id 999 not found"
}
```

### Example 23: Handling Insufficient Funds

```bash
# Payment exceeds balance
curl -X POST http://localhost:8000/booths/1/pay \
  -H "Authorization: Bearer $CASHIER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "card_uid": "A1B2C3D4",
    "amount": 1000.00,
    "remark": "大额消费"
  }'
```

**Error Response (400):**
```json
{
    "error_code": "INSUFFICIENT_FUNDS",
    "message": "Insufficient balance. Current balance: 85.00, required: 1000.00"
}
```

---

## Complete Workflow Example

### Scenario: Setting up and operating a booth

```bash
#!/bin/bash

# Configuration
API_BASE="http://localhost:8000"

echo "=== Step 1: Login as Super Admin ==="
SUPER_ADMIN_RESPONSE=$(curl -s -X POST $API_BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "super_admin",
    "password": "admin_password"
  }')

SUPER_ADMIN_TOKEN=$(echo $SUPER_ADMIN_RESPONSE | jq -r '.access_token')
echo "Super Admin Token: $SUPER_ADMIN_TOKEN"

echo -e "\n=== Step 2: Login as Event Admin ==="
EVENT_ADMIN_RESPONSE=$(curl -s -X POST $API_BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "event_admin",
    "password": "password123"
  }')

EVENT_ADMIN_TOKEN=$(echo $EVENT_ADMIN_RESPONSE | jq -r '.access_token')
echo "Event Admin Token: $EVENT_ADMIN_TOKEN"

echo -e "\n=== Step 3: Create Booth ==="
BOOTH_RESPONSE=$(curl -s -X POST $API_BASE/booths \
  -H "Authorization: Bearer $EVENT_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "name": "美食摊",
    "class_name": "高一(1)班"
  }')

BOOTH_ID=$(echo $BOOTH_RESPONSE | jq -r '.id')
echo "Created Booth ID: $BOOTH_ID"

echo -e "\n=== Step 4: Create Products ==="
curl -s -X POST $API_BASE/products \
  -H "Authorization: Bearer $EVENT_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"booth_id\": $BOOTH_ID,
    \"name\": \"奶茶\",
    \"price\": 500,
    \"cost_price\": 300,
    \"stock\": 100
  }" | jq '.'

curl -s -X POST $API_BASE/products \
  -H "Authorization: Bearer $EVENT_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"booth_id\": $BOOTH_ID,
    \"name\": \"咖啡\",
    \"price\": 600,
    \"cost_price\": 350,
    \"stock\": 80
  }" | jq '.'

echo -e "\n=== Step 5: Create Booth Cashier ==="
CASHIER_RESPONSE=$(curl -s -X POST $API_BASE/users \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"cashier_booth_${BOOTH_ID}\",
    \"password\": \"password123\",
    \"role\": \"booth_cashier\",
    \"booth_id\": $BOOTH_ID
  }")

echo $CASHIER_RESPONSE | jq '.'

echo -e "\n=== Step 6: Login as Booth Cashier ==="
CASHIER_LOGIN_RESPONSE=$(curl -s -X POST $API_BASE/auth/login \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"cashier_booth_${BOOTH_ID}\",
    \"password\": \"password123\"
  }")

CASHIER_TOKEN=$(echo $CASHIER_LOGIN_RESPONSE | jq -r '.access_token')
echo "Cashier Token: $CASHIER_TOKEN"

echo -e "\n=== Step 7: View Booth Products ==="
curl -s -X GET "$API_BASE/products?booth_id=$BOOTH_ID" \
  -H "Authorization: Bearer $CASHIER_TOKEN" | jq '.'

echo -e "\n=== Step 8: Process Payment ==="
curl -s -X POST $API_BASE/booths/$BOOTH_ID/pay \
  -H "Authorization: Bearer $CASHIER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "card_uid": "A1B2C3D4",
    "amount": 5.00,
    "product_id": 1,
    "remark": "购买奶茶"
  }' | jq '.'

echo -e "\n=== Step 9: View Booth Transactions ==="
curl -s -X GET "$API_BASE/booths/$BOOTH_ID/transactions?limit=10" \
  -H "Authorization: Bearer $CASHIER_TOKEN" | jq '.'

echo -e "\n=== Workflow Complete ==="
```

---

## Tips and Best Practices

1. **Token Management**: Store JWT tokens securely and refresh them before expiration
2. **Error Handling**: Always check response status codes and handle errors appropriately
3. **Pagination**: Use `limit` and `offset` for large result sets
4. **Date Filters**: Use ISO format (YYYY-MM-DD) for date parameters
5. **Amount Format**: Amounts are in yuan (元) for API requests, but stored as cents internally
6. **Permissions**: Check user role before attempting operations
7. **Logging**: Log all API requests and responses for debugging
8. **Testing**: Test with different user roles to ensure proper permission enforcement

For more information, see the main API documentation at `docs/API_DOCUMENTATION.md`.
