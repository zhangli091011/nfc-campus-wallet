# Requirements Document

## Introduction

本文档定义了"摊位经营系统"（Booth Management System）的功能需求。该系统将现有的 NFC 校园钱包项目从"活动额度系统"升级为支持多摊位经营的完整商业管理系统。系统引入摊位（booths）、商品（products）、用户角色（users with roles）和基于角色的权限控制（RBAC），使活动组织者能够管理多个摊位，每个摊位可以独立经营、销售商品并追踪收入。

## Glossary

- **System**: 摊位经营系统（Booth Management System）
- **Booth**: 摊位，代表活动中的一个经营单位，由班级或团队运营
- **Product**: 商品，摊位销售的物品或服务
- **User**: 系统用户，具有特定角色和权限
- **Booth_Cashier**: 摊位收银员，负责特定摊位的收银操作
- **Event_Admin**: 活动管理员，负责配置摊位和商品
- **Issuer**: 发放员，负责充值和额度发放
- **Reviewer**: 审核员，负责审核退款等操作（本阶段暂不实现）
- **Super_Admin**: 超级管理员，拥有所有权限
- **JWT**: JSON Web Token，用于用户认证的令牌
- **RBAC**: 基于角色的访问控制（Role-Based Access Control）
- **Transaction**: 交易记录，包含摊位和商品信息
- **Event**: 活动，现有系统中的活动实体
- **Participant**: 参与者，现有系统中的参与者实体
- **Account**: 账户，现有系统中参与者在活动下的账户实体

## Requirements

### Requirement 1: 摊位数据管理

**User Story:** 作为活动管理员，我希望能够创建和管理摊位信息，以便为不同班级或团队分配经营单位。

#### Acceptance Criteria

1. THE System SHALL store booth records with id, event_id, name, class_name, status, and created_at fields
2. WHEN a booth is created, THE System SHALL assign a unique auto-incrementing id
3. THE System SHALL enforce that booth.event_id references a valid event in the events table
4. THE System SHALL support booth status values of 'active', 'inactive', and 'closed'
5. THE System SHALL create a database index on booth.event_id for query performance
6. THE System SHALL set booth.created_at to the current UTC timestamp when a booth is created

### Requirement 2: 商品数据管理

**User Story:** 作为活动管理员，我希望能够为每个摊位创建和管理商品信息，以便摊位可以销售不同的商品。

#### Acceptance Criteria

1. THE System SHALL store product records with id, booth_id, name, price, cost_price, stock, enabled, and created_at fields
2. WHEN a product is created, THE System SHALL assign a unique auto-incrementing id
3. THE System SHALL enforce that product.booth_id references a valid booth in the booths table
4. THE System SHALL store product.price and product.cost_price in cents (integer)
5. THE System SHALL support optional stock tracking where stock can be null (unlimited) or a non-negative integer
6. THE System SHALL support product.enabled as a boolean flag to enable or disable products
7. THE System SHALL create a database index on product.booth_id for query performance

### Requirement 3: 用户角色系统

**User Story:** 作为系统管理员，我希望能够创建具有不同角色的用户账户，以便实现基于角色的权限控制。

#### Acceptance Criteria

1. THE System SHALL store user records with id, username, password_hash, role, booth_id, status, and created_at fields
2. WHEN a user is created, THE System SHALL assign a unique auto-incrementing id
3. THE System SHALL enforce unique usernames across all users
4. THE System SHALL support role values of 'super_admin', 'event_admin', 'booth_cashier', 'reviewer', and 'issuer'
5. THE System SHALL support user status values of 'active', 'inactive', and 'blocked'
6. WHERE a user has role 'booth_cashier', THE System SHALL require a valid booth_id reference
7. WHERE a user has role other than 'booth_cashier', THE System SHALL allow booth_id to be null
8. THE System SHALL create database indexes on username, role, and booth_id fields
9. THE System SHALL hash passwords using a secure hashing algorithm before storage

### Requirement 4: JWT 认证系统

**User Story:** 作为系统用户，我希望能够使用用户名和密码登录系统，以便获得访问权限。

#### Acceptance Criteria

1. WHEN a user submits valid credentials to POST /auth/login, THE System SHALL return a JWT token
2. WHEN a user submits invalid credentials to POST /auth/login, THE System SHALL return a 401 Unauthorized error
3. THE System SHALL include user_id, username, and role in the JWT token payload
4. THE System SHALL sign JWT tokens with a secret key from configuration
5. THE System SHALL set JWT token expiration time based on configuration
6. WHEN a user sends a valid JWT token to GET /auth/me, THE System SHALL return the current user information
7. WHEN a user sends an invalid or expired JWT token, THE System SHALL return a 401 Unauthorized error

