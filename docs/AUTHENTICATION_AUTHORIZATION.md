# Authentication and Authorization Guide

This document explains the authentication and authorization mechanisms in the NFC Campus E-Wallet System with Booth Management.

## Table of Contents

1. [Overview](#overview)
2. [Authentication Methods](#authentication-methods)
3. [JWT Authentication](#jwt-authentication)
4. [Signature Verification](#signature-verification)
5. [User Roles](#user-roles)
6. [Permission Matrix](#permission-matrix)
7. [Security Best Practices](#security-best-practices)

---

## Overview

The system implements two authentication methods:

1. **JWT Authentication**: For booth management, user management, and admin operations
2. **Signature Verification**: For NFC client operations (balance query, payment, recharge)

Authorization is enforced through **Role-Based Access Control (RBAC)** with five distinct user roles.

---

## Authentication Methods

### Method Comparison

| Feature | JWT Authentication | Signature Verification |
|---------|-------------------|------------------------|
| **Use Case** | Booth management, admin operations | NFC client operations |
| **Token Type** | JWT (JSON Web Token) | SHA256 signature |
| **Expiration** | Configurable (default: 24 hours) | 60 seconds (timestamp window) |
| **Stateless** | Yes | Yes |
| **User Context** | Full user info (id, role, booth_id) | UID only |
| **Header** | `Authorization: Bearer <token>` | Request body fields |

---

## JWT Authentication

### How It Works

1. **Login**: User provides username and password
2. **Token Generation**: Server validates credentials and generates JWT token
3. **Token Usage**: Client includes token in Authorization header for subsequent requests
4. **Token Validation**: Server validates token signature and expiration on each request

### Login Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant AuthService
    participant Database
    
    Client->>API: POST /auth/login {username, password}
    API->>AuthService: login(username, password)
    AuthService->>Database: Query user by username
    Database-->>AuthService: User record
    AuthService->>AuthService: Verify password (bcrypt)
    AuthService->>AuthService: Generate JWT token
    AuthService-->>API: {access_token, user_info}
    API-->>Client: 200 OK {access_token, token_type, user}
```

### JWT Token Structure

**Header:**
```json
{
    "alg": "HS256",
    "typ": "JWT"
}
```

**Payload:**
```json
{
    "user_id": 1,
    "username": "admin",
    "role": "super_admin",
    "booth_id": null,
    "exp": 1707234567,
    "iat": 1707148167
}
```

**Signature:**
```
HMACSHA256(
    base64UrlEncode(header) + "." + base64UrlEncode(payload),
    JWT_SECRET_KEY
)
```

### Using JWT Tokens

**Request Example:**
```bash
curl -X GET http://localhost:8000/booths \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Token Validation Process:**
1. Extract token from Authorization header
2. Decode token and verify signature
3. Check token expiration
4. Extract user_id from payload
5. Query user from database
6. Verify user status (active, not blocked)
7. Return user object to route handler

### Token Expiration

- **Default**: 1440 minutes (24 hours)
- **Configurable**: Set `JWT_EXPIRATION_MINUTES` in environment
- **Handling**: Client must login again when token expires

**Error Response (Token Expired):**
```json
{
    "error_code": "TOKEN_EXPIRED",
    "message": "JWT token has expired"
}
```

---

## Signature Verification

### How It Works

1. **Request Preparation**: Client calculates SHA256 signature
2. **Request Submission**: Client sends request with timestamp and signature
3. **Timestamp Validation**: Server checks timestamp is within 60-second window
4. **Signature Verification**: Server recalculates signature and compares

### Signature Calculation

**For Balance Query:**
```
SHA256(uid + timestamp + secret_key)
```

**For Payment/Recharge:**
```
SHA256(uid + amount + timestamp + secret_key)
```

**Example (Python):**
```python
import hashlib
import time

uid = "A1B2C3D4"
amount = 25.00
timestamp = int(time.time())
secret_key = "your-secret-key"

# Calculate signature
message = f"{uid}{amount}{timestamp}{secret_key}"
signature = hashlib.sha256(message.encode('utf-8')).hexdigest()

# Send request
request_data = {
    "uid": uid,
    "amount": amount,
    "timestamp": timestamp,
    "signature": signature
}
```

### Timestamp Validation

- **Window**: 60 seconds (configurable via `TIMESTAMP_WINDOW`)
- **Purpose**: Prevent replay attacks
- **Validation**: `|server_time - request_timestamp| <= 60`

**Error Response (Timestamp Expired):**
```json
{
    "error_code": "TIMESTAMP_EXPIRED",
    "message": "Request timestamp expired. Time difference: 120 seconds"
}
```

---

## User Roles

The system defines five user roles with distinct permissions:

### 1. Super Admin (`super_admin`)

**Description**: System administrator with full access

**Capabilities**:
- Create and manage users
- Manage all booths, products, and transactions
- View all data across events
- Access all system functions

**Restrictions**: None

**Use Case**: System administrators, IT staff

---

### 2. Event Admin (`event_admin`)

**Description**: Event organizer with management permissions

**Capabilities**:
- Create and manage booths
- Create and manage products
- View event-wide statistics
- View all transactions for events
- Process payments for any booth

**Restrictions**:
- Cannot create or manage users
- Cannot access super admin functions

**Use Case**: Event organizers, activity coordinators

---

### 3. Booth Cashier (`booth_cashier`)

**Description**: Booth operator with limited permissions

**Capabilities**:
- Process payments for assigned booth only
- View products for assigned booth
- View transactions for assigned booth

**Restrictions**:
- Cannot manage booths or products
- Cannot access other booths
- Cannot process recharges
- Must be assigned to a specific booth

**Use Case**: Student cashiers, booth operators

---

### 4. Issuer (`issuer`)

**Description**: Recharge operator with limited permissions

**Capabilities**:
- Process recharge transactions
- View transaction history (for auditing)

**Restrictions**:
- Cannot process payments
- Cannot manage booths or products
- Cannot create users

**Use Case**: Recharge stations, fund issuers

---

### 5. Reviewer (`reviewer`)

**Description**: Reserved for future use

**Capabilities**: Currently limited

**Restrictions**: Most operations restricted

**Use Case**: Future refund approval, transaction review

---

## Permission Matrix

### Booth Management

| Operation | super_admin | event_admin | booth_cashier | issuer | reviewer |
|-----------|-------------|-------------|---------------|--------|----------|
| Create Booth | ✓ | ✓ | ✗ | ✗ | ✗ |
| View All Booths | ✓ | ✓ | ✗ | ✗ | ✗ |
| View Own Booth | ✓ | ✓ | ✓ | ✗ | ✗ |
| Update Booth | ✓ | ✓ | ✗ | ✗ | ✗ |

### Product Management

| Operation | super_admin | event_admin | booth_cashier | issuer | reviewer |
|-----------|-------------|-------------|---------------|--------|----------|
| Create Product | ✓ | ✓ | ✗ | ✗ | ✗ |
| Update Product | ✓ | ✓ | ✗ | ✗ | ✗ |
| View All Products | ✓ | ✓ | ✗ | ✗ | ✗ |
| View Own Booth Products | ✓ | ✓ | ✓ | ✗ | ✗ |

### Transaction Operations

| Operation | super_admin | event_admin | booth_cashier | issuer | reviewer |
|-----------|-------------|-------------|---------------|--------|----------|
| Process Payment (Any Booth) | ✓ | ✓ | ✗ | ✗ | ✗ |
| Process Payment (Own Booth) | ✓ | ✓ | ✓ | ✗ | ✗ |
| Process Recharge | ✓ | ✓ | ✗ | ✓ | ✗ |
| View All Transactions | ✓ | ✓ | ✗ | ✓ | ✗ |
| View Own Booth Transactions | ✓ | ✓ | ✓ | ✗ | ✗ |

### User Management

| Operation | super_admin | event_admin | booth_cashier | issuer | reviewer |
|-----------|-------------|-------------|---------------|--------|----------|
| Create User | ✓ | ✗ | ✗ | ✗ | ✗ |
| View Users | ✓ | ✗ | ✗ | ✗ | ✗ |
| Update User Status | ✓ | ✗ | ✗ | ✗ | ✗ |
| Delete User | ✓ | ✗ | ✗ | ✗ | ✗ |

---

## Security Best Practices

### 1. JWT Token Security

**DO:**
- ✓ Use strong JWT_SECRET_KEY (minimum 32 characters)
- ✓ Store tokens securely (encrypted storage, secure cookies)
- ✓ Set appropriate expiration time (balance security and UX)
- ✓ Validate token on every request
- ✓ Use HTTPS in production

**DON'T:**
- ✗ Store tokens in localStorage (XSS vulnerable)
- ✗ Share tokens between users
- ✗ Use weak or default secret keys
- ✗ Extend token expiration indefinitely
- ✗ Transmit tokens over HTTP

### 2. Password Security

**DO:**
- ✓ Use bcrypt with cost factor 12 or higher
- ✓ Enforce strong password policies
- ✓ Hash passwords before storage
- ✓ Use constant-time comparison
- ✓ Implement rate limiting on login

**DON'T:**
- ✗ Store plaintext passwords
- ✗ Use weak hashing algorithms (MD5, SHA1)
- ✗ Allow weak passwords
- ✗ Log passwords
- ✗ Transmit passwords in URLs

### 3. Signature Verification Security

**DO:**
- ✓ Use strong SECRET_KEY
- ✓ Validate timestamp window
- ✓ Use constant-time comparison
- ✓ Rotate secret keys periodically
- ✓ Log signature failures

**DON'T:**
- ✗ Share secret keys publicly
- ✗ Use predictable secret keys
- ✗ Skip timestamp validation
- ✗ Allow large timestamp windows
- ✗ Expose secret keys in client code

### 4. Role-Based Access Control

**DO:**
- ✓ Validate user role on every request
- ✓ Enforce least privilege principle
- ✓ Log permission violations
- ✓ Review role assignments regularly
- ✓ Implement booth ownership validation

**DON'T:**
- ✗ Trust client-side role checks
- ✗ Grant excessive permissions
- ✗ Skip permission validation
- ✗ Allow role escalation
- ✗ Ignore audit logs

### 5. General Security

**DO:**
- ✓ Use HTTPS in production
- ✓ Implement rate limiting
- ✓ Log all authentication attempts
- ✓ Monitor for suspicious activity
- ✓ Keep dependencies updated

**DON'T:**
- ✗ Expose sensitive data in errors
- ✗ Allow unlimited login attempts
- ✗ Ignore security warnings
- ✗ Use default configurations
- ✗ Skip security testing

---

## Implementation Examples

### Example 1: Implementing JWT Authentication in Client

```python
import requests

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
    
    def login(self, username, password):
        """Login and store JWT token"""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        
        data = response.json()
        self.token = data['access_token']
        return data['user']
    
    def get_headers(self):
        """Get headers with JWT token"""
        if not self.token:
            raise Exception("Not authenticated. Call login() first.")
        return {"Authorization": f"Bearer {self.token}"}
    
    def get_booths(self, event_id=None):
        """Get booths with authentication"""
        params = {"event_id": event_id} if event_id else {}
        response = requests.get(
            f"{self.base_url}/booths",
            headers=self.get_headers(),
            params=params
        )
        response.raise_for_status()
        return response.json()

# Usage
client = APIClient("http://localhost:8000")
user = client.login("admin", "password123")
booths = client.get_booths(event_id=1)
```

### Example 2: Implementing Signature Verification in Client

```python
import hashlib
import time
import requests

class NFCClient:
    def __init__(self, base_url, secret_key):
        self.base_url = base_url
        self.secret_key = secret_key
    
    def calculate_signature(self, uid, amount, timestamp):
        """Calculate SHA256 signature"""
        message = f"{uid}{amount}{timestamp}{self.secret_key}"
        return hashlib.sha256(message.encode('utf-8')).hexdigest()
    
    def process_payment(self, uid, amount, merchant_id=None, remark=None):
        """Process payment with signature verification"""
        timestamp = int(time.time())
        signature = self.calculate_signature(uid, amount, timestamp)
        
        data = {
            "uid": uid,
            "amount": amount,
            "timestamp": timestamp,
            "signature": signature
        }
        
        if merchant_id:
            data["merchant_id"] = merchant_id
        if remark:
            data["remark"] = remark
        
        response = requests.post(
            f"{self.base_url}/pay",
            json=data
        )
        response.raise_for_status()
        return response.json()

# Usage
client = NFCClient("http://localhost:8000", "your-secret-key")
result = client.process_payment("A1B2C3D4", 25.00, remark="购买商品")
```

### Example 3: Role-Based Route Protection

```python
from fastapi import APIRouter, Depends, HTTPException
from core.security import get_current_user, RoleChecker
from models.user import User

router = APIRouter()

@router.get("/booths")
async def list_booths(
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"]))
):
    """
    List booths - requires super_admin or event_admin role
    """
    # Permission already validated by RoleChecker
    # Implement booth listing logic
    pass

@router.post("/booths/{booth_id}/pay")
async def process_booth_payment(
    booth_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Process booth payment - custom permission logic
    """
    # Custom permission validation
    if current_user.role == 'booth_cashier':
        if current_user.booth_id != booth_id:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. You can only process payments for booth {current_user.booth_id}"
            )
    elif current_user.role not in ('super_admin', 'event_admin'):
        raise HTTPException(
            status_code=403,
            detail=f"Role '{current_user.role}' cannot process payments"
        )
    
    # Process payment logic
    pass
```

---

## Troubleshooting

### Issue: JWT Token Validation Fails

**Symptoms**:
- 401 Unauthorized error
- "Invalid JWT token" message

**Possible Causes**:
1. JWT_SECRET_KEY mismatch
2. Token expired
3. Token tampered with
4. System time mismatch

**Solutions**:
1. Verify JWT_SECRET_KEY matches between environments
2. Login again to get new token
3. Check token hasn't been modified
4. Synchronize system time (NTP)

---

### Issue: Booth Cashier Cannot Access Booth

**Symptoms**:
- 403 Forbidden error
- "Access denied" message

**Possible Causes**:
1. User not assigned to booth
2. Accessing wrong booth
3. User status not active

**Solutions**:
1. Verify user.booth_id matches requested booth
2. Check booth_id in request
3. Verify user status is 'active'

---

### Issue: Signature Verification Fails

**Symptoms**:
- 401 Unauthorized error
- "Signature verification failed" message

**Possible Causes**:
1. SECRET_KEY mismatch
2. Timestamp expired
3. Incorrect signature calculation
4. System time mismatch

**Solutions**:
1. Verify SECRET_KEY matches between client and server
2. Check timestamp is within 60 seconds
3. Verify signature calculation formula
4. Synchronize system time

---

For more information, see:
- API Documentation: `docs/API_DOCUMENTATION.md`
- Error Codes: `docs/ERROR_CODES.md`
- Usage Examples: `docs/API_USAGE_EXAMPLES.md`
