# 📈 模拟股市与期末结算系统

## 系统概述

本系统实现了一个完整的校园模拟股市，采用"全局奖金池动态定价模型"，支持学生使用投资币购买摊位股票，并在活动结束时根据摊位经营表现进行期末结算。

---

## 🏗️ 系统架构

### 核心设计理念

1. **双账户体系**
   - **活动账户**: 用于日常消费（充值、支付、退款）
   - **投资币账户**: 用于股票投资（独立账户，可与活动账户互转）

2. **悲观锁机制**
   - 使用 `SELECT ... FOR UPDATE` 防止并发超卖
   - 保证投资币余额不会扣成负数

3. **事务一致性**
   - 所有关键操作都在数据库事务中执行
   - 保证数据的原子性和一致性

---

## 📊 数据库设计

### 1. 投资币账户表 (stock_accounts)

```sql
CREATE TABLE stock_accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    participant_id INT NOT NULL,
    event_id INT NOT NULL,
    balance INT NOT NULL DEFAULT 0,  -- 投资币余额（分）
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY (participant_id, event_id)
);
```

### 2. 股票订单表 (stock_orders)

```sql
CREATE TABLE stock_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    participant_id INT NOT NULL,
    stock_account_id INT NOT NULL,
    card_uid VARCHAR(32) NOT NULL,
    booth_id INT NOT NULL,
    shares INT NOT NULL,              -- 购买股数
    buy_price INT NOT NULL,           -- 购买单价（分）
    total_amount INT NOT NULL,        -- 购买总金额（分）
    status VARCHAR(20) NOT NULL,      -- holding/settled
    settlement_price INT NULL,        -- 结算单价（分）
    settlement_amount INT NULL,       -- 结算总金额（分）
    created_at DATETIME NOT NULL,
    settled_at DATETIME NULL
);
```

### 3. 账户互转记录表 (account_transfers)

```sql
CREATE TABLE account_transfers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    participant_id INT NOT NULL,
    card_uid VARCHAR(32) NOT NULL,
    transfer_type VARCHAR(20) NOT NULL,  -- to_stock/from_stock
    amount INT NOT NULL,
    account_balance_before INT NOT NULL,
    account_balance_after INT NOT NULL,
    stock_balance_before INT NOT NULL,
    stock_balance_after INT NOT NULL,
    created_at DATETIME NOT NULL
);
```

---

## 🔄 业务流程

### 1. 账户互转流程

```
活动账户 ←→ 投资币账户
```

**API**: `POST /api/stock/transfer`

**流程**:
1. 验证参与者身份
2. 锁定活动账户（悲观锁）
3. 锁定投资币账户（悲观锁）
4. 检查余额是否充足
5. 执行转账操作
6. 记录转账记录
7. 提交事务

**示例请求**:
```json
{
  "card_uid": "A1B2C3D4",
  "event_id": 1,
  "transfer_type": "to_stock",
  "amount": 10000,
  "timestamp": 1234567890,
  "signature": "abc123..."
}
```

### 2. 购买股票流程

**API**: `POST /api/stock/buy`

**流程**:
1. 验证参与者和摊位
2. 锁定投资币账户（悲观锁）
3. 检查投资币余额
4. 扣除投资币余额
5. 创建股票订单
6. 提交事务

**示例请求**:
```json
{
  "card_uid": "A1B2C3D4",
  "event_id": 1,
  "booth_id": 2,
  "shares": 10,
  "timestamp": 1234567890,
  "signature": "abc123..."
}
```

**购买规则**:
- 固定单价: 10元/股 (1000分/股)
- 股票不可二次交易，只能锁仓至期末结算
- 使用投资币账户余额支付

### 3. 期末结算流程

**API**: `POST /api/stock/settle`

**流程**:
1. 验证活动存在
2. 查询所有股票订单
3. 计算全局奖金池
4. 计算每个摊位的经营分
5. 计算分红占比
6. 计算最终股价
7. 更新所有订单的结算价格
8. 提交事务

**结算公式**:

```
1. 全局奖金池 = (全场买股总金额) × (1 - 0.05 手续费)

2. 摊位经营分 = 0.2 × 营业额 + 0.6 × 净利润 + 0.2 × 订单数

3. 摊位分红占比 = 该摊位分 / 全场摊位总分

4. 摊位最终每股价格 = (奖金池 × 占比) / 该摊位售出总股数
```

**示例**:

假设活动中有3个摊位：

| 摊位 | 营业额 | 净利润 | 订单数 | 经营分 | 售出股数 | 总投资额 |
|------|--------|--------|--------|--------|----------|----------|
| A摊  | 5000分 | 3000分 | 50单   | 3900   | 100股    | 100000分 |
| B摊  | 4000分 | 2500分 | 40单   | 3100   | 80股     | 80000分  |
| C摊  | 3000分 | 2000分 | 30单   | 2400   | 60股     | 60000分  |

**计算过程**:

1. 全局奖金池 = (100000 + 80000 + 60000) × 0.95 = 228000分

2. 全场总分 = 3900 + 3100 + 2400 = 9400

3. A摊分红占比 = 3900 / 9400 = 0.4149
   B摊分红占比 = 3100 / 9400 = 0.3298
   C摊分红占比 = 2400 / 9400 = 0.2553

