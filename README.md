# NFC Campus Event System - Backend

Backend API service for the NFC Campus Event System with complete event management, booth operations, and NFC payment support.

## 🎯 Overview

This system provides a complete NFC-based campus event management solution with support for:
- **Event Management**: Create and manage campus events with full lifecycle support (create → operate → close)
- **Booth Management**: Multi-booth operations for campus events (food stalls, game booths, etc.)
- **Product Management**: Track products sold at each booth with pricing and inventory
- **User Roles & Permissions**: Role-based access control (RBAC) for different user types
- **JWT Authentication**: Secure token-based authentication for all operations
- **Transaction Tracking**: Comprehensive transaction history with booth and product associations
- **Cash Reconciliation**: Track and reconcile cash transactions for each booth
- **Data Export**: Export reports in Excel format (class settlements, transactions, leaderboards)
- **Event Closure**: Automated quota expiration and final settlement

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 3. Initialize Database

```bash
# Run database migration
python scripts/migrate_cash_reconciliation.py
```

### 4. Create Admin User

```bash
# Interactive admin creation
python scripts/create_admin.py
```

### 5. Start Server

```bash
# Development mode
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Setup Demo Data (Optional)

```bash
# Automatically create demo event, booths, products, and participants
python scripts/demo_setup.py
```

### 7. Access API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📚 Documentation

### Quick Links
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[Demo Flow](DEMO_FLOW.md)** - Step-by-step demonstration guide
- **[Final Summary](FINAL_UPGRADE_SUMMARY.md)** - Complete feature list and architecture
- **[API Documentation](docs/API_DOCUMENTATION.md)** - Detailed API reference
- **[Authentication Guide](docs/AUTHENTICATION_AUTHORIZATION.md)** - Security and permissions

### Android Client
- **[Android README](android/README.md)** - Android app setup and usage
- **[Quick Start](android/QUICK_START.md)** - Android quick start guide

## ✨ Key Features

### Event Management
- ✅ Create and manage events
- ✅ Event lifecycle management (draft → active → paused → ended)
- ✅ Automatic quota expiration on event closure
- ✅ Event-specific participant accounts

### Booth & Product Management
- ✅ Multi-booth support per event
- ✅ Product catalog with pricing and inventory
- ✅ Booth-specific cashier accounts
- ✅ Real-time sales tracking

### Transaction Processing
- ✅ NFC card-based payments
- ✅ Quota issuance and recharge
- ✅ Refund and adjustment support
- ✅ Concurrent transaction safety
- ✅ Complete audit trail

### Cash Reconciliation
- ✅ Booth cash reconciliation records
- ✅ Expected vs actual cash tracking
- ✅ Discrepancy reason documentation
- ✅ Reviewer assignment

### Reports & Export
- ✅ Class settlement reports
- ✅ Transaction history export
- ✅ Refund/adjustment reports
- ✅ Booth leaderboards
- ✅ Excel format export

### Security
- ✅ JWT authentication
- ✅ Role-based access control
- ✅ Password encryption (bcrypt)
- ✅ Concurrent transaction control
- ✅ Audit logging

## 🏗️ System Architecture

```
Backend (FastAPI)
├── Core Layer
│   ├── Configuration
│   ├── Database
│   ├── Security (JWT)
│   └── Exceptions
├── Model Layer (SQLAlchemy)
│   ├── Users
│   ├── Events
│   ├── Participants
│   ├── Accounts
│   ├── Booths
│   ├── Products
│   ├── Transactions
│   └── Cash Reconciliations
├── Service Layer
│   ├── Auth Service
│   ├── Event Service
│   ├── Booth Service
│   ├── Transaction Service
│   ├── Ledger Service
│   ├── Report Service
│   └── Export Service
└── API Layer (Routes)
    ├── Authentication
    ├── Event Management
    ├── Booth Management
    ├── Transaction Processing
    ├── Cash Reconciliation
    ├── Reports
    └── Data Export

