# Requirements Document

## Introduction

本文档定义了"Android 收银终端升级"（Android Cashier Terminal Upgrade）的功能需求。该系统将现有的 Android NFC 钱包 App 升级为功能完整的活动收银终端，支持摊位收银员登录、商品管理、购物车、多种支付模式，并与后端的摊位经营系统（Booth Management System）完全集成。

## Glossary

- **System**: Android 收银终端应用（Android Cashier Terminal App）
- **Cashier**: 摊位收银员，使用 Android 终端进行收银操作的用户
- **Booth**: 摊位，收银员所属的经营单位
- **Product**: 商品，摊位销售的物品或服务
- **Cart**: 购物车，临时存储待结算商品的容器
- **Participant**: 参与者，持有 NFC 卡的消费者
- **Card_UID**: NFC 卡的唯一标识符
- **JWT_Token**: JSON Web Token，用于收银员身份认证
- **Quick_Amount_Mode**: 快速金额模式，手动输入金额的支付方式
- **Product_Selection_Mode**: 商品点选模式，通过选择商品构建购物车的支付方式
- **Backend_API**: 后端 API 服务，提供认证、商品、支付等接口
- **Session**: 会话，从刷卡到交易完成或清空的完整流程

## Requirements

### Requirement 1: 收银员登录认证

**User Story:** 作为摊位收银员，我希望能够使用用户名和密码登录系统，以便获得收银权限并访问我的摊位数据。

#### Acceptance Criteria

1. WHEN the app starts, THE System SHALL display a login screen if no valid JWT token exists
2. WHEN a cashier submits valid credentials, THE System SHALL call POST /auth/login and store the JWT token securely
3. WHEN a cashier submits invalid credentials, THE System SHALL display an error message "用户名或密码错误"
4. THE System SHALL extract and store user_id, username, role, and booth_id from the JWT token
5. WHEN the JWT token expires, THE System SHALL redirect the cashier to the login screen
6. THE System SHALL validate that the user role is "booth_cashier" before allowing access to cashier functions
7. THE System SHALL display the current logged-in cashier username on the main screen

### Requirement 2: 活动和摊位信息显示

**User Story:** 作为摊位收银员，我希望在主界面看到当前活动名称和摊位名称，以便确认我正在为正确的摊位收银。

#### Acceptance Criteria

1. WHEN the cashier logs in successfully, THE System SHALL call GET /booths/{booth_id} to retrieve booth information
2. THE System SHALL display the booth name on the main screen
3. THE System SHALL display the event name associated with the booth on the main screen
4. WHEN booth information cannot be retrieved, THE System SHALL display an error message "无法获取摊位信息"
5. THE System SHALL cache booth and event information for offline display

### Requirement 3: NFC 卡片读取和参与者信息查询

**User Story:** 作为摊位收银员，我希望刷卡后自动显示参与者姓名和余额，以便快速确认客户身份和支付能力。

#### Acceptance Criteria

1. WHEN an NFC card is detected, THE System SHALL extract the card_uid using existing NFCReader logic
2. WHEN a card_uid is obtained, THE System SHALL display the card_uid on the main screen
3. WHEN a card_uid is obtained, THE System SHALL call GET /balance with signature verification to query balance
4. WHEN balance is retrieved successfully, THE System SHALL display the participant name and current balance
5. WHEN the card is not bound to a participant, THE System SHALL display an error message "卡未绑定"
6. WHEN balance query fails due to network error, THE System SHALL display an error message "网络连接失败"
7. THE System SHALL preserve existing signature generation logic for balance queries

### Requirement 4: 商品列表获取和显示

**User Story:** 作为摊位收银员，我希望看到我摊位的所有可售商品，以便快速选择商品加入购物车。

#### Acceptance Criteria

