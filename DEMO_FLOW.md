# NFC Campus Event System - 完整演示流程

本文档提供了一套完整的演示数据流，展示系统从活动创建到结算的全流程。

---

## 演示环境准备

### 1. 启动后端服务

```bash
# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate  # Windows

# 启动服务
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 创建管理员账户

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123",
    "role": "super_admin"
  }'
```

### 3. 登录获取 Token

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**保存返回的 access_token，后续请求都需要使用。**

```bash
# 设置环境变量
export TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
```

---

## 演示流程

### 步骤 1: 创建活动

创建一个校园美食节活动。

```bash
curl -X POST "http://localhost:8000/events" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "2024春季校园美食节",
    "start_time": "2024-03-01T08:00:00Z",
    "end_time": "2024-03-03T20:00:00Z",
    "status": "active",
    "recharge_enabled": true,
    "consume_enabled": true,
    "expire_rule": "event_end"
  }'
```

**响应示例：**
```json
{
  "id": 1,
  "name": "2024春季校园美食节",
  "start_time": "2024-03-01T08:00:00Z",
  "end_time": "2024-03-03T20:00:00Z",
  "status": "active",
  "recharge_enabled": true,
  "consume_enabled": true,
  "expire_rule": "event_end",
  "created_at": "2024-02-28T10:00:00Z"
}
```

**记录 event_id = 1**

---

### 步骤 2: 创建摊位

创建三个班级摊位。

#### 2.1 高一(1)班 - 美食摊

```bash
curl -X POST "http://localhost:8000/booths" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "name": "美食天地",
    "class_name": "高一(1)班",
    "status": "active"
  }'
```

**记录 booth_id = 1**

#### 2.2 高一(2)班 - 饮品站

```bash
curl -X POST "http://localhost:8000/booths" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "name": "清凉饮品站",
    "class_name": "高一(2)班",
    "status": "active"
  }'
```

**记录 booth_id = 2**

#### 2.3 高一(3)班 - 甜品屋

```bash
curl -X POST "http://localhost:8000/booths" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "name": "甜蜜时光",
    "class_name": "高一(3)班",
    "status": "active"
  }'
```

**记录 booth_id = 3**

---

### 步骤 3: 创建商品

为每个摊位添加商品。

#### 3.1 美食天地商品

```bash
# 烤肠
curl -X POST "http://localhost:8000/products" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booth_id": 1,
    "name": "烤肠",
    "price": 5.00,
    "cost": 2.50,
    "stock": 100,
    "status": "available"
  }'

# 炸鸡翅
curl -X POST "http://localhost:8000/products" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booth_id": 1,
    "name": "炸鸡翅",
    "price": 8.00,
    "cost": 4.00,
    "stock": 80,
    "status": "available"
  }'
```

#### 3.2 清凉饮品站商品

```bash
# 奶茶
curl -X POST "http://localhost:8000/products" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booth_id": 2,
    "name": "珍珠奶茶",
    "price": 10.00,
    "cost": 4.00,
    "stock": 120,
    "status": "available"
  }'

# 果汁
curl -X POST "http://localhost:8000/products" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booth_id": 2,
    "name": "鲜榨果汁",
    "price": 12.00,
    "cost": 5.00,
    "stock": 100,
    "status": "available"
  }'
```

#### 3.3 甜蜜时光商品

```bash
# 蛋糕
curl -X POST "http://localhost:8000/products" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booth_id": 3,
    "name": "小蛋糕",
    "price": 15.00,
    "cost": 6.00,
    "stock": 60,
    "status": "available"
  }'

# 冰淇淋
curl -X POST "http://localhost:8000/products" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booth_id": 3,
    "name": "冰淇淋",
    "price": 8.00,
    "cost": 3.00,
    "stock": 100,
    "status": "available"
  }'
```

---

### 步骤 4: 创建参与者并绑定卡片

创建学生参与者并绑定 NFC 卡片。

#### 4.1 创建参与者

