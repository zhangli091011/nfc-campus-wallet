# Implementation Plan: NFC Campus Event Quota System

## Overview

本实现计划将"学校单场活动额度系统"升级项目分解为可执行的编码任务。系统已完成数据库迁移、ORM 模型、Pydantic Schemas 和 EventService 的实现。本计划专注于实现剩余的服务层、路由层和测试。

**实现语言**：Python (FastAPI + SQLAlchemy)

**已完成组件**：
- ✅ 数据库迁移 SQL
- ✅ ORM 模型（Event, Participant, Account）
- ✅ Pydantic Schemas（Event, Participant, Account）
- ✅ EventService

**待实现组件**：
- ParticipantService
- AccountService
- LedgerService（扩展支持 Account 模型）
- TransactionService（扩展支持活动模式）
- Transaction Schema（扩展支持活动模式）
- 路由层（events, participants, recharge, payment, balance）
- 主应用更新
- 测试（example-based 和 property-based）

## Tasks

- [x] 1. 实现 ParticipantService 服务
  - 创建 `services/participant_service.py` 文件
  - 实现参与者创建、查询、更新功能
  - 实现卡片绑定和通过 card_uid 查询功能
  - 实现参与者列表查询（支持状态过滤和分页）
  - 添加 card_uid 格式验证（十六进制）
  - 添加 card_uid 唯一性验证
  - 添加参与者状态验证
  - 实现异常处理（ParticipantNotFoundError, CardAlreadyBoundError, ParticipantBlockedError）
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [ ]* 1.1 为 ParticipantService 编写单元测试
  - 测试创建参与者成功场景
  - 测试通过 card_uid 查询参与者
  - 测试绑定卡片成功场景
  - 测试分页查询参与者列表
  - 测试参与者不存在异常
  - 测试卡片已绑定异常
  - _Requirements: 3.1, 3.4, 3.5, 3.6_

- [ ]* 1.2 为 ParticipantService 编写属性测试
  - **Property 4: Card UID 格式验证**
  - **Validates: Requirements 3.2, 15.1**
  - 使用 hypothesis 生成随机字符串（包括有效和无效的十六进制字符串）
  - 验证系统正确接受有效的十六进制 card_uid
  - 验证系统正确拒绝无效的 card_uid
  - _Requirements: 3.2, 15.1_

- [ ]* 1.3 为 ParticipantService 编写属性测试
  - **Property 5: Card UID 唯一性**
  - **Validates: Requirements 3.3**
  - 使用 hypothesis 生成随机的参与者数据
  - 尝试创建具有相同 card_uid 的两个参与者
  - 验证系统拒绝第二个参与者的创建
  - _Requirements: 3.3_

- [x] 2. 实现 AccountService 服务
  - 创建 `services/account_service.py` 文件
  - 实现 get_or_create_account 方法（自动创建账户）
  - 实现 get_account 方法（查询账户）
  - 实现 get_account_balance 方法（查询余额，返回分）
  - 实现 list_participant_accounts 方法（查询参与者所有账户）
  - 实现 list_event_accounts 方法（查询活动所有账户，支持分页）
  - 确保账户唯一性约束（participant_id, event_id）
  - 实现异常处理（AccountNotFoundError, DuplicateAccountError）
  - _Requirements: 4.1, 4.2, 4.3, 4.6_

- [ ]* 2.1 为 AccountService 编写单元测试
  - 测试 get_or_create_account 自动创建新账户
  - 测试 get_or_create_account 返回已存在账户
  - 测试 get_account_balance 查询余额
  - 测试 list_participant_accounts 查询参与者所有账户
  - 测试账户不存在异常
  - _Requirements: 4.1, 4.2, 4.3, 4.6_

- [ ]* 2.2 为 AccountService 编写属性测试
  - **Property 6: 账户唯一性**
  - **Validates: Requirements 4.2**
  - 使用 hypothesis 生成随机的 participant_id 和 event_id
  - 尝试为同一参与者和活动创建多个账户
  - 验证系统确保只有一个账户存在
  - _Requirements: 4.2_

- [ ]* 2.3 为 AccountService 编写属性测试
  - **Property 8: 金额单位转换 round-trip**
  - **Validates: Requirements 4.4, 4.5, 14.4, 14.5, 14.6**
  - 使用 hypothesis 生成随机金额（元，最多 2 位小数）
  - 执行 yuan → cents → yuan 的 round-trip 转换
  - 验证转换后的值与原始值相等（允许 0.01 元误差）
  - _Requirements: 4.4, 4.5, 14.4, 14.5, 14.6_