### Requirement 5: 摊位收银员权限控制

**User Story:** 作为摊位收银员，我希望只能访问和操作自己摊位的数据，以便保护其他摊位的信息安全。

#### Acceptance Criteria

1. WHEN a booth_cashier requests product list, THE System SHALL return only products belonging to their assigned booth
2. WHEN a booth_cashier attempts to create a payment transaction, THE System SHALL verify the booth_id matches their assigned booth
3. WHEN a booth_cashier attempts to access another booth's data, THE System SHALL return a 403 Forbidden error
4. WHEN a booth_cashier attempts to perform a recharge operation, THE System SHALL return a 403 Forbidden error
5. THE System SHALL extract user role and booth_id from the JWT token for permission validation

### Requirement 6: 发放员权限控制

**User Story:** 作为发放员，我希望能够为参与者充值额度，但不能进行消费扣款操作，以便职责分离。

#### Acceptance Criteria

1. WHEN an issuer performs a recharge operation, THE System SHALL allow the transaction
2. WHEN an issuer attempts to perform a payment operation, THE System SHALL return a 403 Forbidden error
3. THE System SHALL record the issuer's user_id as operator_id in recharge transactions

### Requirement 7: 活动管理员权限控制

**User Story:** 作为活动管理员，我希望能够配置摊位和商品，并查看活动全局数据，以便管理整个活动。

#### Acceptance Criteria

1. WHEN an event_admin creates a booth, THE System SHALL allow the operation
2. WHEN an event_admin creates or updates a product, THE System SHALL allow the operation
3. WHEN an event_admin requests transaction history for any booth, THE System SHALL return the data
4. WHEN an event_admin requests activity-wide statistics, THE System SHALL return aggregated data across all booths

### Requirement 8: 摊位管理接口

**User Story:** 作为活动管理员，我希望通过 API 接口管理摊位，以便集成到管理后台。

#### Acceptance Criteria

1. WHEN an authorized user sends POST /booths with valid data, THE System SHALL create a new booth and return booth details
2. WHEN an authorized user sends GET /booths, THE System SHALL return a list of booths with optional filtering by event_id
3. WHEN an authorized user sends GET /booths/{id}, THE System SHALL return the booth details for the specified id
4. WHEN a user sends GET /booths/{id} for a non-existent booth, THE System SHALL return a 404 Not Found error
5. THE System SHALL validate that event_id exists before creating a booth
6. THE System SHALL require authentication for all booth management endpoints

### Requirement 9: 商品管理接口

**User Story:** 作为活动管理员，我希望通过 API 接口管理商品，以便为摊位配置销售商品。

#### Acceptance Criteria

1. WHEN an authorized user sends POST /products with valid data, THE System SHALL create a new product and return product details
2. WHEN an authorized user sends GET /products, THE System SHALL return a list of products with optional filtering by booth_id
3. WHEN an authorized user sends PATCH /products/{id} with valid data, THE System SHALL update the product and return updated details
4. WHEN a user sends PATCH /products/{id} for a non-existent product, THE System SHALL return a 404 Not Found error
5. THE System SHALL validate that booth_id exists before creating a product
6. THE System SHALL validate that price and cost_price are non-negative integers
7. WHERE stock is provided, THE System SHALL validate that stock is a non-negative integer
8. THE System SHALL require authentication for all product management endpoints

### Requirement 10: 支付交易改造

**User Story:** 作为摊位收银员，我希望在处理支付时能够关联摊位和商品信息，以便追踪销售数据。

#### Acceptance Criteria

1. WHEN a payment transaction is created, THE System SHALL require event_id, booth_id, and operator_id fields
2. WHEN a payment transaction is created, THE System SHALL accept an optional product_id field
3. WHEN a payment transaction includes product_id, THE System SHALL verify the product belongs to the specified booth
4. WHEN a payment transaction is created, THE System SHALL verify the booth belongs to the specified event
5. WHEN a payment transaction is created, THE System SHALL verify the operator has permission to operate the specified booth
6. THE System SHALL record booth_id, product_id, and operator_id in the transaction record
7. THE System SHALL maintain backward compatibility with existing payment transactions that lack booth information

### Requirement 11: 交易流水记录增强

