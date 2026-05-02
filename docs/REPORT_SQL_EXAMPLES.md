# 报表统计 SQL 查询示例

本文档展示报表系统中各项统计指标的 SQL 查询逻辑。所有统计均基于 `transactions` 表（账本流水）。

## 📊 总览统计

### 1. 总发放额度
```sql
-- 统计所有 issue 类型交易的金额总和
SELECT COALESCE(SUM(amount), 0) as total_issued_cents
FROM transactions
WHERE type = 'issue'
  AND event_id = ?  -- 可选：按活动筛选
```

### 2. 总充值额
```sql
-- 统计所有 recharge 类型交易的金额总和
SELECT COALESCE(SUM(amount), 0) as total_recharged_cents
FROM transactions
WHERE type = 'recharge'
  AND event_id = ?  -- 可选：按活动筛选
```

### 3. 总消费额
```sql
-- 统计所有 pay 类型交易的金额总和
SELECT COALESCE(SUM(amount), 0) as total_consumed_cents
FROM transactions
WHERE type = 'pay'
  AND event_id = ?  -- 可选：按活动筛选
```

### 4. 总退款额
```sql
-- 统计所有 refund 类型交易的金额总和
SELECT COALESCE(SUM(amount), 0) as total_refunded_cents
FROM transactions
WHERE type = 'refund'
  AND event_id = ?  -- 可选：按活动筛选
```

### 5. 净消费额
```python
# 计算逻辑（Python）
net_consumed_cents = total_consumed_cents - total_refunded_cents
```

### 6. 总交易笔数
```sql
-- 统计所有交易记录数
SELECT COUNT(id) as total_transactions
FROM transactions
WHERE event_id = ?  -- 可选：按活动筛选
```

### 7. 参与者数量
```sql
-- 按活动统计
SELECT COUNT(DISTINCT participant_id) as participant_count
FROM accounts
WHERE event_id = ?

-- 全局统计
SELECT COUNT(id) as participant_count
FROM participants
```

### 8. 摊位数量
```sql
-- 统计摊位数量
SELECT COUNT(id) as booth_count
FROM booths
WHERE event_id = ?  -- 可选：按活动筛选
```

## 🏪 摊位维度统计

### 1. 摊位营业额
```sql
-- 统计每个摊位的 pay 类型交易总额
SELECT 
    b.id as booth_id,
    b.name as booth_name,
    b.class_name,
    COALESCE(SUM(t.amount), 0) as revenue_cents
FROM booths b
LEFT JOIN transactions t ON t.booth_id = b.id AND t.type = 'pay'
WHERE b.event_id = ?  -- 可选：按活动筛选
GROUP BY b.id, b.name, b.class_name
ORDER BY revenue_cents DESC
```

### 2. 摊位退款额
```sql
-- 统计每个摊位的 refund 类型交易总额
SELECT 
    booth_id,
    COALESCE(SUM(amount), 0) as refund_cents
FROM transactions
WHERE type = 'refund'
  AND booth_id IS NOT NULL
  AND event_id = ?  -- 可选：按活动筛选
GROUP BY booth_id
```

### 3. 摊位净收入
```python
# 计算逻辑（Python）
net_revenue_cents = revenue_cents - refund_cents
```

### 4. 摊位销量
```sql
-- 统计每个摊位的 pay 类型交易笔数
SELECT 
    booth_id,
    COUNT(id) as sales_count
FROM transactions
WHERE type = 'pay'
  AND booth_id IS NOT NULL
  AND event_id = ?  -- 可选：按活动筛选
GROUP BY booth_id
```

### 5. 摊位总成本
```sql
-- 基于商品成本价和销量计算
SELECT 
    t.booth_id,
    COALESCE(SUM(p.cost_price), 0) as total_cost_cents
FROM transactions t
JOIN products p ON p.id = t.product_id
WHERE t.type = 'pay'
  AND t.booth_id IS NOT NULL
  AND p.cost_price IS NOT NULL
  AND t.event_id = ?  -- 可选：按活动筛选
GROUP BY t.booth_id
```

### 6. 摊位利润
```python
# 计算逻辑（Python）
profit_cents = net_revenue_cents - total_cost_cents
```

### 7. 摊位利润率
```python
# 计算逻辑（Python）
if net_revenue_cents > 0:
    profit_margin = (profit_cents / net_revenue_cents) * 100.0
else:
    profit_margin = None
```

## 🛍️ 商品维度统计

### 1. 商品销量
```sql
-- 统计每个商品的 pay 类型交易笔数
SELECT 
    p.id as product_id,
    p.name as product_name,
    p.booth_id,
    b.name as booth_name,
    COUNT(t.id) as sales_quantity
FROM products p
JOIN booths b ON b.id = p.booth_id
LEFT JOIN transactions t ON t.product_id = p.id AND t.type = 'pay'
WHERE b.event_id = ?  -- 可选：按活动筛选
GROUP BY p.id, p.name, p.booth_id, b.name
ORDER BY sales_quantity DESC
```