Android Client (Java)
├── NFC Reader
├── Cashier Terminal
├── Product Management
└── Transaction History
```

## 👥 User Roles

| Role | Permissions |
|------|-------------|
| **super_admin** | Full system access, user management, all operations |
| **event_admin** | Event management, booth/product management, reports |
| **booth_cashier** | Process payments for assigned booth only |
| **issuer** | Issue quotas, bind cards, view transactions |

## 🔌 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login (returns JWT)

### Event Management
- `POST /events` - Create event
- `GET /events` - List events
- `GET /events/{id}` - Get event details
- `PATCH /events/{id}` - Update event
- `POST /events/{id}/close` - Close event (with quota expiration)

### Booth Management
- `POST /booths` - Create booth
- `GET /booths` - List booths
- `GET /booths/{id}` - Get booth details
- `PATCH /booths/{id}` - Update booth

### Product Management
- `POST /products` - Create product
- `GET /products` - List products
- `PATCH /products/{id}` - Update product

### Transaction Processing
- `GET /balance` - Query balance
- `POST /payment` - Process payment
- `POST /recharge` - Issue/recharge quota
- `POST /refund` - Process refund
- `GET /transactions` - Query transactions

### Cash Reconciliation
- `POST /cash-reconciliation` - Create reconciliation
- `GET /cash-reconciliation` - List reconciliations

### Reports & Export
- `GET /reports/summary` - Summary statistics
- `GET /reports/booths` - Booth report
- `GET /reports/products` - Product report
- `GET /export/class-settlement` - Export class settlement (Excel)
- `GET /export/transactions` - Export transactions (Excel)
- `GET /export/refund-adjustments` - Export refunds (Excel)
- `GET /export/leaderboard` - Export leaderboard (Excel)

## 🛠️ Development

### Project Structure

```
.
├── app/                    # Main application
├── core/                   # Core utilities
├── models/                 # Database models
├── services/              # Business logic
├── routes/                # API endpoints
├── schemas/               # Pydantic schemas
├── middleware/            # Custom middleware
├── scripts/               # Utility scripts
├── docs/                  # Documentation
├── android/               # Android client
└── tests/                 # Test suite
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov=models --cov=services --cov=routes --cov=core

# Run specific tests
pytest tests/test_auth.py
```

### Database Migrations

```bash
# Run migration
python scripts/migrate_cash_reconciliation.py
```

## 🚢 Deployment

### Production Checklist

- [ ] Configure strong JWT_SECRET_KEY (32+ characters)
- [ ] Set up MySQL database
- [ ] Configure .env file
- [ ] Run database migrations
- [ ] Create admin user
- [ ] Enable HTTPS
- [ ] Set up database backups
- [ ] Configure logging
- [ ] Set up monitoring

### Production Run

```bash
# Using uvicorn with multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Using gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

See **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** for complete deployment instructions.

## 📱 Android Client

The Android client provides a cashier terminal interface with NFC card reading capabilities.

### Features
- NFC card reading (ISO 14443A)
- Product selection and cart management
- Real-time payment processing
- Transaction history
- Offline mode support (coming soon)

### Setup

```bash
cd android
cp local.properties.example local.properties
# Edit local.properties with backend URL
./gradlew assembleDebug
```

See **[android/README.md](android/README.md)** for detailed setup instructions.

## 🎬 Demo Flow

Complete demonstration flow with sample data:

1. Create event
2. Create booths (3 class booths)
3. Create products (6 products)
4. Create participants (3 students)
5. Bind NFC cards
6. Issue quotas (100 yuan each)
7. Process payments
8. Query balances
9. Process refund
10. Cash reconciliation
11. View reports
12. Export data
13. Close event
14. Verify quota expiration

See **[DEMO_FLOW.md](DEMO_FLOW.md)** for complete step-by-step guide.

## 🔧 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check MySQL service
systemctl status mysql

# Verify credentials in .env
DB_HOST=localhost
DB_USER=your_user
DB_PASSWORD=your_password
```

**JWT Token Invalid**
```bash
# Regenerate secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Update JWT_SECRET_KEY in .env
```

**Android Cannot Connect**
```bash
# Check backend URL in local.properties
backend.url=http://YOUR_SERVER_IP:8000