- [x] 3. 扩展 LedgerService 支持 Account 模型
  - 打开 `services/ledger_service.py` 文件
  - 添加 _acquire_account_lock 方法（使用 SELECT FOR UPDATE 锁定账户）
  - 添加 append_credit_to_account 方法（贷方记录到 Account）
  - 添加 append_debit_from_account 方法（借方记录从 Account）
  - 在交易记录中添加 event_id, participant_id, account_id 字段
  - 确保事务内完成：锁定账户 → 验证余额 → 更新余额 → 创建交易记录 → 提交
  - 保持对原有 User 模型的支持
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [ ]* 3.1 为 LedgerService 扩展编写单元测试
  - 测试 append_credit_to_account 贷方记录成功
  - 测试 append_debit_from_account 借方记录成功
  - 测试 append_debit_from_account 余额不足被拒绝
  - 测试事务失败时回滚
  - 测试账户锁定机制
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ]* 3.2 为 LedgerService 编写属性测试
  - **Property 7: 账户余额非负不变量**
  - **Validates: Requirements 4.7, 8.3**
  - 使用 hypothesis 生成随机的借方操作（包括会导致余额为负的操作）
  - 验证系统拒绝会导致余额为负的操作
  - 验证所有成功的操作后账户余额 >= 0
  - _Requirements: 4.7, 8.3_

- [ ]* 3.3 为 LedgerService 编写属性测试
  - **Property 9: 交易余额计算正确性**
  - **Validates: Requirements 8.7**
  - 使用 hypothesis 生成随机的贷方和借方交易
  - 验证贷方交易：balance_after = balance_before + amount
  - 验证借方交易：balance_after = balance_before - amount
  - _Requirements: 8.7_

- [ ]* 3.4 为 LedgerService 编写并发安全集成测试
  - 创建测试场景：多个线程同时操作同一账户
  - 验证所有交易串行化执行
  - 验证最终余额正确
  - 验证没有交易丢失
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 4. 扩展 TransactionService 支持活动模式
  - 打开 `services/transaction_service.py` 文件
  - 添加 process_event_recharge 方法（活动模式充值）
  - 添加 process_event_payment 方法（活动模式消费）
  - 添加 get_event_transaction_history 方法（查询活动交易历史）
  - 实现流程：验证活动 → 查找参与者 → 获取或创建账户 → 调用 LedgerService
  - 保持对原有 uid 模式的支持
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

- [ ]* 4.1 为 TransactionService 扩展编写单元测试
  - 测试 process_event_recharge 活动模式充值成功
  - 测试 process_event_payment 活动模式消费成功
  - 测试参与者不存在异常
  - 测试活动不允许充值异常
  - 测试活动不允许消费异常
  - 测试余额不足异常
  - 测试 get_event_transaction_history 查询交易历史
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ]* 4.2 为 TransactionService 编写属性测试
  - **Property 10: 充值金额验证**
  - **Validates: Requirements 5.8, 15.2**
  - 使用 hypothesis 生成随机金额（包括正数、零和负数）
  - 验证系统接受正数金额
  - 验证系统拒绝零和负数金额
  - _Requirements: 5.8, 15.2_

- [ ]* 4.3 为 TransactionService 编写属性测试
  - **Property 12: 交易响应完整性**
  - **Validates: Requirements 5.5**
  - 使用 hypothesis 生成随机的充值和消费交易
  - 验证所有成功的交易响应包含：success, new_balance, transaction_id, balance_before
  - 验证响应字段类型正确
  - _Requirements: 5.5_

- [ ]* 4.4 为 TransactionService 编写集成测试
  - 测试完整充值流程（活动验证 → 参与者查询 → 账户创建 → 余额更新）
  - 测试完整消费流程（活动验证 → 参与者查询 → 账户查询 → 余额扣减）
  - 验证交易记录正确创建
  - 验证余额正确更新
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 5. 扩展 Transaction Schema 支持活动模式
  - 打开 `schemas/transaction.py` 文件
  - 在 RechargeRequest 中添加可选字段：event_id, card_uid
  - 在 PaymentRequest 中添加可选字段：event_id, card_uid
  - 在 BalanceRequest 中添加可选字段：event_id, card_uid
  - 添加字段验证：event_id 和 card_uid 必须同时存在或同时不存在
  - 保持对原有 uid 字段的支持
  - _Requirements: 9.1, 9.2_

- [x] 6. Checkpoint - 确保所有服务层测试通过
  - 运行所有服务层单元测试
  - 运行所有服务层属性测试
  - 运行所有服务层集成测试
  - 确保测试覆盖率 >= 80%
  - 如有问题，询问用户