```bash
# 张三
curl -X POST "http://localhost:8000/participants" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "张三",
    "student_id": "2024001",
    "class_name": "高二(1)班",
    "phone": "13800138001"
  }'

# 李四
curl -X POST "http://localhost:8000/participants" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "李四",
    "student_id": "2024002",
    "class_name": "高二(2)班",
    "phone": "13800138002"
  }'

# 王五
curl -X POST "http://localhost:8000/participants" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "王五",
    "student_id": "2024003",
    "class_name": "高二(3)班",
    "phone": "13800138003"
  }'
```

#### 4.2 绑定 NFC 卡片

```bash
# 张三绑定卡片
curl -X POST "http://localhost:8000/participants/1/bind-card" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "card_uid": "A1B2C3D4"
  }'

# 李四绑定卡片
curl -X POST "http://localhost:8000/participants/2/bind-card" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "card_uid": "E5F6G7H8"
  }'

# 王五绑定卡片
curl -X POST "http://localhost:8000/participants/3/bind-card" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "card_uid": "I9J0K1L2"
  }'
```

---

### 步骤 5: 发放活动额度

为参与者发放初始额度。

```bash
# 张三发放 100 元
curl -X POST "http://localhost:8000/recharge" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "card_uid": "A1B2C3D4",
    "amount": 100.00,
    "remark": "活动初始额度"
  }'

# 李四发放 100 元
curl -X POST "http://localhost:8000/recharge" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "card_uid": "E5F6G7H8",
    "amount": 100.00,
    "remark": "活动初始额度"
  }'

# 王五发放 100 元
curl -X POST "http://localhost:8000/recharge" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "card_uid": "I9J0K1L2",
    "amount": 100.00,
    "remark": "活动初始额度"
  }'
```

---

### 步骤 6: 创建摊位收银员

为每个摊位创建收银员账户。

```bash
# 美食天地收银员
curl -X POST "http://localhost:8000/auth/register" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "cashier1",
    "password": "cashier123",
    "role": "booth_cashier",
    "booth_id": 1
  }'

# 清凉饮品站收银员
curl -X POST "http://localhost:8000/auth/register" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "cashier2",
    "password": "cashier123",
    "role": "booth_cashier",
    "booth_id": 2
  }'

# 甜蜜时光收银员
curl -X POST "http://localhost:8000/auth/register" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "cashier3",
    "password": "cashier123",
    "role": "booth_cashier",
    "booth_id": 3
  }'
```

---

### 步骤 7: 刷卡消费

模拟学生在各摊位消费。

#### 7.1 收银员登录

```bash
# 美食天地收银员登录
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "cashier1",
    "password": "cashier123"
  }'

# 保存 token
export CASHIER1_TOKEN="..."
```

#### 7.2 张三在美食天地消费

```bash
# 购买烤肠（5元）
curl -X POST "http://localhost:8000/payment" \
  -H "Authorization: Bearer $CASHIER1_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "card_uid": "A1B2C3D4",
    "amount": 5.00,
    "booth_id": 1,
    "product_id": 1,
    "remark": "购买烤肠"
  }'

# 购买炸鸡翅（8元）
curl -X POST "http://localhost:8000/payment" \
  -H "Authorization: Bearer $CASHIER1_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "card_uid": "A1B2C3D4",
    "amount": 8.00,
    "booth_id": 1,
    "product_id": 2,
    "remark": "购买炸鸡翅"
  }'
```

#### 7.3 李四在清凉饮品站消费

```bash
# 收银员2登录
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "cashier2",
    "password": "cashier123"
  }'

export CASHIER2_TOKEN="..."

# 购买珍珠奶茶（10元）
curl -X POST "http://localhost:8000/payment" \
  -H "Authorization: Bearer $CASHIER2_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "card_uid": "E5F6G7H8",
    "amount": 10.00,
    "booth_id": 2,
    "product_id": 3,
    "remark": "购买珍珠奶茶"
  }'
```

#### 7.4 王五在甜蜜时光消费