# Verify firewall allows port 8000
sudo ufw allow 8000
```

## 📊 System Status

**Version**: v2.0.0 - Final Release  
**Status**: ✅ Production Ready  
**Last Updated**: 2024-05-02

### Completed Features
- ✅ Complete event lifecycle management
- ✅ Multi-booth operations
- ✅ NFC payment processing
- ✅ Cash reconciliation
- ✅ Data export (Excel)
- ✅ Android cashier terminal
- ✅ Role-based access control
- ✅ Complete documentation

## 📄 License

Internal project for campus use.

## 🤝 Support

For issues, questions, or contributions:
- **GitHub Issues**: https://github.com/your-repo/issues
- **Email**: support@example.com
- **Documentation**: See docs/ folder

---

**Made with ❤️ for campus events**

## Project Structure

```
.
├── app/                    # Main application package
│   ├── __init__.py
│   ├── main.py            # Application entry point
│   ├── config.py          # Configuration management
│   └── database.py        # Database connection
├── core/                   # Core utilities
│   ├── config.py          # Core configuration
│   ├── database.py        # Database session management
│   ├── security.py        # JWT auth, password hashing, permissions
│   └── exceptions.py      # Custom exception classes
├── models/                 # SQLAlchemy ORM models
│   ├── user.py            # User model (with roles)
│   ├── booth.py           # Booth model
│   ├── product.py         # Product model
│   ├── event.py           # Event model
│   ├── participant.py     # Participant model
│   ├── account.py         # Account model
│   └── transaction.py     # Transaction model (enhanced)
├── services/              # Business logic services
│   ├── auth_service.py    # Authentication service
│   ├── user_service.py    # User management service
│   ├── booth_service.py   # Booth management service
│   ├── product_service.py # Product management service
│   ├── transaction_service.py  # Transaction processing
│   └── ...
├── routes/                # API route handlers
│   ├── auth.py            # Authentication endpoints
│   ├── users.py           # User management endpoints
│   ├── booths.py          # Booth management endpoints
│   ├── products.py        # Product management endpoints
│   ├── transactions.py    # Transaction query endpoints
│   ├── payment.py         # Payment processing endpoint
│   └── ...
├── schemas/               # Pydantic schemas for validation
│   ├── user.py            # User schemas
│   ├── booth.py           # Booth schemas
│   ├── product.py         # Product schemas
│   └── ...
├── middleware/            # Custom middleware
│   ├── signature_verification.py  # Signature verification
│   └── request_logging.py         # Request logging
├── migrations/            # Database migration scripts
│   ├── 001_upgrade_to_ledger_mode.sql
│   ├── 002_upgrade_to_event_system.sql
│   └── 003_booth_management_system.sql
├── requirements.txt       # Python dependencies
├── .env.example          # Environment configuration template
└── docs/                 # Documentation
    └── API_DOCUMENTATION.md  # Detailed API documentation
```

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` and set the required values:
```env
# Database Configuration
DATABASE_PATH=./nfc_wallet.db

# Security Configuration
SECRET_KEY=your-secret-key-for-signature-verification
JWT_SECRET_KEY=your-jwt-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

### 3. Set Up Database

Run the migration scripts to create the database schema:

```bash
# Run all migrations
python run_all_migrations.py

# Or run migrations individually
python run_migration.py migrations/001_upgrade_to_ledger_mode.sql
python run_migration.py migrations/002_upgrade_to_event_system.sql
python run_migration.py migrations/003_booth_management_system.sql
```

### 4. Create Initial Admin User

```bash
# Create a super admin user
python create_admin_user.py
```

### 5. Run the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 6. View API Documentation

FastAPI provides automatic interactive API documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Detailed API Guide**: See `docs/API_DOCUMENTATION.md`

## Configuration

All configuration is managed through environment variables. See `.env.example` for available options.

### Required Configuration

```env
# Database
DATABASE_PATH=./nfc_wallet.db