**User Story:** 作为活动管理员，我希望交易记录包含摊位和商品信息，以便进行销售分析和对账。

#### Acceptance Criteria

1. THE System SHALL add booth_id, product_id, and operator_id columns to the transactions table
2. THE System SHALL create database indexes on booth_id, product_id, and operator_id for query performance
3. THE System SHALL allow booth_id, product_id, and operator_id to be null for backward compatibility
4. WHEN querying transaction history, THE System SHALL include booth_id, product_id, and operator_id in the response
5. THE System SHALL support filtering transactions by booth_id
6. THE System SHALL support filtering transactions by product_id

### Requirement 12: 权限校验中间件

**User Story:** 作为系统开发者，我希望有统一的权限校验机制，以便在所有需要权限控制的接口中复用。

#### Acceptance Criteria

1. THE System SHALL provide a JWT authentication dependency that extracts and validates JWT tokens
2. WHEN a JWT token is invalid or expired, THE Authentication_Dependency SHALL raise a 401 Unauthorized error
3. THE System SHALL provide a role-based authorization dependency that checks user roles
4. WHEN a user lacks required role, THE Authorization_Dependency SHALL raise a 403 Forbidden error
5. THE System SHALL provide a booth ownership validation dependency for booth_cashier operations
6. WHEN a booth_cashier attempts to access a booth they don't own, THE Booth_Ownership_Dependency SHALL raise a 403 Forbidden error
7. THE System SHALL extract user information from JWT token and make it available to route handlers

### Requirement 13: 密码安全

**User Story:** 作为系统管理员，我希望用户密码被安全存储，以便保护用户账户安全。

#### Acceptance Criteria

1. WHEN a user is created, THE System SHALL hash the password using bcrypt with a cost factor of at least 12
2. THE System SHALL never store plaintext passwords in the database
3. WHEN a user logs in, THE System SHALL verify the password against the stored hash using bcrypt
4. THE System SHALL use a constant-time comparison for password verification to prevent timing attacks

### Requirement 14: 数据库迁移脚本

**User Story:** 作为系统部署人员，我希望有数据库迁移脚本，以便将现有系统升级到摊位经营系统。

#### Acceptance Criteria

1. THE System SHALL provide a SQL migration script that creates the booths table
2. THE System SHALL provide a SQL migration script that creates the products table
3. THE System SHALL provide a SQL migration script that creates the users table
4. THE System SHALL provide a SQL migration script that adds booth_id, product_id, and operator_id columns to the transactions table
5. THE System SHALL provide a SQL migration script that creates necessary indexes
6. THE Migration_Script SHALL be idempotent and safe to run multiple times
7. THE Migration_Script SHALL preserve all existing data in the database

### Requirement 15: 接口响应格式

**User Story:** 作为前端开发者，我希望所有接口返回统一的响应格式，以便简化客户端处理逻辑。

#### Acceptance Criteria

1. WHEN an operation succeeds, THE System SHALL return a JSON response with appropriate data fields
2. WHEN an operation fails, THE System SHALL return a JSON response with error code and message
3. THE System SHALL use standard HTTP status codes (200, 201, 400, 401, 403, 404, 500)
4. WHEN validation fails, THE System SHALL return a 400 Bad Request with detailed validation errors
5. WHEN authentication fails, THE System SHALL return a 401 Unauthorized with an error message
6. WHEN authorization fails, THE System SHALL return a 403 Forbidden with an error message

### Requirement 16: 向后兼容性

**User Story:** 作为系统维护者，我希望新系统保持与现有 API 的兼容性，以便现有客户端继续正常工作。

#### Acceptance Criteria

1. THE System SHALL maintain all existing API endpoints for events, participants, accounts, and transactions
2. THE System SHALL allow existing payment and recharge operations without booth information
3. THE System SHALL allow transactions table to have null values for booth_id, product_id, and operator_id
4. THE System SHALL continue to support signature verification middleware for existing endpoints
5. THE System SHALL not break existing Android client functionality

### Requirement 17: 配置管理

**User Story:** 作为系统部署人员，我希望能够通过配置文件管理 JWT 密钥和过期时间，以便在不同环境中使用不同配置。

#### Acceptance Criteria

1. THE System SHALL read JWT secret key from environment variable or configuration file
2. THE System SHALL read JWT expiration time from environment variable or configuration file
3. THE System SHALL provide default values for JWT configuration if not specified
4. THE System SHALL validate that JWT secret key is at least 32 characters long
5. THE System SHALL log a warning if default JWT secret key is used in production

