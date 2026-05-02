# 账本模式快速参考

## 核心概念

### 账本追加模式（Ledger Append-Only Mode）

- 所有交易都是追加记录，不可修改
- 每条记录包含交易前后余额
- 形成完整的审计链

### 金额单位

- **数据库存储**：INT，单位为分（cents）
- **API接口**：float，单位为元（yuan）
- **内部转换**：`yuan_to_cents = int(round(yuan * 100))`

## 核心服务

### LedgerService

账本服务，负责所有余额变更操作。

```python
from services.ledger_service import LedgerService

ledger_service = LedgerService(db_session)

# 追加贷方记录（增加余额）
entry = ledger_service.append_credit(
    uid="A1B2C3D4",
    amount_yuan=50.0,
    transaction_type="recharge",
    remark="现金充值"
)

# 追加借方记录（减少余额）
entry = ledger_service.append_debit(
    uid="A1B2C3D4",
    amount_yuan=25.0,
    transaction_type="pay",
    merchant_id="MERCHANT001",
    remark="购买商品"
)

# 验证账本完整性
is_valid, message = ledger_service.verify_balance_integrity(uid="A1B2C3D4")
```

### TransactionService

交易服务，使用 LedgerService 实现。

```python
from services.transaction_service import TransactionService

transaction_service = TransactionService(db_session)

# 处理支付
result = transaction_service.process_payment(
    uid="A1B2C3D4",
    amount_yuan=25.0,
    merchant_id="MERCHANT001",
    remark="购买商品"
)

# 处理充值
result = transaction_service.process_recharge(
    uid="A1B2C3D4",
    amount_yuan=50.0,
    operator_id="ADMIN001",
    remark="现金充值"
)

# 获取交易历史
history = transaction_service.get_transaction_history(
    uid="A1B2C3D4",
    limit=20,
    offset=0
)
```

### UserService

用户服务，适配新的金额单位。

```python
from services.user_service import UserService

user_service = UserService(db_session)

# 获取余额（分）
balance_cents = user_service.get_balance(uid="A1B2C3D4")

# 获取余额（元）
balance_yuan = user_service.get_balance_yuan(uid="A1B2C3D4")

# 创建用户
user = user_service.create_user(uid="A1B2C3D4", initial_balance=0)
```

## 数据模型

### Transaction

```python
class Transaction(Base):
    id: int                          # 交易ID
    uid: str                         # 用户UID
    card_uid: str                    # 卡片UID（与uid兼容）
    type: str                        # 交易类型
    amount: int                      # 交易金额（分）
    balance_before: int              # 交易前余额（分）
    balance_after: int               # 交易后余额（分）
    merchant_id: Optional[str]       # 商户ID
    related_txn_id: Optional[int]    # 关联交易ID
    remark: Optional[str]            # 备注
    operator_id: Optional[str]       # 操作员ID
    created_at: datetime             # 创建时间
```

### User

```python
class User(Base):
    id: int                          # 用户ID
    uid: str                         # 用户UID（唯一）
    balance: int                     # 账户余额（分）
    created_at: datetime             # 创建时间
```

## 交易类型

| 类型 | 说明 | 余额变化 | 状态 |
|------|------|----------|------|
| `recharge` | 充值 | 增加 | ✅ 已实现 |
| `pay` | 支付 | 减少 | ✅ 已实现 |
| `refund` | 退款 | 增加 | 🔜 预留 |
| `adjust` | 调整 | 增加/减少 | 🔜 预留 |
| `issue` | 发卡 | 增加 | 🔜 预留 |
| `void` | 作废 | 减少 | 🔜 预留 |
| `expire` | 过期 | 减少 | 🔜 预留 |

## API 接口

### POST /recharge

充值接口。

**请求：**

```json
{
  "uid": "A1B2C3D4",
  "amount": 50.00,
  "timestamp": 1234567890,
  "signature": "abc123...",
  "operator_id": "ADMIN001",
  "remark": "现金充值"
}
```

**响应：**

```json
{
  "success": true,
  "new_balance": 150.50,
  "transaction_id": 12346,
  "balance_before": 100.50
}
```

### POST /pay

支付接口。

**请求：**

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

**响应：**

```json
{
  "success": true,
  "new_balance": 75.50,
  "transaction_id": 12345,
  "balance_before": 100.50
}
```

### GET /balance

余额查询接口。

**请求：**

```
GET /balance?uid=A1B2C3D4&timestamp=1234567890&signature=abc123...
```

**响应：**

```json
{
  "balance": 100.50
}
```

## 事务边界

### 支付流程

```
1. 开始数据库事务
2. 获取用户行锁（SELECT ... FOR UPDATE）
3. 验证余额充足
4. 计算新余额
5. 更新用户余额
6. 创建交易记录
7. 提交事务
8. 失败则回滚
```

### 充值流程

```
1. 开始数据库事务
2. 获取用户行锁（SELECT ... FOR UPDATE）
3. 计算新余额
4. 更新用户余额
5. 创建交易记录
6. 提交事务
7. 失败则回滚
```

## 异常处理