```bash
# 收银员3登录
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "cashier3",
    "password": "cashier123"
  }'

export CASHIER3_TOKEN="..."

# 购买小蛋糕（15元）
curl -X POST "http://localhost:8000/payment" \
  -H "Authorization: Bearer $CASHIER3_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "card_uid": "I9J0K1L2",
    "amount": 15.00,
    "booth_id": 3,
    "product_id": 5,
    "remark": "购买小蛋糕"
  }'

# 购买冰淇淋（8元）
curl -X POST "http://localhost:8000/payment" \
  -H "Authorization: Bearer $CASHIER3_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "card_uid": "I9J0K1L2",
    "amount": 8.00,
    "booth_id": 3,
    "product_id": 6,
    "remark": "购买冰淇淋"
  }'
```

---

### 步骤 8: 查询余额

查询参与者当前余额。

```bash
# 查询张三余额（应该是 100 - 5 - 8 = 87 元）
curl -X GET "http://localhost:8000/balance?event_id=1&card_uid=A1B2C3D4" \
  -H "Authorization: Bearer $TOKEN"

# 查询李四余额（应该是 100 - 10 = 90 元）
curl -X GET "http://localhost:8000/balance?event_id=1&card_uid=E5F6G7H8" \
  -H "Authorization: Bearer $TOKEN"

# 查询王五余额（应该是 100 - 15 - 8 = 77 元）
curl -X GET "http://localhost:8000/balance?event_id=1&card_uid=I9J0K1L2" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 步骤 9: 退款操作

模拟一笔退款。

```bash
# 张三退回炸鸡翅（8元）
curl -X POST "http://localhost:8000/refund" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "card_uid": "A1B2C3D4",
    "amount": 8.00,
    "related_txn_id": 2,
    "remark": "商品质量问题退款"
  }'

# 再次查询张三余额（应该是 87 + 8 = 95 元）
curl -X GET "http://localhost:8000/balance?event_id=1&card_uid=A1B2C3D4" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 步骤 10: 查看交易历史

查询各摊位的交易记录。

```bash
# 查询美食天地交易记录
curl -X GET "http://localhost:8000/transactions?booth_id=1" \
  -H "Authorization: Bearer $TOKEN"

# 查询清凉饮品站交易记录
curl -X GET "http://localhost:8000/transactions?booth_id=2" \
  -H "Authorization: Bearer $TOKEN"

# 查询甜蜜时光交易记录
curl -X GET "http://localhost:8000/transactions?booth_id=3" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 步骤 11: 现金对账

为摊位进行现金对账。

```bash
# 美食天地现金对账
curl -X POST "http://localhost:8000/cash-reconciliation" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booth_id": 1,
    "event_id": 1,
    "expected_cash": 5.00,
    "actual_cash": 5.00,
    "reason": null
  }'

# 清凉饮品站现金对账（有差额）
curl -X POST "http://localhost:8000/cash-reconciliation" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booth_id": 2,
    "event_id": 1,
    "expected_cash": 10.00,
    "actual_cash": 9.50,
    "reason": "找零误差"
  }'
```

---

### 步骤 12: 查看报表

查询各类统计报表。

```bash
# 总览统计
curl -X GET "http://localhost:8000/reports/summary?event_id=1" \
  -H "Authorization: Bearer $TOKEN"

# 摊位报表
curl -X GET "http://localhost:8000/reports/booths?event_id=1" \
  -H "Authorization: Bearer $TOKEN"

# 商品报表
curl -X GET "http://localhost:8000/reports/products?event_id=1" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 步骤 13: 导出数据

导出各类报表文件。

```bash
# 导出班级结算单
curl -X GET "http://localhost:8000/export/class-settlement?event_id=1" \
  -H "Authorization: Bearer $TOKEN" \
  -o class_settlement.xlsx

# 导出全量流水
curl -X GET "http://localhost:8000/export/transactions?event_id=1" \
  -H "Authorization: Bearer $TOKEN" \
  -o transactions.xlsx

# 导出退款清单
curl -X GET "http://localhost:8000/export/refund-adjustments?event_id=1" \
  -H "Authorization: Bearer $TOKEN" \
  -o refund_adjustments.xlsx

# 导出排名表
curl -X GET "http://localhost:8000/export/leaderboard?event_id=1" \
  -H "Authorization: Bearer $TOKEN" \
  -o leaderboard.xlsx
```

---

### 步骤 14: 活动关闭