# Security - Signature Verification
SECRET_KEY=your-secret-key-for-signature-verification

# Security - JWT Authentication
JWT_SECRET_KEY=your-jwt-secret-key-minimum-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
```

### Optional Configuration

```env
# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Transaction Limits
TIMESTAMP_WINDOW=60
MAX_TRANSACTION_AMOUNT=10000.00

# Logging
LOG_LEVEL=INFO
```

### Security Best Practices

1. **JWT Secret Key**: Must be at least 32 characters long. Generate a secure random key:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Signature Secret Key**: Used for NFC client signature verification. Keep this secret and share only with authorized clients.

3. **Never commit** `.env` file to version control. Use `.env.example` as a template.

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov=models --cov=services --cov=routes --cov=core

# Run specific test files
pytest tests/test_auth.py
pytest tests/test_booths.py
pytest tests/test_products.py

# Run with verbose output
pytest -v
```

## Error Handling

All API endpoints return consistent error responses:

```json
{
    "error_code": "ERROR_CODE",
    "message": "Human-readable error message"
}
```

### Common Error Codes

**Authentication Errors (401)**
- `AUTH_ERROR`: General authentication error
- `INVALID_CREDENTIALS`: Invalid username or password
- `TOKEN_EXPIRED`: JWT token has expired
- `TOKEN_INVALID`: JWT token is invalid
- `AUTHENTICATION_REQUIRED`: JWT authentication required for this operation

**Authorization Errors (403)**
- `PERMISSION_DENIED`: Insufficient permissions
- `BOOTH_ACCESS_DENIED`: Cannot access this booth
- `ROLE_NOT_ALLOWED`: Role not allowed for this operation

**Validation Errors (400)**
- `VALIDATION_ERROR`: General validation error
- `INVALID_BOOTH_ID`: Invalid booth ID
- `INVALID_PRODUCT_ID`: Invalid product ID
- `PRODUCT_NOT_IN_BOOTH`: Product does not belong to booth
- `INSUFFICIENT_FUNDS`: Insufficient balance
- `MISSING_FILTER`: Required filter parameter missing

**Resource Not Found (404)**
- `BOOTH_NOT_FOUND`: Booth not found
- `PRODUCT_NOT_FOUND`: Product not found
- `USER_NOT_FOUND`: User not found
- `EVENT_NOT_FOUND`: Event not found

See `docs/API_DOCUMENTATION.md` for complete error code reference.

## User Roles & Permissions

The system implements role-based access control (RBAC) with five user roles:

### 1. Super Admin (`super_admin`)
- Full system access
- Create and manage users
- Manage all booths, products, and transactions
- View all data across events

### 2. Event Admin (`event_admin`)
- Manage booths and products for events
- View event-wide statistics and transactions
- Cannot create users or access other admin functions

### 3. Booth Cashier (`booth_cashier`)
- Process payments for their assigned booth only
- View products and transactions for their booth
- Cannot manage booths or products
- Must be assigned to a specific booth

### 4. Issuer (`issuer`)
- Process recharge transactions only
- Cannot process payments
- View transaction history for auditing

### 5. Reviewer (`reviewer`)
- Reserved for future use (refund approval, etc.)
- Currently has limited permissions

## API Endpoints Overview

### Authentication
- `POST /auth/login` - User login (returns JWT token)
- `GET /auth/me` - Get current user info

### User Management (Super Admin only)
- `POST /users` - Create new user
- `GET /users` - List users
- `GET /users/{id}` - Get user details
- `PATCH /users/{id}/status` - Update user status

### Booth Management
- `POST /booths` - Create booth (Event Admin, Super Admin)
- `GET /booths` - List booths (Event Admin, Super Admin)
- `GET /booths/{id}` - Get booth details (Event Admin, Super Admin, Booth Cashier for own booth)
- `POST /booths/{id}/pay` - Process booth payment (Booth Cashier for own booth, Admins)
- `GET /booths/{id}/transactions` - Get booth transactions