4. A摊最终股价 = (228000 × 0.4149) / 100 = 946分/股 = 9.46元/股
   B摊最终股价 = (228000 × 0.3298) / 80 = 939分/股 = 9.39元/股
   C摊最终股价 = (228000 × 0.2553) / 60 = 971分/股 = 9.71元/股

**结果分析**:
- A摊经营最好，但因售出股数多，最终股价略低
- C摊虽然经营分最低，但售出股数少，最终股价反而最高
- 这体现了"稀缺性"的市场规律

---

## 🔐 安全机制

### 1. 悲观锁 (Pessimistic Locking)

```python
# 锁定投资币账户
stock_account = db.query(StockAccount).filter(
    and_(
        StockAccount.participant_id == participant_id,
        StockAccount.event_id == event_id
    )
).with_for_update().first()
```

**作用**:
- 防止并发购买导致余额扣成负数
- 防止并发转账导致数据不一致

### 2. 数据库事务

```python
try:
    # 执行业务逻辑
    db.commit()
except Exception as e:
    db.rollback()
    raise
```

**作用**:
- 保证操作的原子性
- 失败时自动回滚

### 3. 签名验证

```python
signature = SHA256(card_uid + amount + timestamp + secret_key)
```

**作用**:
- 防止请求被篡改
- 防止重放攻击

---

## 📱 Android 客户端

### 投资办理终端 (InvestmentActivity)

**功能**:
- NFC卡片识别
- 双账户余额展示
- 摊位选择
- 股数输入
- 实时金额计算
- 投资确认

**UI设计**:
- 黑金配色，未来科技感
- NFC脉冲动画
- 流畅的卡片动画
- 高科技感对话框

**使用流程**:
1. 打开投资办理终端
2. 学生刷NFC卡
3. 自动识别参与者信息
4. 选择投资摊位
5. 输入购买股数
6. 确认投资
7. 显示投资结果

---

## 📊 数据统计

### 1. 股市统计 API

**API**: `GET /api/stock/stats/{event_id}`

**返回数据**:
```json
{
  "event_id": 1,
  "total_investment": 240000,
  "total_investment_yuan": 2400.0,
  "global_pool": 228000,
  "global_pool_yuan": 2280.0,
  "fee_collected": 12000,
  "fee_collected_yuan": 120.0,
  "total_orders": 50,
  "total_investors": 30,
  "total_booths": 3,
  "is_settled": false
}
```

### 2. 摊位股票统计 API

**API**: `GET /api/stock/booth-stats/{booth_id}?event_id={event_id}`

**返回数据**:
```json
{
  "booth_id": 1,
  "booth_name": "美食摊",
  "class_name": "高一(1)班",
  "sold_shares": 100,
  "total_investment": 100000,
  "total_investment_yuan": 1000.0,
  "investor_count": 20,
  "current_price": 10.0,
  "is_settled": false,
  "final_price": null
}
```

---

## 🎯 使用场景

### 场景1: 学生投资

1. 学生到投资办理窗口
2. 工作人员打开投资办理终端
3. 学生刷NFC卡
4. 工作人员帮助选择摊位
5. 输入购买股数
6. 确认投资
7. 完成交易

### 场景2: 账户互转

1. 学生需要将活动余额转为投资币
2. 工作人员调用转账API
3. 输入转账金额
4. 确认转账
5. 完成互转

### 场景3: 期末结算

1. 活动结束
2. 管理员登录后台
3. 点击"期末结算"按钮
4. 系统自动计算所有摊位的最终股价
5. 更新所有订单的结算价格
6. 生成结算报告
7. 公布结算结果

---

## 🚀 部署指南

### 1. 数据库迁移

```bash
# 运行迁移脚本
python run_migration.py migrations/007_stock_account_system.sql
```

### 2. 启动后端服务

```bash
# 启动FastAPI服务
python start_server.py
```

### 3. 配置Android客户端

```properties
# local.properties
backend.url=http://YOUR_SERVER_IP:8000
```

### 4. 安装Android应用

```bash
cd android
./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

---

## 📝 API文档

### 完整API列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | /api/stock/transfer | 账户互转 | 无需认证 |
| POST | /api/stock/buy | 购买股票 | 无需认证 |
| GET | /api/stock/orders/{participant_id} | 查询订单 | 需要认证 |
| POST | /api/stock/settle | 期末结算 | 管理员 |
| GET | /api/stock/stats/{event_id} | 股市统计 | 需要认证 |
| GET | /api/stock/booth-stats/{booth_id} | 摊位统计 | 需要认证 |

---

## 🐛 故障排查

### 常见问题

**1. 购买失败: 投资币余额不足**
- 解决: 使用账户互转功能，将活动余额转为投资币

**2. 结算失败: 已完成结算**
- 解决: 每个活动只能结算一次，无法重复结算

**3. 并发购买导致超卖**
- 解决: 系统已使用悲观锁机制，理论上不会发生

**4. 数据不一致**
- 解决: 检查数据库事务是否正常提交

---

## 📞 技术支持

如有问题，请查看以下文档：
- [API文档](./API_DOCUMENTATION.md)
- [Android集成指南](../android/INVESTMENT_INTEGRATION.md)
- [数据库迁移脚本](../migrations/007_stock_account_system.sql)

---

**Made with ❤️ for campus financial education**
