# 账本追加模式升级文档

## 概述

本次升级将 NFC 校园钱包系统从"简单余额模型"升级为"账本追加模式"（Ledger Append-Only Mode），实现可审计的账本内核。

## 升级内容

### 1. 数据库升级

#### 新增字段

在 `transactions` 表中新增以下字段：

- `balance_before` (INT): 交易前余额（分）
- `balance_after` (INT): 交易后余额（分）- 已存在，类型改为 INT
- `related_txn_id` (INT, NULL): 关联交易ID（用于退款、调整）
- `remark` (VARCHAR(255), NULL): 交易备注
- `operator_id` (VARCHAR(64), NULL): 操作员ID（预留）
- `card_uid` (VARCHAR(32), NULL): 卡片UID（与uid兼容）

#### 交易类型扩展

`type` 字段从 ENUM 改为 VARCHAR(20)，支持以下类型：

- `recharge`: 充值
- `pay`: 支付
- `refund`: 退款（预留）
- `adjust`: 调整（预留）
- `issue`: 发卡（预留）
- `void`: 作废（预留）
- `expire`: 过期（预留）

#### 金额单位变更

所有金额字段从 `DECIMAL(10,2)`（元）改为 `INT`（分）：

- `transactions.amount`: INT（分）
- `transactions.balance_before`: INT（分）
- `transactions.balance_after`: INT（分）
- `users.balance`: INT（分）

#### 执行迁移

```bash
# 1. 备份数据库
mysqldump -u root -p nfc_wallet > backup_before_ledger_upgrade.sql

# 2. 执行迁移脚本
mysql -u root -p nfc_wallet < migrations/001_upgrade_to_ledger_mode.sql
```

### 2. 核心服务层

#### LedgerService（新增）

账本服务是核心组件，负责所有余额变更操作：

**核心方法：**

- `append_credit()`: 追加贷方记录（增加余额）
  - 适用于：recharge、refund、adjust（增加）
  
- `append_debit()`: 追加借方记录（减少余额）
  - 适用于：pay、void、expire、adjust（减少）

- `verify_balance_integrity()`: 验证账本完整性

**特性：**

- 使用 `SELECT ... FOR UPDATE` 行锁保证并发安全
- 每条交易记录包含 `balance_before` 和 `balance_after`
- 所有操作在数据库事务内完成
- 失败自动回滚，不会产生错误流水

#### TransactionService（重构）

交易服务使用 LedgerService 实现：

- `process_payment()`: 处理支付，调用 `ledger_service.append_debit()`
- `process_recharge()`: 处理充值，调用 `ledger_service.append_credit()`
- `get_transaction_history()`: 获取交易历史（支持分页）
- `get_leaderboard()`: 生成排行榜

#### UserService（更新）

用户服务适配新的金额单位：

- `get_balance()`: 返回余额（分）
- `get_balance_yuan()`: 返回余额（元）
- `create_user()`: 创建用户，初始余额为 0 分

### 3. 接口兼容性

#### 保持兼容的接口

所有现有接口保持兼容，金额单位仍为元：

- `POST /recharge`: 充值接口
  - 请求：`amount` 单位为元
  - 响应：`new_balance` 单位为元
  - 新增：`balance_before` 字段（可选）

- `POST /pay`: 支付接口
  - 请求：`amount` 单位为元
  - 响应：`new_balance` 单位为元
  - 新增：`balance_before` 字段（可选）

- `GET /balance`: 余额查询接口
  - 响应：`balance` 单位为元

#### 新增字段

请求模型新增可选字段：

- `PaymentRequest.remark`: 交易备注
- `RechargeRequest.operator_id`: 操作员ID
- `RechargeRequest.remark`: 交易备注

响应模型新增字段：

- `TransactionResponse.balance_before`: 交易前余额（元）

### 4. 事务边界说明

#### 支付流程

```python
# 1. 开始数据库事务（自动）
# 2. 获取用户行锁：SELECT ... FOR UPDATE
# 3. 验证余额充足
# 4. 计算新余额
# 5. 更新用户余额
# 6. 创建交易记录（包含 balance_before 和 balance_after）
# 7. 提交事务
# 8. 失败则回滚，不产生错误流水
```

#### 充值流程

```python
# 1. 开始数据库事务（自动）
# 2. 获取用户行锁：SELECT ... FOR UPDATE
# 3. 计算新余额
# 4. 更新用户余额
# 5. 创建交易记录（包含 balance_before 和 balance_after）
# 6. 提交事务
# 7. 失败则回滚，不产生错误流水
```

