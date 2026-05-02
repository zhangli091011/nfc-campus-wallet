# Requirements Document

## Introduction

本文档定义了"学校单场活动额度系统"升级项目的功能需求。该项目将基础 NFC 钱包系统升级为支持学校活动的额度管理系统。系统的核心特性包括：

- **活动隔离**：每个活动拥有独立的额度系统，参与者在不同活动下有独立账户
- **卡片绑定**：NFC 卡仅存储 card_uid，所有余额和账户信息存储在服务器
- **活动控制**：活动管理员可以控制充值和消费的开关、时间范围
- **账本模式**：使用 Ledger Mode 保证交易一致性和可审计性
- **向后兼容**：保持原有 User 模型和接口的兼容性

本阶段专注于核心功能：活动管理、参与者管理、卡片绑定、活动账户和交易处理。不包括摊位（booth）、商品（product）、排行榜和后台管理页面。

## Glossary

- **System**: 学校单场活动额度系统（NFC Campus Event Quota System）
- **Event_Service**: 活动服务模块，负责活动的创建、查询、更新和验证
- **Participant_Service**: 参与者服务模块，负责参与者的创建、查询和卡片绑定
- **Account_Service**: 账户服务模块，负责活动账户的创建和查询
- **Ledger_Service**: 账本服务模块，负责账本追加模式的交易记录
- **Transaction_Service**: 交易服务模块，负责充值和消费交易的处理
- **Event**: 活动实体，代表一个学校活动
- **Participant**: 参与者实体，代表一个活动参与者
- **Account**: 账户实体，代表参与者在特定活动下的账户
- **Transaction**: 交易实体，代表一笔充值或消费交易
- **card_uid**: NFC 卡片的唯一标识符（十六进制字符串）
- **balance**: 账户余额，以"分"为单位存储，以"元"为单位交互
- **event_id**: 活动的唯一标识符
- **participant_id**: 参与者的唯一标识符
- **account_id**: 账户的唯一标识符
- **Administrator**: 系统管理员，有权创建活动和参与者
- **Recharge_Endpoint**: 充值接口，处理充值请求
- **Payment_Endpoint**: 支付接口，处理消费请求
- **Balance_Endpoint**: 余额查询接口，返回账户余额

## Requirements

### Requirement 1: 活动管理

**User Story:** 作为系统管理员，我希望能够创建和管理活动，以便为不同的学校活动提供独立的额度系统。

#### Acceptance Criteria

1. WHEN 管理员提供活动名称、开始时间和结束时间，THE Event_Service SHALL 创建一个新的 Event
2. THE Event_Service SHALL 验证结束时间晚于开始时间
3. WHEN 管理员查询活动列表，THE Event_Service SHALL 返回所有活动及其状态
4. WHEN 管理员查询特定活动，THE Event_Service SHALL 返回该活动的详细信息
5. WHEN 管理员更新活动信息，THE Event_Service SHALL 更新指定字段并保持其他字段不变
6. THE Event_Service SHALL 支持活动状态：draft（草稿）、active（活跃）、paused（暂停）、ended（结束）
7. THE Event_Service SHALL 支持过期规则：event_end（活动结束时过期）、never（永不过期）、custom（自定义）

### Requirement 2: 活动状态验证

**User Story:** 作为系统，我需要验证活动状态，以便确保充值和消费操作只在允许的时间和状态下进行。

#### Acceptance Criteria

1. WHEN 充值请求到达，THE Event_Service SHALL 验证活动状态为 active
2. WHEN 充值请求到达，THE Event_Service SHALL 验证当前时间在活动时间范围内
3. WHEN 充值请求到达，THE Event_Service SHALL 验证活动的 recharge_enabled 标志为 true
4. WHEN 消费请求到达，THE Event_Service SHALL 验证活动状态为 active
5. WHEN 消费请求到达，THE Event_Service SHALL 验证当前时间在活动时间范围内
6. WHEN 消费请求到达，THE Event_Service SHALL 验证活动的 consume_enabled 标志为 true
7. IF 活动验证失败，THEN THE Event_Service SHALL 返回描述性错误信息

### Requirement 3: 参与者管理

**User Story:** 作为系统管理员，我希望能够创建参与者并绑定 NFC 卡片，以便参与者可以使用卡片进行充值和消费。

#### Acceptance Criteria

1. WHEN 管理员提供参与者姓名和 card_uid，THE Participant_Service SHALL 创建一个新的 Participant
2. THE Participant_Service SHALL 验证 card_uid 为十六进制格式
3. THE Participant_Service SHALL 确保 card_uid 在系统中唯一
4. WHEN 管理员查询参与者列表，THE Participant_Service SHALL 返回所有参与者信息
5. WHEN 管理员通过 card_uid 查询参与者，THE Participant_Service SHALL 返回对应的参与者信息
6. WHEN 管理员更新参与者的 card_uid，THE Participant_Service SHALL 更新卡片绑定
7. THE Participant_Service SHALL 支持参与者状态：active（活跃）、inactive（非活跃）、blocked（已封禁）