- [x] 7. 实现 Events 路由
  - 创建 `routes/events.py` 文件
  - 实现 POST /events 端点（创建活动）
  - 实现 GET /events 端点（活动列表，支持状态过滤和分页）
  - 实现 GET /events/{id} 端点（活动详情）
  - 实现 PATCH /events/{id} 端点（更新活动）
  - 使用 EventCreate, EventUpdate, EventResponse, EventListResponse schemas
  - 添加请求验证和错误处理
  - 添加 OpenAPI 文档注释
  - _Requirements: 1.1, 1.3, 1.4, 1.5, 13.1, 13.4_

- [ ]* 7.1 为 Events 路由编写单元测试
  - 测试 POST /events 创建活动成功
  - 测试 GET /events 查询活动列表
  - 测试 GET /events/{id} 查询活动详情
  - 测试 PATCH /events/{id} 更新活动
  - 测试活动不存在返回 404
  - 测试无效输入返回 400
  - _Requirements: 1.1, 1.3, 1.4, 1.5_

- [ ]* 7.2 为 Events 路由编写属性测试
  - **Property 1: 活动时间验证**
  - **Validates: Requirements 1.2, 15.3**
  - 使用 hypothesis 生成随机的 start_time 和 end_time
  - 验证系统拒绝 end_time <= start_time 的活动创建
  - 验证系统接受 end_time > start_time 的活动创建
  - _Requirements: 1.2, 15.3_

- [ ]* 7.3 为 Events 路由编写属性测试
  - **Property 2: 活动充值验证**
  - **Validates: Requirements 2.1, 2.2, 2.3**
  - 使用 hypothesis 生成随机的活动状态、时间和 recharge_enabled 标志
  - 验证充值验证逻辑的正确性（status=active AND 时间范围内 AND recharge_enabled=true）
  - _Requirements: 2.1, 2.2, 2.3_

- [ ]* 7.4 为 Events 路由编写属性测试
  - **Property 3: 活动消费验证**
  - **Validates: Requirements 2.4, 2.5, 2.6**
  - 使用 hypothesis 生成随机的活动状态、时间和 consume_enabled 标志
  - 验证消费验证逻辑的正确性（status=active AND 时间范围内 AND consume_enabled=true）
  - _Requirements: 2.4, 2.5, 2.6_

- [x] 8. 实现 Participants 路由
  - 创建 `routes/participants.py` 文件
  - 实现 POST /participants 端点（创建参与者）
  - 实现 GET /participants 端点（参与者列表，支持状态过滤和分页）
  - 实现 GET /participants/{id} 端点（参与者详情）
  - 实现 PATCH /participants/{id} 端点（更新参与者）
  - 实现 POST /participants/bind-card 端点（绑定卡片）
  - 实现 GET /participants/by-card/{card_uid} 端点（通过卡片查询）
  - 使用 ParticipantCreate, ParticipantUpdate, ParticipantResponse, ParticipantListResponse schemas
  - 添加请求验证和错误处理
  - 添加 OpenAPI 文档注释
  - _Requirements: 3.1, 3.4, 3.5, 3.6, 13.2, 13.4_

- [ ]* 8.1 为 Participants 路由编写单元测试
  - 测试 POST /participants 创建参与者成功
  - 测试 GET /participants 查询参与者列表
  - 测试 GET /participants/{id} 查询参与者详情
  - 测试 PATCH /participants/{id} 更新参与者
  - 测试 POST /participants/bind-card 绑定卡片
  - 测试 GET /participants/by-card/{card_uid} 通过卡片查询
  - 测试参与者不存在返回 404
  - 测试卡片已绑定返回 400
  - _Requirements: 3.1, 3.4, 3.5, 3.6_

- [x] 9. 更新 Recharge 路由支持活动模式
  - 打开 `routes/recharge.py` 文件（如不存在则创建）
  - 实现 POST /recharge 端点
  - 添加请求模式判断逻辑：
    - 如果 request.event_id 和 request.card_uid 存在 → 活动模式
    - 如果 request.uid 存在 → 传统模式
  - 活动模式：调用 transaction_service.process_event_recharge()
  - 传统模式：调用 transaction_service.process_recharge()
  - 使用扩展后的 RechargeRequest schema
  - 添加错误处理（ParticipantNotFoundError, EventInactiveError）
  - 添加 OpenAPI 文档注释
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 13.3, 13.4_

- [ ]* 9.1 为 Recharge 路由编写单元测试
  - 测试活动模式充值成功
  - 测试传统模式充值成功
  - 测试参与者不存在返回 400
  - 测试活动不允许充值返回 400
  - 测试无效金额返回 400
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_