1. WHEN the main screen loads, THE System SHALL call GET /products?booth_id={booth_id} with JWT authentication
2. THE System SHALL filter and display only enabled products (enabled=true)
3. THE System SHALL display product name and price for each product
4. WHEN no products are available, THE System SHALL display a message "暂无商品"
5. THE System SHALL refresh the product list when the cashier manually triggers a refresh action
6. THE System SHALL cache product list for offline display
7. THE System SHALL display product price in yuan format (¥X.XX)

### Requirement 5: 商品点选和购物车管理

**User Story:** 作为摊位收银员，我希望能够点击商品加入购物车并修改数量，以便为客户构建订单。

#### Acceptance Criteria

1. WHEN a cashier clicks a product button, THE System SHALL add the product to the shopping cart with quantity 1
2. WHEN a product already exists in the cart, THE System SHALL increment its quantity by 1
3. THE System SHALL display the shopping cart with product name, unit price, quantity, and subtotal
4. THE System SHALL allow the cashier to increase or decrease product quantity in the cart
5. THE System SHALL allow the cashier to remove a product from the cart
6. THE System SHALL calculate and display the total amount of all items in the cart
7. WHEN the cart is empty, THE System SHALL disable the payment button

### Requirement 6: 快速金额输入模式

**User Story:** 作为摊位收银员，我希望能够手动输入金额并添加备注，以便处理非标准商品或服务的支付。

#### Acceptance Criteria

1. THE System SHALL provide a text input field for manual amount entry
2. THE System SHALL provide a text input field for optional remark entry
3. THE System SHALL validate that the entered amount is a positive number
4. THE System SHALL validate that the entered amount does not exceed 10000 yuan
5. WHEN using quick amount mode, THE System SHALL ignore the shopping cart contents
6. THE System SHALL allow the cashier to switch between product selection mode and quick amount mode
7. THE System SHALL clear the amount input field after a successful transaction

### Requirement 7: 支付交易处理

**User Story:** 作为摊位收银员，我希望点击扣款按钮后能够完成支付交易，以便为客户结账。

#### Acceptance Criteria

1. WHEN the cashier clicks the payment button in product selection mode, THE System SHALL call POST /booths/{booth_id}/pay with JWT authentication
2. WHEN the cashier clicks the payment button in quick amount mode, THE System SHALL call POST /booths/{booth_id}/pay with amount and optional remark
3. THE System SHALL include event_id, card_uid, booth_id, amount, and operator_id in the payment request
4. WHEN using product selection mode with a single product, THE System SHALL include product_id in the payment request
5. WHEN the payment succeeds, THE System SHALL display the new balance and a success message
6. WHEN the payment fails due to insufficient funds, THE System SHALL display an error message "余额不足"
7. WHEN the payment succeeds, THE System SHALL clear the shopping cart and amount input field
8. THE System SHALL disable the payment button during transaction processing to prevent double submission

### Requirement 8: 充值功能（权限控制）

**User Story:** 作为摊位收银员，我希望只有在拥有充值权限时才能看到充值按钮，以便进行充值操作。

#### Acceptance Criteria

1. WHEN the user role is "booth_cashier", THE System SHALL hide the recharge button
2. WHEN the user role is "event_admin" or "super_admin", THE System SHALL display the recharge button
3. WHEN the recharge button is clicked, THE System SHALL call POST /recharge with signature verification
4. WHEN recharge succeeds, THE System SHALL display the new balance and a success message
5. WHEN recharge fails due to permission error, THE System SHALL display an error message "权限不足"
6. THE System SHALL preserve existing signature generation logic for recharge operations

### Requirement 9: 余额查询功能

**User Story:** 作为摊位收银员，我希望能够手动触发余额查询，以便在交易后确认最新余额。

#### Acceptance Criteria

1. THE System SHALL provide a "查询余额" button on the main screen
2. WHEN the button is clicked and a card is present, THE System SHALL call GET /balance to refresh the balance
3. WHEN the button is clicked and no card is present, THE System SHALL display an error message "请先刷卡"
4. THE System SHALL update the displayed balance with the query result
5. THE System SHALL display a loading indicator during the balance query

### Requirement 10: 交易结果显示