### Requirement 4: 活动账户管理

**User Story:** 作为系统，我需要为参与者在特定活动下自动创建和管理账户，以便实现活动隔离的额度系统。

#### Acceptance Criteria

1. WHEN 参与者首次在某活动下进行交易，THE Account_Service SHALL 自动创建该参与者在该活动下的 Account
2. THE Account_Service SHALL 确保一个参与者在一个活动下只有一个账户
3. WHEN 查询账户余额，THE Account_Service SHALL 返回指定参与者在指定活动下的余额
4. THE Account_Service SHALL 以"分"为单位存储余额
5. THE Account_Service SHALL 以"元"为单位返回余额
6. WHEN 查询参与者的所有账户，THE Account_Service SHALL 返回该参与者在所有活动下的账户列表
7. THE Account_Service SHALL 确保账户余额非负

### Requirement 5: 活动模式充值

**User Story:** 作为参与者，我希望能够在活动中刷卡充值，以便获得活动额度进行消费。

#### Acceptance Criteria

1. WHEN 充值请求包含 event_id 和 card_uid，THE Recharge_Endpoint SHALL 通过 card_uid 查找 Participant
2. WHEN 找到参与者，THE Recharge_Endpoint SHALL 验证活动允许充值
3. WHEN 活动验证通过，THE Recharge_Endpoint SHALL 获取或创建该参与者在该活动下的 Account
4. WHEN 账户准备就绪，THE Recharge_Endpoint SHALL 调用 Ledger_Service 追加贷方记录
5. THE Recharge_Endpoint SHALL 返回交易成功状态、新余额、交易前余额和交易 ID
6. IF 参与者不存在，THEN THE Recharge_Endpoint SHALL 返回错误码 PARTICIPANT_NOT_FOUND
7. IF 活动不允许充值，THEN THE Recharge_Endpoint SHALL 返回错误码 EVENT_INACTIVE
8. THE Recharge_Endpoint SHALL 验证充值金额为正数

### Requirement 6: 活动模式消费

**User Story:** 作为参与者，我希望能够在活动中刷卡消费，以便使用活动额度购买商品或服务。

#### Acceptance Criteria

1. WHEN 消费请求包含 event_id 和 card_uid，THE Payment_Endpoint SHALL 通过 card_uid 查找 Participant
2. WHEN 找到参与者，THE Payment_Endpoint SHALL 验证活动允许消费
3. WHEN 活动验证通过，THE Payment_Endpoint SHALL 获取或创建该参与者在该活动下的 Account
4. WHEN 账户准备就绪，THE Payment_Endpoint SHALL 调用 Ledger_Service 追加借方记录
5. THE Payment_Endpoint SHALL 验证账户余额充足
6. THE Payment_Endpoint SHALL 返回交易成功状态、新余额、交易前余额和交易 ID
7. IF 参与者不存在，THEN THE Payment_Endpoint SHALL 返回错误码 PARTICIPANT_NOT_FOUND
8. IF 活动不允许消费，THEN THE Payment_Endpoint SHALL 返回错误码 EVENT_INACTIVE
9. IF 余额不足，THEN THE Payment_Endpoint SHALL 返回错误码 INSUFFICIENT_FUNDS

### Requirement 7: 活动模式余额查询

**User Story:** 作为参与者，我希望能够查询我在特定活动下的余额，以便了解我的可用额度。

#### Acceptance Criteria

1. WHEN 余额查询请求包含 event_id 和 card_uid，THE Balance_Endpoint SHALL 通过 card_uid 查找 Participant
2. WHEN 找到参与者，THE Balance_Endpoint SHALL 查询该参与者在该活动下的 Account
3. WHEN 账户存在，THE Balance_Endpoint SHALL 返回账户余额（以元为单位）
4. WHEN 账户不存在，THE Balance_Endpoint SHALL 返回余额为 0
5. IF 参与者不存在，THEN THE Balance_Endpoint SHALL 返回错误码 PARTICIPANT_NOT_FOUND
6. IF 活动不存在，THEN THE Balance_Endpoint SHALL 返回错误码 EVENT_NOT_FOUND

### Requirement 8: 账本模式支持活动账户

**User Story:** 作为系统，我需要扩展账本服务以支持活动账户，以便为活动模式提供相同的交易一致性保证。

#### Acceptance Criteria

1. THE Ledger_Service SHALL 支持 Account 模型的借方和贷方记录
2. WHEN 追加贷方记录到 Account，THE Ledger_Service SHALL 使用 SELECT FOR UPDATE 锁定账户记录
3. WHEN 追加借方记录到 Account，THE Ledger_Service SHALL 验证账户余额充足
4. THE Ledger_Service SHALL 在同一事务内更新账户余额和创建交易记录
5. THE Ledger_Service SHALL 记录交易前余额和交易后余额
6. THE Ledger_Service SHALL 保持对原有 User 模型的支持
7. FOR ALL 交易记录，THE Ledger_Service SHALL 确保 balance_after = balance_before + amount（贷方）或 balance_after = balance_before - amount（借方）