- [x] 10. 更新 Payment 路由支持活动模式
  - 打开 `routes/payment.py` 文件（如不存在则创建）
  - 实现 POST /pay 端点
  - 添加请求模式判断逻辑：
    - 如果 request.event_id 和 request.card_uid 存在 → 活动模式
    - 如果 request.uid 存在 → 传统模式
  - 活动模式：调用 transaction_service.process_event_payment()
  - 传统模式：调用 transaction_service.process_payment()
  - 使用扩展后的 PaymentRequest schema
  - 添加错误处理（ParticipantNotFoundError, EventInactiveError, InsufficientFundsError）
  - 添加 OpenAPI 文档注释
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 13.3, 13.4_

- [ ]* 10.1 为 Payment 路由编写单元测试
  - 测试活动模式消费成功
  - 测试传统模式消费成功
  - 测试参与者不存在返回 400
  - 测试活动不允许消费返回 400
  - 测试余额不足返回 400
  - 测试无效金额返回 400
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9_

- [x] 11. 更新 Balance 路由支持活动模式
  - 打开 `routes/balance.py` 文件（如不存在则创建）
  - 实现 GET /balance 端点
  - 添加查询参数模式判断逻辑：
    - 如果 event_id 和 card_uid 存在 → 活动模式
    - 如果 uid 存在 → 传统模式
  - 活动模式：通过 card_uid 查找参与者 → 查询账户余额
  - 传统模式：通过 uid 查询用户余额
  - 使用扩展后的 BalanceRequest schema
  - 添加错误处理（ParticipantNotFoundError, EventNotFoundError）
  - 添加 OpenAPI 文档注释
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 13.3, 13.4_

- [ ]* 11.1 为 Balance 路由编写单元测试
  - 测试活动模式余额查询成功
  - 测试传统模式余额查询成功
  - 测试参与者不存在返回 400
  - 测试活动不存在返回 400
  - 测试账户不存在返回余额 0
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 12. 更新主应用注册新路由
  - 打开 `app/main.py` 文件
  - 导入新的路由模块：events, participants
  - 使用 app.include_router() 注册 events 路由
  - 使用 app.include_router() 注册 participants 路由
  - 确保 recharge, payment, balance 路由已注册
  - 为所有路由应用签名验证中间件
  - 为所有路由应用请求日志中间件
  - _Requirements: 13.1, 13.2, 13.3, 13.5_

- [ ]* 12.1 为主应用编写集成测试
  - 测试所有路由已正确注册
  - 测试签名验证中间件应用到所有路由
  - 测试请求日志中间件应用到所有路由
  - 测试 OpenAPI 文档生成正确
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 13. Checkpoint - 确保所有路由层测试通过
  - 运行所有路由层单元测试
  - 运行所有路由层属性测试
  - 运行所有路由层集成测试
  - 确保测试覆盖率 >= 80%
  - 如有问题，询问用户

- [ ]* 14. 编写字符串长度验证属性测试
  - **Property 11: 字符串长度验证**
  - **Validates: Requirements 15.6**
  - 使用 hypothesis 生成不同长度的随机字符串
  - 测试所有字符串字段的长度限制：
    - Event.name (max 255)
    - Participant.name (max 100)
    - Participant.class_name (max 100)
    - Participant.student_no (max 50)
    - Participant.card_uid (max 32)
  - 验证系统拒绝超过长度限制的输入
  - _Requirements: 15.6_

- [ ]* 15. 编写端到端集成测试
  - 测试完整的活动创建 → 参与者创建 → 充值 → 消费 → 余额查询流程
  - 测试多个参与者在同一活动下的交易
  - 测试同一参与者在多个活动下的交易
  - 测试活动状态变更对交易的影响
  - 测试并发场景下的交易安全性
  - _Requirements: 1.1, 3.1, 5.1, 6.1, 7.1_

- [x] 16. 最终 Checkpoint - 确保所有测试通过
  - 运行所有单元测试
  - 运行所有属性测试（每个属性至少 100 次迭代）
  - 运行所有集成测试
  - 生成测试覆盖率报告
  - 确保代码覆盖率 >= 80%
  - 确保分支覆盖率 >= 75%
  - 如有问题，询问用户

## Notes

- 任务标记 `*` 的为可选测试任务，可以跳过以加快 MVP 开发
- 每个任务都引用了具体的需求编号，便于追溯
- Checkpoint 任务确保增量验证
- 属性测试验证通用的正确性属性
- 单元测试验证具体的业务场景和边界情况
- 集成测试验证完整的业务流程和组件集成
- 所有金额在数据库中以"分"为单位存储，在 API 中以"元"为单位交互
- 使用 Ledger Mode 确保所有交易的原子性和一致性
- 使用 SELECT FOR UPDATE 行锁机制确保并发安全