### Product Management
- `POST /products` - Create product (Event Admin, Super Admin)
- `GET /products` - List products (Event Admin, Super Admin, Booth Cashier for own booth)
- `PATCH /products/{id}` - Update product (Event Admin, Super Admin)

### Transaction Management
- `GET /transactions` - Query transactions with filters (role-based access)
- `POST /pay` - Process payment (supports booth mode, event mode, legacy mode)
- `POST /recharge` - Process recharge (Issuer, Admins)

### Event & Participant Management
- `POST /events` - Create event
- `GET /events` - List events
- `POST /participants` - Register participant
- `GET /balance` - Query participant balance

See `docs/API_DOCUMENTATION.md` for detailed endpoint documentation with request/response examples.

## Development

### Project Architecture

The project follows a layered architecture:

1. **Routes Layer** (`routes/`): API endpoint handlers, request validation
2. **Service Layer** (`services/`): Business logic, transaction management
3. **Model Layer** (`models/`): Database models and relationships
4. **Core Layer** (`core/`): Security, configuration, exceptions

### Adding New Features

#### 1. Adding New Routes

```python
# routes/my_feature.py
from fastapi import APIRouter, Depends
from core.security import get_current_user, RoleChecker

router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint(
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin"]))
):
    return {"message": "Hello"}
```

Then register in `app/main.py`:
```python
from routes import my_feature
app.include_router(my_feature.router, tags=["My Feature"])
```

#### 2. Adding New Services

```python
# services/my_service.py
from sqlalchemy.orm import Session
from models.my_model import MyModel

class MyService:
    def __init__(self, db: Session):
        self.db = db
    
    def do_something(self, param: str):
        # Business logic here
        pass
```

#### 3. Adding New Models

```python
# models/my_model.py
from sqlalchemy import Column, Integer, String
from core.database import Base

class MyModel(Base):
    __tablename__ = 'my_table'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
```

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions focused and single-purpose
- Use meaningful variable and function names

### Database Migrations

When modifying the database schema:

1. Create a new migration file in `migrations/`
2. Name it with incrementing number: `004_my_feature.sql`
3. Make migrations idempotent (safe to run multiple times)
4. Test migrations on a copy of production data
5. Document the migration in comments

## Validation Utilities

The `utils/validators.py` module provides centralized validation functions that can be reused across endpoints:

### Available Validators

#### `validate_amount(amount: float)`
Validates that an amount is positive and within the maximum transaction limit.

```python
from utils.validators import validate_amount

try:
    validate_amount(50.00)  # Valid
    validate_amount(0)      # Raises ValueError: "Amount must be positive"
    validate_amount(99999)  # Raises ValueError: "Amount exceeds maximum..."
except ValueError as e:
    print(f"Validation error: {e}")
```

#### `validate_uid_format(uid: str)`
Validates that a UID matches the expected hexadecimal format.

```python
from utils.validators import validate_uid_format

try:
    validate_uid_format("A1B2C3D4")  # Valid
    validate_uid_format("")          # Raises ValueError: "UID cannot be empty"
    validate_uid_format("XYZ123")    # Raises ValueError: "UID must be hexadecimal"
except ValueError as e:
    print(f"Validation error: {e}")
```

#### `validate_required_fields(request: Dict, required_fields: List[str])`
Validates that all required parameters are present in a request.

```python
from utils.validators import validate_required_fields

request = {"uid": "A1B2C3D4", "amount": 50.0}
required = ["uid", "amount", "timestamp"]

try:
    validate_required_fields(request, required)
    # Raises ValueError: "Missing required field: timestamp"
except ValueError as e:
    print(f"Validation error: {e}")
```

### Usage in Routes

These validators can be used alongside Pydantic validation for additional checks:

```python
from utils.validators import validate_amount, validate_uid_format

@router.post("/pay")
async def process_payment(request: PaymentRequest):
    # Additional validation beyond Pydantic
    validate_amount(request.amount)
    validate_uid_format(request.uid)
    # Process payment...
```