### 业务异常

| 异常类型 | 错误代码 | 说明 |
|---------|---------|------|
| `UserNotFoundError` | `USER_NOT_FOUND` | 用户不存在 |
| `InsufficientFundsError` | `INSUFFICIENT_FUNDS` | 余额不足 |
| `InvalidTransactionError` | `INVALID_TRANSACTION` | 无效交易 |
| `TransactionNotFoundError` | `TRANSACTION_NOT_FOUND` | 交易不存在 |
| `MerchantNotFoundError` | `MERCHANT_NOT_FOUND` | 商户不存在 |
| `MerchantInactiveError` | `MERCHANT_INACTIVE` | 商户未激活 |

### 错误响应格式

```json
{
  "error_code": "INSUFFICIENT_FUNDS",
  "message": "Account balance (50.00 yuan) is insufficient for payment amount (100.00 yuan)"
}
```

## 数据库查询

### 查询用户交易历史

```sql
SELECT 
    id,
    type,
    amount / 100.0 AS amount_yuan,
    balance_before / 100.0 AS balance_before_yuan,
    balance_after / 100.0 AS balance_after_yuan,
    merchant_id,
    remark,
    created_at
FROM transactions
WHERE uid = 'A1B2C3D4'
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

### 验证余额一致性

```sql
SELECT 
    u.uid,
    u.balance / 100.0 AS current_balance_yuan,
    t.balance_after / 100.0 AS last_txn_balance_yuan,
    CASE 
        WHEN u.balance = t.balance_after THEN 'OK'
        ELSE 'MISMATCH'
    END AS status
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

### 统计交易金额

```sql
-- 总充值金额
SELECT 
    uid,
    SUM(amount) / 100.0 AS total_recharge_yuan
FROM transactions
WHERE type = 'recharge'
GROUP BY uid;

-- 总支付金额
SELECT 
    uid,
    SUM(amount) / 100.0 AS total_payment_yuan
FROM transactions
WHERE type = 'pay'
GROUP BY uid;
```

## 最佳实践

### 1. 使用 LedgerService

所有余额变更必须通过 LedgerService 进行，不要直接修改 User.balance。

```python
# ✅ 正确
ledger_service.append_credit(uid, amount_yuan, "recharge")

# ❌ 错误
user.balance += amount_cents
db.commit()
```

### 2. 事务管理

使用 SQLAlchemy 的事务管理，失败自动回滚。

```python
try:
    # 业务逻辑
    ledger_service.append_debit(uid, amount_yuan, "pay")
    # 自动提交
except Exception as e:
    # 自动回滚
    logger.error(f"Transaction failed: {e}")
    raise
```

### 3. 金额转换

API 层使用元，内部使用分。

```python
# API 接收金额（元）
amount_yuan = request.amount  # 25.00

# 内部转换为分
amount_cents = int(round(amount_yuan * 100))  # 2500

# 响应转换回元
response_amount = amount_cents / 100.0  # 25.00
```

### 4. 并发控制

LedgerService 自动使用行锁，无需额外处理。

```python
# 自动获取行锁
user = db.query(User).filter(User.uid == uid).with_for_update().first()
```

### 5. 错误处理

捕获业务异常，返回标准错误响应。

```python
try:
    result = transaction_service.process_payment(uid, amount_yuan)
except InsufficientFundsError as e:
    return JSONResponse(
        status_code=400,
        content={
            "error_code": e.error_code,
            "message": e.message
        }
    )
```

## 常见问题

### Q: 为什么使用分而不是元？

A: 避免浮点数精度问题。金融场景必须使用整数或定点数。

### Q: 如何验证账本完整性？

A: 使用 `LedgerService.verify_balance_integrity()` 方法。

### Q: 失败的交易会产生流水吗？

A: 不会。失败的交易会自动回滚，不会产生任何记录。

### Q: 如何实现退款？

A: 使用 `append_credit()` 方法，`transaction_type="refund"`，`related_txn_id` 指向原交易。

### Q: 如何处理并发支付？

A: LedgerService 使用行锁（SELECT ... FOR UPDATE），自动处理并发。

### Q: 如何查询某个时间点的余额？

A: 查询该时间点之前的最后一条交易记录的 `balance_after`。

```sql
SELECT balance_after / 100.0 AS balance_yuan
FROM transactions
WHERE uid = 'A1B2C3D4' AND created_at <= '2024-01-15 10:30:00'
ORDER BY created_at DESC, id DESC
LIMIT 1;
```

## 迁移检查清单

- [ ] 备份数据库
- [ ] 执行迁移脚本
- [ ] 验证数据完整性
- [ ] 测试充值接口
- [ ] 测试支付接口
- [ ] 测试余额查询接口
- [ ] 测试并发场景
- [ ] 验证账本完整性
- [ ] 更新 Android 客户端（如需要）
- [ ] 监控生产环境

## 相关文档

- [完整升级文档](LEDGER_MODE_UPGRADE.md)
- [数据库迁移脚本](migrations/001_upgrade_to_ledger_mode.sql)
- [API 文档](README.md)
