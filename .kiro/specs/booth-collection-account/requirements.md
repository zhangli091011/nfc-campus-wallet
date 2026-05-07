# Requirements Document

## Introduction

本文档定义了"摊位专用收款账号"（Booth Collection Account）功能的需求。该功能为每个摊位用户添加一个专用收款账号，用于收集摊位的销售收入。专用收款账号的特点是只能扣款（支付），不能充值，确保资金流向的单向性和安全性。该功能需要在安卓端实现用户管理界面，让摊位用户可以方便地管理自己的专用收款账号。

## Glossary

- **System**: 摊位专用收款账号系统（Booth Collection Account System）
- **Booth_Collection_Account**: 摊位专用收款账号，一种特殊的参与者账户，只能扣款不能充值
- **Booth**: 摊位，代表活动中的一个经营单位
- **Participant**: 参与者，系统中的用户实体，可以是普通用户（person）或摊位收款账号（booth_collection）
- **Account**: 账户，参与者在特定活动下的账户实体
- **Booth_Cashier**: 摊位收银员，负责管理摊位的用户角色
- **Android_Client**: 安卓客户端应用
- **NFC_Card**: NFC 卡，用于绑定参与者身份
- **Transaction**: 交易记录，包含充值和扣款操作
- **Event**: 活动，系统中的活动实体
- **Backend_API**: 后端 API 服务

## Requirements

### Requirement 1: 摊位收款账号数据模型

**User Story:** 作为系统开发者，我希望能够在数据库中存储摊位收款账号信息，以便区分普通参与者和收款账号。

#### Acceptance Criteria

1. THE System SHALL store booth collection accounts as Participant records with participant_type set to 'booth_collection'
2. THE System SHALL enforce that Participant.participant_type is either 'person' or 'booth_collection'
3. THE System SHALL create a database index on Participant.participant_type for query performance
4. WHEN a booth collection account is created, THE System SHALL assign a unique card_uid for NFC card binding
5. THE System SHALL allow booth collection accounts to have null values for class_name and student_no fields
6. THE System SHALL store booth collection account name in the format "摊位名称-收款账号"

### Requirement 2: 摊位收款账号与摊位关联

**User Story:** 作为活动管理员，我希望每个摊位收款账号能够关联到特定的摊位，以便追踪资金归属。

#### Acceptance Criteria

1. THE System SHALL store the association between booth collection accounts and booths
2. WHEN a booth collection account is created, THE System SHALL require a valid booth_id reference
3. THE System SHALL support one-to-one relationship between booth and booth collection account
4. THE System SHALL prevent creating multiple booth collection accounts for the same booth
5. THE System SHALL create a database index on the booth-account association for query performance

### Requirement 3: 充值限制规则

**User Story:** 作为系统管理员，我希望摊位收款账号不能充值，以便确保资金流向的单向性。

#### Acceptance Criteria

1. WHEN a recharge operation is attempted on a booth collection account, THE System SHALL return a validation error
2. THE System SHALL check participant_type before processing recharge transactions
3. THE System SHALL return error code 'RECHARGE_NOT_ALLOWED' with message "摊位收款账号不支持充值操作"
4. THE System SHALL allow recharge operations only for participants with participant_type 'person'
5. THE Participant.can_recharge method SHALL return false for booth collection accounts

### Requirement 4: 扣款操作支持

**User Story:** 作为摊位收银员，我希望能够从摊位收款账号扣款，以便结算摊位收入。

#### Acceptance Criteria

1. WHEN a payment transaction is processed, THE System SHALL allow deduction from booth collection accounts
2. THE System SHALL verify sufficient balance before processing deduction from booth collection accounts
3. THE System SHALL record deduction transactions with type 'pay' in the transactions table
4. THE System SHALL update the booth collection account balance after successful deduction
5. THE System SHALL support deduction operations for both 'person' and 'booth_collection' participant types

### Requirement 5: 摊位收款账号创建接口

**User Story:** 作为活动管理员，我希望通过 API 接口创建摊位收款账号，以便为摊位配置收款功能。

#### Acceptance Criteria

1. WHEN an authorized user sends POST /booths/{booth_id}/collection-account with valid data, THE System SHALL create a booth collection account
2. THE System SHALL require event_admin or super_admin role to create booth collection accounts
3. THE System SHALL validate that the booth exists before creating the collection account
4. THE System SHALL validate that the booth does not already have a collection account
5. THE System SHALL generate a unique card_uid for the collection account
6. THE System SHALL create an account record for the collection account under the booth's event
7. THE System SHALL return the created collection account details including participant_id, card_uid, and account_id

### Requirement 6: 摊位收款账号查询接口

**User Story:** 作为摊位收银员，我希望能够查询自己摊位的收款账号信息，以便了解收款账号状态和余额。