**User Story:** 作为摊位收银员，我希望在交易完成后看到清晰的成功或失败提示，以便确认交易状态。

#### Acceptance Criteria

1. WHEN a payment transaction succeeds, THE System SHALL display a success message "支付成功" in green color
2. WHEN a recharge transaction succeeds, THE System SHALL display a success message "充值成功" in green color
3. WHEN a transaction fails, THE System SHALL display an error message in red color
4. THE System SHALL display the new balance after a successful transaction
5. THE System SHALL auto-dismiss success messages after 5 seconds
6. THE System SHALL keep error messages visible until the cashier dismisses them or starts a new transaction
7. THE System SHALL display transaction_id for successful transactions

### Requirement 11: 错误处理和用户提示

**User Story:** 作为摊位收银员，我希望系统能够区分不同类型的错误并给出明确提示，以便我知道如何处理问题。

#### Acceptance Criteria

1. WHEN a network connection error occurs, THE System SHALL display "网络连接失败，请检查网络"
2. WHEN signature verification fails, THE System SHALL display "签名验证失败，请联系管理员"
3. WHEN permission is denied, THE System SHALL display "权限不足，无法执行此操作"
4. WHEN balance is insufficient, THE System SHALL display "余额不足，当前余额：¥X.XX"
5. WHEN the event is closed, THE System SHALL display "活动已关闭，无法进行交易"
6. WHEN the card is not bound, THE System SHALL display "卡未绑定，请先绑定参与者"
7. WHEN a participant does not exist, THE System SHALL display "用户不存在"
8. THE System SHALL log all errors to Android Logcat for debugging

### Requirement 12: 会话管理和清空功能

**User Story:** 作为摊位收银员，我希望能够清空当前会话，以便开始为下一位客户服务。

#### Acceptance Criteria

1. THE System SHALL provide a "清空" button on the main screen
2. WHEN the clear button is clicked, THE System SHALL clear the displayed card_uid
3. WHEN the clear button is clicked, THE System SHALL clear the displayed participant name and balance
4. WHEN the clear button is clicked, THE System SHALL clear the shopping cart
5. WHEN the clear button is clicked, THE System SHALL clear the amount input field
6. WHEN the clear button is clicked, THE System SHALL hide transaction result messages
7. THE System SHALL automatically clear the session after a successful transaction (optional behavior)

### Requirement 13: 离线数据缓存

**User Story:** 作为摊位收银员，我希望在网络不稳定时仍能看到基本信息，以便继续工作。

#### Acceptance Criteria

1. THE System SHALL cache the JWT token in Android SharedPreferences with encryption
2. THE System SHALL cache booth information in local storage
3. THE System SHALL cache product list in local storage
4. WHEN network is unavailable, THE System SHALL display cached booth and product information
5. WHEN network is unavailable, THE System SHALL disable payment and recharge operations
6. THE System SHALL display a network status indicator on the main screen
7. THE System SHALL attempt to refresh cached data when network becomes available

### Requirement 14: UI 布局和交互设计

**User Story:** 作为摊位收银员，我希望界面简洁实用，以便快速完成收银操作。

#### Acceptance Criteria

1. THE System SHALL use a single-screen layout for all cashier operations
2. THE System SHALL display information in the following order from top to bottom: event/booth info, cashier info, card info, participant info, balance, product buttons, cart, amount input, action buttons
3. THE System SHALL use large touch-friendly buttons (minimum 48dp height)
4. THE System SHALL use clear visual hierarchy with appropriate spacing and grouping
5. THE System SHALL use color coding: green for success, red for error, blue for information, orange for warning
6. THE System SHALL disable buttons during processing to prevent accidental double-clicks
7. THE System SHALL provide visual feedback (ripple effect) for all button clicks

### Requirement 15: API 客户端封装

**User Story:** 作为开发者，我希望有统一的 API 客户端封装，以便简化网络请求代码。

#### Acceptance Criteria