### Requirement 9: 交易服务支持活动模式

**User Story:** 作为系统，我需要扩展交易服务以支持活动模式，以便处理基于 event_id 和 card_uid 的交易请求。

#### Acceptance Criteria

1. THE Transaction_Service SHALL 支持基于 event_id 和 card_uid 的充值请求
2. THE Transaction_Service SHALL 支持基于 event_id 和 card_uid 的消费请求
3. WHEN 处理活动模式交易，THE Transaction_Service SHALL 自动查找 Participant
4. WHEN 处理活动模式交易，THE Transaction_Service SHALL 自动获取或创建 Account
5. THE Transaction_Service SHALL 将 event_id、participant_id 和 account_id 记录到交易记录中
6. THE Transaction_Service SHALL 保持对原有 uid 模式的支持
7. THE Transaction_Service SHALL 使用 Ledger_Service 执行所有余额变更操作

### Requirement 10: 并发安全

**User Story:** 作为系统，我需要确保并发交易的安全性，以便防止余额不一致和重复扣款。

#### Acceptance Criteria

1. WHEN 多个交易同时操作同一账户，THE Ledger_Service SHALL 使用行锁（SELECT FOR UPDATE）串行化操作
2. THE Ledger_Service SHALL 在数据库事务内完成余额验证、更新和交易记录创建
3. IF 事务失败，THEN THE Ledger_Service SHALL 回滚所有变更
4. THE Ledger_Service SHALL 确保每笔交易的原子性
5. FOR ALL 并发交易，THE System SHALL 保证账户余额的最终一致性

### Requirement 11: 数据迁移兼容性

**User Story:** 作为系统维护者，我需要确保系统升级后原有数据仍然可用，以便平滑过渡到新系统。

#### Acceptance Criteria

1. THE System SHALL 将现有 users 表的数据迁移到 participants 表
2. THE System SHALL 保持原有 User 模型和接口的可用性
3. WHEN 旧版客户端使用原有接口，THE System SHALL 正常处理请求
4. THE System SHALL 支持新旧接口共存
5. THE System SHALL 在数据库中保留 users 表以支持旧版接口

### Requirement 12: 错误处理和日志

**User Story:** 作为系统维护者，我需要清晰的错误信息和日志记录，以便快速定位和解决问题。

#### Acceptance Criteria

1. WHEN 业务异常发生，THE System SHALL 返回结构化的错误响应，包含 error_code 和 message
2. THE System SHALL 记录所有交易操作的日志，包括成功和失败的交易
3. THE System SHALL 记录账户余额变更的详细信息
4. THE System SHALL 记录活动状态验证的结果
5. WHEN 系统内部错误发生，THE System SHALL 记录完整的错误堆栈信息
6. THE System SHALL 使用结构化日志格式便于日志分析

### Requirement 13: API 路由注册

**User Story:** 作为系统，我需要注册所有新的 API 路由，以便客户端可以访问活动管理和参与者管理功能。

#### Acceptance Criteria

1. THE System SHALL 在主应用中注册 events 路由
2. THE System SHALL 在主应用中注册 participants 路由
3. THE System SHALL 保持原有 recharge、payment 和 balance 路由的可用性
4. THE System SHALL 为所有路由提供 OpenAPI 文档
5. THE System SHALL 为所有路由应用签名验证中间件

### Requirement 14: 金额单位转换

**User Story:** 作为系统，我需要正确处理金额单位转换，以便确保数据存储和 API 交互的一致性。

#### Acceptance Criteria

1. THE System SHALL 以"分"为单位存储所有金额到数据库
2. THE System SHALL 以"元"为单位接收 API 请求中的金额
3. THE System SHALL 以"元"为单位返回 API 响应中的金额
4. THE System SHALL 使用四舍五入方式将元转换为分
5. THE System SHALL 使用除以 100 的方式将分转换为元
6. FOR ALL 金额转换，THE System SHALL 确保精度不丢失

### Requirement 15: 输入验证

**User Story:** 作为系统，我需要验证所有输入数据，以便防止无效数据导致的错误和安全问题。

#### Acceptance Criteria

1. WHEN 接收 card_uid，THE System SHALL 验证其为十六进制格式
2. WHEN 接收金额，THE System SHALL 验证其为正数
3. WHEN 接收活动时间，THE System SHALL 验证结束时间晚于开始时间
4. WHEN 接收活动状态，THE System SHALL 验证其为有效的枚举值
5. WHEN 接收参与者状态，THE System SHALL 验证其为有效的枚举值
6. THE System SHALL 对所有字符串字段验证长度限制
7. IF 输入验证失败，THEN THE System SHALL 返回错误码 VALIDATION_ERROR 和具体的验证错误信息