#### Acceptance Criteria

1. WHEN a booth_cashier sends GET /booths/{booth_id}/collection-account, THE System SHALL return the booth's collection account details
2. THE System SHALL verify that the booth_cashier has permission to access the specified booth
3. THE System SHALL return collection account details including participant_id, name, card_uid, balance, and status
4. WHEN a booth does not have a collection account, THE System SHALL return a 404 Not Found error
5. THE System SHALL allow event_admin and super_admin to query any booth's collection account

### Requirement 7: 摊位收款账号余额查询

**User Story:** 作为摊位收银员，我希望能够查询收款账号的余额，以便了解摊位的收入情况。

#### Acceptance Criteria

1. WHEN a user queries booth collection account balance, THE System SHALL return the current balance in the event account
2. THE System SHALL calculate balance from the account record associated with the collection account
3. THE System SHALL return balance in yuan (元) with two decimal places
4. THE System SHALL include balance information in the collection account details response
5. THE System SHALL support balance query through both participant_id and card_uid

### Requirement 8: 安卓端收款账号管理界面

**User Story:** 作为摊位收银员，我希望在安卓端有专门的界面管理收款账号，以便方便地查看和操作收款账号。

#### Acceptance Criteria

1. THE Android_Client SHALL provide a collection account management screen accessible from the booth management menu
2. THE Android_Client SHALL display collection account information including name, card_uid, balance, and status
3. THE Android_Client SHALL provide a button to create collection account if it does not exist
4. THE Android_Client SHALL display an error message if collection account creation fails
5. THE Android_Client SHALL refresh collection account information when the screen is opened
6. THE Android_Client SHALL display balance in yuan (元) with two decimal places

### Requirement 9: 安卓端收款账号创建流程

**User Story:** 作为摊位收银员，我希望能够在安卓端创建收款账号，以便快速配置摊位收款功能。

#### Acceptance Criteria

1. WHEN a booth_cashier clicks the create collection account button, THE Android_Client SHALL send a POST request to /booths/{booth_id}/collection-account
2. THE Android_Client SHALL include the JWT token in the Authorization header
3. WHEN the creation succeeds, THE Android_Client SHALL display a success message and show the collection account details
4. WHEN the creation fails, THE Android_Client SHALL display the error message from the API response
5. THE Android_Client SHALL disable the create button if a collection account already exists

### Requirement 10: 安卓端收款账号余额显示

**User Story:** 作为摊位收银员，我希望在安卓端清晰地看到收款账号的余额，以便了解摊位收入。

#### Acceptance Criteria

1. THE Android_Client SHALL display collection account balance prominently on the collection account management screen
2. THE Android_Client SHALL format balance with thousand separators (e.g., "1,234.56")
3. THE Android_Client SHALL display balance in yuan (元) with currency symbol "¥"
4. THE Android_Client SHALL update balance display after each transaction
5. THE Android_Client SHALL show a loading indicator while fetching balance information

### Requirement 11: 安卓端收款账号卡片绑定显示

**User Story:** 作为摊位收银员，我希望在安卓端看到收款账号绑定的 NFC 卡号，以便识别收款卡。

#### Acceptance Criteria

1. THE Android_Client SHALL display the card_uid of the collection account on the management screen
2. THE Android_Client SHALL format card_uid in a readable format (e.g., "A1:B2:C3:D4")
3. THE Android_Client SHALL provide a copy button to copy card_uid to clipboard
4. WHEN the copy button is clicked, THE Android_Client SHALL show a toast message "卡号已复制"
5. THE Android_Client SHALL display card_uid in a monospace font for better readability

### Requirement 12: 收款账号交易历史查询

**User Story:** 作为摊位收银员，我希望能够查询收款账号的交易历史，以便追踪资金流向。

#### Acceptance Criteria

1. WHEN a user sends GET /booths/{booth_id}/collection-account/transactions, THE System SHALL return the collection account's transaction history
2. THE System SHALL filter transactions by the collection account's participant_id
3. THE System SHALL support pagination with limit and offset parameters
4. THE System SHALL support date range filtering with start_date and end_date parameters
5. THE System SHALL return transactions in descending order by created_at
6. THE System SHALL include transaction details such as type, amount, balance_before, balance_after, and created_at

### Requirement 13: 安卓端收款账号交易历史界面

**User Story:** 作为摊位收银员，我希望在安卓端查看收款账号的交易历史，以便了解资金流向。

#### Acceptance Criteria