1. THE System SHALL extend the existing APIClient to support JWT authentication
2. THE System SHALL provide a method to set and clear JWT tokens
3. THE System SHALL automatically include "Authorization: Bearer {token}" header for authenticated requests
4. THE System SHALL handle 401 Unauthorized errors by redirecting to login screen
5. THE System SHALL handle 403 Forbidden errors by displaying permission error messages
6. THE System SHALL preserve existing signature verification logic for balance and legacy payment endpoints
7. THE System SHALL provide methods for all new endpoints: /auth/login, /booths/{id}, /products, /booths/{id}/pay

### Requirement 16: 登录态持久化

**User Story:** 作为摊位收银员，我希望登录后不需要频繁重新登录，以便提高工作效率。

#### Acceptance Criteria

1. THE System SHALL store the JWT token in Android SharedPreferences after successful login
2. THE System SHALL encrypt the JWT token before storage using Android Keystore
3. WHEN the app starts, THE System SHALL check for a valid stored JWT token
4. WHEN a valid token exists, THE System SHALL skip the login screen and proceed to the main screen
5. WHEN the token is expired or invalid, THE System SHALL clear the stored token and show the login screen
6. THE System SHALL provide a logout button that clears the stored token and returns to login screen
7. THE System SHALL validate token expiration before each API call

### Requirement 17: 向后兼容性

**User Story:** 作为系统维护者，我希望新版本保留现有的 NFC 读取和签名生成逻辑，以便与旧版本后端兼容。

#### Acceptance Criteria

1. THE System SHALL preserve the existing NFCReader.java implementation without modification
2. THE System SHALL preserve the existing SignatureGenerator.java implementation without modification
3. THE System SHALL continue to support legacy /balance, /pay, and /recharge endpoints with signature verification
4. THE System SHALL allow switching between JWT-authenticated endpoints and signature-verified endpoints via configuration
5. THE System SHALL maintain backward compatibility with existing data models (BalanceResponse, TransactionResponse, etc.)

### Requirement 18: 多商品支付处理

**User Story:** 作为摊位收银员，我希望在购物车有多个商品时能够正确处理支付，以便完成复杂订单。

#### Acceptance Criteria

1. WHEN the shopping cart contains multiple products, THE System SHALL calculate the total amount
2. WHEN the shopping cart contains multiple products, THE System SHALL call POST /booths/{booth_id}/pay with the total amount
3. WHEN the shopping cart contains multiple products, THE System SHALL NOT include product_id in the payment request
4. WHEN the shopping cart contains multiple products, THE System SHALL include a remark listing all products and quantities
5. THE System SHALL format the remark as "商品1 x数量1, 商品2 x数量2, ..."
6. THE System SHALL limit the remark length to 255 characters

### Requirement 19: 配置管理

**User Story:** 作为开发者，我希望能够通过配置文件管理后端 URL 和密钥，以便在不同环境中使用不同配置。

#### Acceptance Criteria

1. THE System SHALL read backend BASE_URL from a configuration file or build config
2. THE System SHALL read SECRET_KEY from a configuration file or build config
3. THE System SHALL provide different configurations for development, staging, and production environments
4. THE System SHALL validate that BASE_URL is a valid HTTPS URL in production builds
5. THE System SHALL log a warning if default SECRET_KEY is used in production builds
6. THE System SHALL allow runtime configuration changes for testing purposes

### Requirement 20: 日志和调试支持

**User Story:** 作为开发者，我希望系统记录详细的日志信息，以便排查问题和优化性能。

#### Acceptance Criteria

1. THE System SHALL log all API requests with method, URL, and request body (excluding sensitive data)
2. THE System SHALL log all API responses with status code and response body
3. THE System SHALL log all NFC card detection events with card_uid
4. THE System SHALL log all authentication events (login, logout, token refresh)
5. THE System SHALL log all errors with stack traces
6. THE System SHALL use appropriate log levels: DEBUG, INFO, WARN, ERROR
7. THE System SHALL disable verbose logging in production builds