### 2. 商品收入
```sql
-- 统计每个商品的 pay 类型交易总额
SELECT 
    product_id,
    COALESCE(SUM(amount), 0) as revenue_cents
FROM transactions
WHERE type = 'pay'
  AND product_id IS NOT NULL
  AND event_id = ?  -- 可选：按活动筛选
GROUP BY product_id
```

### 3. 商品总成本
```python
# 计算逻辑（Python）
if product.cost_price is not None:
    total_cost_cents = product.cost_price * sales_quantity
else:
    total_cost_cents = 0
```

### 4. 商品利润
```python
# 计算逻辑（Python）
profit_cents = revenue_cents - total_cost_cents
```

### 5. 商品利润率
```python
# 计算逻辑（Python）
if revenue_cents > 0:
    profit_margin = (profit_cents / revenue_cents) * 100.0
else:
    profit_margin = None
```

## 🏆 排行榜查询

### 1. 营业额排行榜
```sql
-- 按摊位营业额降序排序，取 TOP N
SELECT 
    b.id as booth_id,
    b.name as booth_name,
    b.class_name,
    COALESCE(SUM(t.amount), 0) as revenue_cents
FROM booths b
LEFT JOIN transactions t ON t.booth_id = b.id AND t.type = 'pay'
WHERE b.event_id = ?  -- 可选：按活动筛选
GROUP BY b.id, b.name, b.class_name
ORDER BY revenue_cents DESC
LIMIT ?  -- TOP N
```

### 2. 利润排行榜
```python
# 计算逻辑（Python）
# 1. 获取所有摊位的报表数据（包含利润）
booth_report = get_booth_report(event_id)

# 2. 按利润降序排序
sorted_booths = sorted(
    booth_report.booths,
    key=lambda x: x.profit,
    reverse=True
)[:limit]
```

### 3. 利润率排行榜
```python
# 计算逻辑（Python）
# 1. 获取所有摊位的报表数据（包含利润率）
booth_report = get_booth_report(event_id)

# 2. 过滤掉利润率为 None 的摊位
booths_with_margin = [
    booth for booth in booth_report.booths
    if booth.profit_margin is not None
]

# 3. 按利润率降序排序
sorted_booths = sorted(
    booths_with_margin,
    key=lambda x: x.profit_margin,
    reverse=True
)[:limit]
```

### 4. 商品排行榜（销量）
```sql
-- 按商品销量降序排序，取 TOP N
SELECT 
    p.id as product_id,
    p.name as product_name,
    p.booth_id,
    b.name as booth_name,
    COUNT(t.id) as sales_quantity
FROM products p
JOIN booths b ON b.id = p.booth_id
LEFT JOIN transactions t ON t.product_id = p.id AND t.type = 'pay'
WHERE b.event_id = ?  -- 可选：按活动筛选
GROUP BY p.id, p.name, p.booth_id, b.name
ORDER BY sales_quantity DESC
LIMIT ?  -- TOP N
```

### 5. 商品排行榜（收入）
```sql
-- 按商品收入降序排序，取 TOP N
SELECT 
    p.id as product_id,
    p.name as product_name,
    p.booth_id,
    b.name as booth_name,
    COALESCE(SUM(t.amount), 0) as revenue_cents
FROM products p
JOIN booths b ON b.id = p.booth_id
LEFT JOIN transactions t ON t.product_id = p.id AND t.type = 'pay'
WHERE b.event_id = ?  -- 可选：按活动筛选
GROUP BY p.id, p.name, p.booth_id, b.name
ORDER BY revenue_cents DESC
LIMIT ?  -- TOP N
```

## 🔍 异常审计查询

### 1. 高频退款检测
```sql
-- 查询最近1小时内退款超过5次的操作员
SELECT 
    booth_operator_id,
    COUNT(id) as refund_count
FROM transactions
WHERE type = 'refund'
  AND created_at >= datetime('now', '-1 hour')  -- SQLite
  -- AND created_at >= NOW() - INTERVAL '1 hour'  -- PostgreSQL
  AND booth_operator_id IS NOT NULL
  AND event_id = ?  -- 可选：按活动筛选
GROUP BY booth_operator_id
HAVING COUNT(id) > 5
```

### 2. 大额更正检测
```sql
-- 查询金额超过1000元的 adjust 类型交易
SELECT 
    id,
    type,
    amount,
    participant_id,
    booth_id,
    booth_operator_id,
    remark,
    created_at
FROM transactions
WHERE type = 'adjust'
  AND amount > 100000  -- 1000元 = 100000分
  AND event_id = ?  -- 可选：按活动筛选
ORDER BY created_at DESC
LIMIT ?
```