关闭活动并执行额度失效。

```bash
curl -X POST "http://localhost:8000/events/1/close" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "expire_quotas": true
  }'
```

**响应示例：**
```json
{
  "event_id": 1,
  "status": "ended",
  "expired_accounts": 3,
  "total_expired_amount": 262.00
}
```

---

## 验证结果

### 1. 验证活动状态

```bash
curl -X GET "http://localhost:8000/events/1" \
  -H "Authorization: Bearer $TOKEN"
```

应该显示 `status: "ended"`

### 2. 验证余额归零

```bash
# 所有参与者余额应该为 0
curl -X GET "http://localhost:8000/balance?event_id=1&card_uid=A1B2C3D4" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. 验证交易记录

```bash
# 应该能看到 expire 类型的交易记录
curl -X GET "http://localhost:8000/transactions?event_id=1" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Android 应用演示

### 1. 收银员登录

1. 启动 Android 应用
2. 输入收银员账号：`cashier1`
3. 输入密码：`cashier123`
4. 点击登录

### 2. 选择活动和摊位

1. 选择活动：`2024春季校园美食节`
2. 自动关联到摊位：`美食天地`

### 3. NFC 刷卡消费

1. 点击"刷卡支付"
2. 将 NFC 卡片靠近手机背面
3. 读取卡片 UID
4. 选择商品：`烤肠`
5. 确认金额：`5.00 元`
6. 点击"确认支付"
7. 显示支付成功和余额

### 4. 查看交易记录

1. 点击"交易记录"
2. 查看本摊位的所有交易
3. 可按日期、商品筛选

---

## 演示数据总结

### 活动数据
- **活动名称**: 2024春季校园美食节
- **活动时间**: 2024-03-01 至 2024-03-03
- **参与摊位**: 3 个
- **参与学生**: 3 人
- **总发放额度**: 300 元
- **总消费额**: 46 元（含退款后）
- **总退款额**: 8 元

### 摊位数据
| 摊位 | 班级 | 营业额 | 退款额 | 净收入 |
|------|------|--------|--------|--------|
| 美食天地 | 高一(1)班 | 13 元 | 8 元 | 5 元 |
| 清凉饮品站 | 高一(2)班 | 10 元 | 0 元 | 10 元 |
| 甜蜜时光 | 高一(3)班 | 23 元 | 0 元 | 23 元 |

### 学生消费数据
| 学生 | 初始额度 | 消费额 | 退款额 | 剩余额度 | 失效额度 |
|------|----------|--------|--------|----------|----------|
| 张三 | 100 元 | 13 元 | 8 元 | 95 元 | 95 元 |
| 李四 | 100 元 | 10 元 | 0 元 | 90 元 | 90 元 |
| 王五 | 100 元 | 23 元 | 0 元 | 77 元 | 77 元 |

---

## 联调注意事项

### 1. 时间同步
- 确保服务器和客户端时间同步
- JWT token 有过期时间限制

### 2. 网络配置
- Android 设备和服务器需在同一网络
- 检查防火墙设置，开放 8000 端口

### 3. NFC 卡片
- 使用真实的 NFC 卡片或模拟器
- 卡片 UID 必须唯一

### 4. 数据一致性
- 每次演示前清空数据库
- 或使用不同的活动 ID

### 5. 错误处理
- 注意查看后端日志
- Android 应用显示详细错误信息

### 6. 性能测试
- 模拟多个收银员同时操作
- 测试并发支付场景

---

## 常见问题

### Q1: Token 过期怎么办？
A: 重新登录获取新的 token。

### Q2: 余额不足如何处理？
A: 系统会返回错误，需要先充值。

### Q3: 如何撤销交易？
A: 使用退款接口，需要提供原交易 ID。

### Q4: 活动关闭后还能操作吗？
A: 只能进行退款和调整操作，不能消费和充值。

### Q5: 如何重置演示数据？
A: 删除数据库重新初始化，或创建新活动。

---

## 下一步

完成演示后，可以：
1. 查看生成的 Excel 报表
2. 分析摊位经营数据
3. 导出完整的交易流水
4. 进行财务对账
5. 生成活动总结报告