## Security

### Authentication Methods

The system supports two authentication methods:

1. **JWT Authentication** (Booth Management System)
   - Used for booth management, user management, and admin operations
   - Token-based authentication with configurable expiration
   - Include token in `Authorization: Bearer <token>` header

2. **Signature Verification** (NFC Client Operations)
   - Used for NFC client operations (balance query, payment, recharge)
   - SHA256 signature: `SHA256(uid + amount + timestamp + secret_key)`
   - Timestamp must be within 60 seconds of server time (configurable)
   - Prevents replay attacks and ensures request integrity

### Password Security

- Passwords are hashed using **bcrypt** with cost factor 12
- Plaintext passwords are never stored in the database
- Constant-time comparison prevents timing attacks

### Permission Model

- **Role-Based Access Control (RBAC)**: Each user has a specific role with defined permissions
- **Booth Ownership**: Booth cashiers can only access their assigned booth
- **Token Validation**: All JWT tokens are validated for signature and expiration
- **Audit Trail**: All operations are logged with user identification

### Best Practices

1. Use HTTPS in production to encrypt all API traffic
2. Rotate JWT secret keys periodically
3. Set appropriate token expiration times (default: 24 hours)
4. Monitor failed authentication attempts
5. Keep signature secret keys secure and never expose them in client code

## License

Internal project for campus use.


## Deployment

### Production Checklist

- [ ] Set strong JWT_SECRET_KEY (minimum 32 characters)
- [ ] Set strong SECRET_KEY for signature verification
- [ ] Configure appropriate JWT_EXPIRATION_MINUTES
- [ ] Enable HTTPS/TLS for all API traffic
- [ ] Set up database backups
- [ ] Configure logging to file or external service
- [ ] Set LOG_LEVEL to WARNING or ERROR
- [ ] Review and adjust MAX_TRANSACTION_AMOUNT
- [ ] Set up monitoring and alerting
- [ ] Document admin credentials securely

### Running in Production

```bash
# Using uvicorn with multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Using gunicorn with uvicorn workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Common Issues

**Issue**: JWT token validation fails
- **Solution**: Check JWT_SECRET_KEY matches between token creation and validation
- **Solution**: Verify token hasn't expired (check JWT_EXPIRATION_MINUTES)

**Issue**: Booth cashier cannot access their booth
- **Solution**: Verify user.booth_id matches the booth they're trying to access
- **Solution**: Check user status is 'active', not 'blocked' or 'inactive'

**Issue**: Signature verification fails
- **Solution**: Ensure SECRET_KEY matches between client and server
- **Solution**: Check timestamp is within TIMESTAMP_WINDOW (default 60 seconds)
- **Solution**: Verify signature calculation matches: SHA256(uid + amount + timestamp + secret_key)

**Issue**: Database migration fails
- **Solution**: Check if migration was already applied
- **Solution**: Verify database file permissions
- **Solution**: Review migration SQL for syntax errors

## Documentation

### API Documentation
- **[API Documentation](docs/API_DOCUMENTATION.md)**: Complete API reference with all endpoints, request/response formats
- **[API Usage Examples](docs/API_USAGE_EXAMPLES.md)**: Practical examples and complete workflow demonstrations
- **[Error Codes Reference](docs/ERROR_CODES.md)**: Comprehensive error code documentation with resolutions
- **[Authentication & Authorization Guide](docs/AUTHENTICATION_AUTHORIZATION.md)**: Security, roles, and permissions explained

### System Documentation
- **[Booth Management System](MIGRATION_003_SUMMARY.md)**: Booth system upgrade and features
- **[Event System](EVENT_SYSTEM_UPGRADE_SUMMARY.md)**: Event mode documentation
- **[Ledger Mode](LEDGER_MODE_UPGRADE.md)**: Ledger system documentation
- **[Quick Reference](LEDGER_MODE_QUICK_REFERENCE.md)**: Quick reference guide

## Support

For issues, questions, or contributions, please contact the development team.