1. THE Android_Client SHALL provide a transaction history button on the collection account management screen
2. WHEN the transaction history button is clicked, THE Android_Client SHALL navigate to a transaction history screen
3. THE Android_Client SHALL display transactions in a list with type, amount, balance, and timestamp
4. THE Android_Client SHALL support pull-to-refresh to reload transaction history
5. THE Android_Client SHALL support infinite scroll to load more transactions
6. THE Android_Client SHALL display transaction type with appropriate icons (pay icon for deductions)

### Requirement 14: 收款账号状态管理

**User Story:** 作为活动管理员，我希望能够管理收款账号的状态，以便控制收款账号的可用性。

#### Acceptance Criteria

1. THE System SHALL support collection account status values of 'active', 'inactive', and 'blocked'
2. WHEN a collection account status is 'inactive' or 'blocked', THE System SHALL prevent deduction operations
3. THE System SHALL provide an API endpoint PATCH /booths/{booth_id}/collection-account/status to update status
4. THE System SHALL require event_admin or super_admin role to update collection account status
5. THE System SHALL validate that the new status is one of the allowed values
6. THE System SHALL return the updated collection account details after status change

### Requirement 15: 安卓端收款账号状态显示

**User Story:** 作为摊位收银员，我希望在安卓端看到收款账号的状态，以便了解账号是否可用。

#### Acceptance Criteria

1. THE Android_Client SHALL display collection account status on the management screen
2. THE Android_Client SHALL use color coding for status: green for 'active', gray for 'inactive', red for 'blocked'
3. THE Android_Client SHALL display status text in Chinese: "正常" for active, "未激活" for inactive, "已封禁" for blocked
4. WHEN the status is not 'active', THE Android_Client SHALL display a warning message
5. THE Android_Client SHALL refresh status display when the screen is opened

### Requirement 16: 收款账号权限验证

**User Story:** 作为系统管理员，我希望收款账号相关操作有严格的权限控制，以便保护资金安全。

#### Acceptance Criteria

1. THE System SHALL require JWT authentication for all collection account management endpoints
2. THE System SHALL verify that booth_cashier can only access their assigned booth's collection account
3. THE System SHALL allow event_admin and super_admin to access all collection accounts
4. WHEN a booth_cashier attempts to access another booth's collection account, THE System SHALL return a 403 Forbidden error
5. THE System SHALL extract user role and booth_id from JWT token for permission validation

### Requirement 17: 收款账号初始余额设置

**User Story:** 作为活动管理员，我希望在创建收款账号时可以设置初始余额，以便灵活配置收款账号。

#### Acceptance Criteria

1. WHEN creating a booth collection account, THE System SHALL accept an optional initial_balance parameter
2. WHERE initial_balance is not provided, THE System SHALL set the account balance to 0
3. WHERE initial_balance is provided, THE System SHALL validate that it is a non-negative number
4. THE System SHALL create the account record with the specified initial_balance
5. THE System SHALL convert initial_balance from yuan to cents for storage

### Requirement 18: 收款账号删除限制

**User Story:** 作为系统管理员，我希望收款账号不能被随意删除，以便保护交易历史数据。

#### Acceptance Criteria

1. THE System SHALL not provide an API endpoint to delete booth collection accounts
2. WHEN a booth is deleted, THE System SHALL set the collection account status to 'inactive' instead of deleting it
3. THE System SHALL preserve all transaction history associated with the collection account
4. THE System SHALL allow event_admin and super_admin to manually set collection account status to 'inactive'
5. THE System SHALL prevent reactivation of collection accounts for deleted booths

### Requirement 19: 安卓端错误处理

**User Story:** 作为摊位收银员，我希望在安卓端遇到错误时能看到清晰的错误提示，以便了解问题所在。

#### Acceptance Criteria

1. WHEN an API request fails, THE Android_Client SHALL display the error message from the API response
2. WHEN network connection fails, THE Android_Client SHALL display "网络连接失败，请检查网络设置"
3. WHEN authentication fails, THE Android_Client SHALL display "登录已过期，请重新登录" and navigate to login screen
4. WHEN permission is denied, THE Android_Client SHALL display "权限不足，无法执行此操作"
5. THE Android_Client SHALL log error details for debugging purposes

### Requirement 20: 收款账号 API 响应格式

**User Story:** 作为前端开发者，我希望收款账号相关 API 返回统一的响应格式，以便简化客户端处理逻辑。

#### Acceptance Criteria

1. WHEN a collection account operation succeeds, THE System SHALL return a JSON response with collection account details
2. THE System SHALL include fields: participant_id, name, card_uid, participant_type, status, account_id, balance, created_at
3. WHEN a collection account operation fails, THE System SHALL return a JSON response with error_code and message
4. THE System SHALL use standard HTTP status codes: 200 for success, 201 for creation, 400 for validation errors, 403 for permission errors, 404 for not found
5. THE System SHALL return balance in cents as an integer in the API response