### 5. 异常处理

#### 新增异常类型

- `InvalidTransactionError`: 无效交易异常
- `TransactionNotFoundError`: 交易不存在异常

#### 统一异常处理

所有业务异常继承自 `BusinessException`，包含：

- `error_code`: 错误代码
- `message`: 错误消息

路由层统一捕获并返回标准错误响应：

```json
{
  "error_code": "INSUFFICIENT_FUNDS",
  "message": "Account balance (50.00 yuan) is insufficient for payment amount (100.00 yuan)"
}
```

## 升级优势

### 1. 可审计性

- 每条交易记录包含交易前后余额
- 形成完整的审计链
- 可追溯任意时刻的余额状态

### 2. 数据完整性

- 账本追加模式，记录不可修改
- 余额计算可验证
- 提供 `verify_balance_integrity()` 方法验证账本完整性

### 3. 并发安全

- 使用行锁（SELECT ... FOR UPDATE）
- 防止并发修改导致的余额错误
- 事务隔离保证一致性

### 4. 精确计算

- 使用整数（分）存储金额
- 避免浮点数精度问题
- 适合金融场景

### 5. 扩展性

- 预留字段支持未来功能：
  - `related_txn_id`: 支持退款、调整
  - `operator_id`: 支持后台操作审计
  - `remark`: 支持交易备注
- 交易类型可扩展：refund、adjust、issue、void、expire

## 验证方法

### 1. 验证账本完整性

```python
from services.ledger_service import LedgerService

ledger_service = LedgerService(db_session)
is_valid, message = ledger_service.verify_balance_integrity(uid="A1B2C3D4")
print(f"Integrity check: {is_valid}, {message}")
```

### 2. 验证余额计算

```sql
-- 查询用户的所有交易记录
SELECT 
    id,
    type,
    amount / 100.0 AS amount_yuan,
    balance_before / 100.0 AS balance_before_yuan,
    balance_after / 100.0 AS balance_after_yuan,
    created_at
FROM transactions
WHERE uid = 'A1B2C3D4'
ORDER BY created_at, id;

-- 验证最后一条交易的余额与用户当前余额一致
SELECT 
    u.balance / 100.0 AS user_balance_yuan,
    t.balance_after / 100.0 AS last_txn_balance_yuan
FROM users u
LEFT JOIN (
    SELECT uid, balance_after
    FROM transactions
    WHERE uid = 'A1B2C3D4'
    ORDER BY created_at DESC, id DESC
    LIMIT 1
) t ON u.uid = t.uid
WHERE u.uid = 'A1B2C3D4';
```

### 3. 测试并发安全

```python
import concurrent.futures
from services.transaction_service import TransactionService

def test_concurrent_payment(uid, amount):
    try:
        service = TransactionService(db_session)
        result = service.process_payment(uid=uid, amount_yuan=amount)
        return f"Success: {result.transaction_id}"
    except Exception as e:
        return f"Failed: {str(e)}"

# 并发执行10次支付
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(test_concurrent_payment, "A1B2C3D4", 10.0) for _ in range(10)]
    results = [f.result() for f in futures]
    print(results)
```

## 注意事项

### 1. 数据迁移

- 必须先备份数据库
- 现有数据需要转换金额单位（元 → 分）
- 需要计算并填充 `balance_before` 字段

### 2. 兼容性

- 接口保持兼容，金额单位仍为元
- 内部使用分为单位，避免精度问题
- 响应中新增 `balance_before` 字段（可选）

### 3. 性能

- 行锁可能影响高并发性能
- 建议监控数据库锁等待情况
- 可考虑使用连接池优化

### 4. 扩展

- 预留字段为未来功能做准备
- 暂不实现退款、调整等功能
- 暂不实现活动、摊位、商品等功能

## 下一步计划

本次升级完成后，系统具备了可审计的账本内核。未来可以在此基础上扩展：

1. **退款功能**：使用 `related_txn_id` 关联原交易
2. **余额调整**：使用 `adjust` 类型和 `operator_id` 审计
3. **活动系统**：基于账本模式实现活动充值、消费
4. **后台管理**：基于 `operator_id` 实现操作审计
5. **报表统计**：基于完整账本生成各类报表

## 总结

本次升级将项目从"钱包 demo"升级为"可审计账本内核"，为未来的功能扩展打下坚实基础。所有交易都有完整的审计链，余额计算可验证，并发安全有保障。