### 3. 可疑操作检测（深夜交易）
```sql
-- 查询深夜时段（22:00-06:00）的交易
SELECT 
    id,
    type,
    amount,
    participant_id,
    booth_id,
    booth_operator_id,
    remark,
    created_at
FROM transactions
WHERE (
    CAST(strftime('%H', created_at) AS INTEGER) >= 22  -- SQLite
    OR CAST(strftime('%H', created_at) AS INTEGER) < 6
    -- EXTRACT(HOUR FROM created_at) >= 22  -- PostgreSQL
    -- OR EXTRACT(HOUR FROM created_at) < 6
)
  AND type IN ('pay', 'refund', 'adjust')
  AND event_id = ?  -- 可选：按活动筛选
ORDER BY created_at DESC
LIMIT ?
```

## 📈 ORM 查询示例（SQLAlchemy）

### 总览统计
```python
from sqlalchemy import func
from models.transaction import Transaction, TransactionType

# 总发放额度
total_issued_cents = db.query(
    func.coalesce(func.sum(Transaction.amount), 0)
).filter(
    Transaction.type == TransactionType.issue.value,
    Transaction.event_id == event_id  # 可选
).scalar()

# 总充值额
total_recharged_cents = db.query(
    func.coalesce(func.sum(Transaction.amount), 0)
).filter(
    Transaction.type == TransactionType.recharge.value,
    Transaction.event_id == event_id  # 可选
).scalar()

# 总消费额
total_consumed_cents = db.query(
    func.coalesce(func.sum(Transaction.amount), 0)
).filter(
    Transaction.type == TransactionType.pay.value,
    Transaction.event_id == event_id  # 可选
).scalar()

# 总退款额
total_refunded_cents = db.query(
    func.coalesce(func.sum(Transaction.amount), 0)
).filter(
    Transaction.type == TransactionType.refund.value,
    Transaction.event_id == event_id  # 可选
).scalar()
```

### 摊位营业额排行榜
```python
from sqlalchemy import func, desc, and_
from models.booth import Booth
from models.transaction import Transaction, TransactionType

# 查询摊位营业额
query = db.query(
    Booth.id.label('booth_id'),
    Booth.name.label('booth_name'),
    Booth.class_name.label('class_name'),
    func.coalesce(func.sum(Transaction.amount), 0).label('revenue')
).outerjoin(
    Transaction,
    and_(
        Transaction.booth_id == Booth.id,
        Transaction.type == TransactionType.pay.value
    )
).group_by(
    Booth.id, Booth.name, Booth.class_name
)

# 可选：按活动筛选
if event_id:
    query = query.filter(Booth.event_id == event_id)

# 按营业额降序排序
results = query.order_by(desc('revenue')).limit(limit).all()
```

### 商品成本统计
```python
from models.product import Product

# 查询摊位总成本
cost_query = db.query(
    func.coalesce(func.sum(Product.cost_price), 0)
).join(
    Transaction,
    Transaction.product_id == Product.id
).filter(
    Transaction.booth_id == booth_id,
    Transaction.type == TransactionType.pay.value,
    Product.cost_price.isnot(None)
)

total_cost_cents = cost_query.scalar() or 0
```

## 💡 性能优化建议

### 1. 索引优化
```sql
-- 为常用查询字段创建索引
CREATE INDEX idx_transactions_type ON transactions(type);
CREATE INDEX idx_transactions_event_id ON transactions(event_id);
CREATE INDEX idx_transactions_booth_id ON transactions(booth_id);
CREATE INDEX idx_transactions_product_id ON transactions(product_id);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_transactions_booth_operator_id ON transactions(booth_operator_id);

-- 复合索引
CREATE INDEX idx_transactions_type_event ON transactions(type, event_id);
CREATE INDEX idx_transactions_type_booth ON transactions(type, booth_id);
```

### 2. 查询优化
- 使用 `COALESCE` 处理 NULL 值
- 使用 `LEFT JOIN` 确保所有摊位/商品都被包含
- 使用 `GROUP BY` 进行聚合统计
- 使用 `LIMIT` 限制返回数量
- 避免 `SELECT *`，只查询需要的字段

### 3. 缓存策略
- 对于不经常变化的统计数据，可以使用缓存
- 设置合理的缓存过期时间（如5分钟）
- 在数据更新时主动清除缓存

## 📝 注意事项

1. **金额单位**: 数据库存储单位为"分"，展示时需要除以100转换为"元"
2. **NULL 处理**: 使用 `COALESCE` 或 `IFNULL` 处理可能的 NULL 值
3. **时区处理**: 确保时间戳使用 UTC 时区
4. **数据完整性**: 依赖外键关系确保数据一致性
5. **性能监控**: 对于大数据量查询，需要监控执行时间并优化

## 🔗 相关文档

- [账本模式快速参考](../LEDGER_MODE_QUICK_REFERENCE.md)
- [API 文档](./API_DOCUMENTATION.md)
- [报表系统总结](../REPORTS_SYSTEM_SUMMARY.md)
