# 单一活动活动系统升级

## 概述

本次升级确保系统在同一时间只能有一个活动处于 `active` 状态，并且所有摊位和参与者都自动关联到当前激活的活动。这简化了操作流程，避免了多活动并行带来的混乱。

## 主要变更

### 1. 后端 - 活动管理 (services/event_service.py)

#### 新增功能

- **自动暂停其他活动**：当创建或更新活动状态为 `active` 时，系统会自动将所有其他活动状态设置为 `paused`
- **获取当前活动活动**：新增 `get_active_event()` 方法，用于获取当前唯一的激活活动
- **内部辅助方法**：`_pause_all_active_events()` 用于批量暂停活动

#### 修改的方法

```python
def create_event(...) -> Event:
    """
    创建新活动。
    如果创建的活动状态为 'active'，会自动将其他所有活动状态设置为 'paused'。
    """

def update_event(event_id: int, **kwargs) -> Event:
    """
    更新活动信息。
    如果将活动状态更新为 'active'，会自动将其他所有活动状态设置为 'paused'。
    """

def get_active_event() -> Optional[Event]:
    """
    获取当前激活的活动。
    Returns: 当前激活的活动对象，如果没有则返回 None
    """
```

### 2. 后端 - 摊位管理 (routes/booths.py, schemas/booth.py)

#### Schema 变更

**BoothCreate**:
- `event_id`: 从必填改为可选 (`Optional[int]`)
- 默认行为：如果未指定，自动使用当前激活的活动

**BoothPaymentRequest**:
- `event_id`: 从必填改为可选 (`Optional[int]`)
- 默认行为：如果未指定，自动使用当前激活的活动

#### 路由变更

**POST /booths** (创建摊位):
```python
# 如果未指定 event_id，使用当前激活的活动
if event_id is None:
    active_event = event_service.get_active_event()
    if active_event is None:
        return 400 "NO_ACTIVE_EVENT"
    event_id = active_event.id
```

**GET /booths** (列出摊位):
```python
# 如果未指定 event_id，默认过滤到当前激活的活动
if event_id is None:
    active_event = event_service.get_active_event()
    if active_event is None:
        return 400 "NO_ACTIVE_EVENT"
    event_id = active_event.id
```

**POST /booths/{booth_id}/pay** (摊位支付):
```python
# 如果未指定 event_id，使用当前激活的活动
if payment_request.event_id is None:
    active_event = event_service.get_active_event()
    if active_event is None:
        return 400 "NO_ACTIVE_EVENT"
    event_id = active_event.id
```

### 3. 安卓端 - 模型更新

#### BoothPaymentRequest.java

**变更**:
- `eventId` 字段类型从 `int` 改为 `Integer`（允许 null）
- 新增不需要 `eventId` 的构造函数

**新构造函数**:
```java
// 不指定 event_id - 后端将使用当前激活的活动
public BoothPaymentRequest(String cardUid, double amount)

// 完整构造函数（不指定 event_id）
public BoothPaymentRequest(String cardUid, double amount, Integer productId, String remark)
```

**保留的构造函数**:
```java
// 指定 event_id
public BoothPaymentRequest(int eventId, String cardUid, double amount)

// 完整构造函数（指定 event_id）
public BoothPaymentRequest(int eventId, String cardUid, double amount, Integer productId, String remark)
```

#### CashierActivity.java

**变更**:
- `executePayment()` 方法不再需要从 `currentBooth` 获取 `eventId`
- 直接创建不包含 `eventId` 的 `BoothPaymentRequest`

**修改前**:
```java
BoothPaymentRequest request = new BoothPaymentRequest(
    currentBooth.getEventId(),  // 需要 event_id
    currentCardUid,
    totalAmount,
    productId,
    remark.isEmpty() ? null : remark
);
```

**修改后**:
```java
// 不指定 event_id - 后端自动使用当前激活的活动
BoothPaymentRequest request = new BoothPaymentRequest(
    currentCardUid,
    totalAmount,
    productId,
    remark.isEmpty() ? null : remark
);
```

## 使用场景

### 场景 1: 创建新活动并激活

```python
# 创建并激活新活动
POST /events
{
    "name": "2024春季校园美食节",
    "start_time": "2024-03-01T08:00:00Z",
    "end_time": "2024-03-03T20:00:00Z",
    "status": "active"  # 自动暂停其他所有活动
}
```

### 场景 2: 激活已存在的活动

```python
# 将活动状态更新为 active
PATCH /events/2
{
    "status": "active"  # 自动暂停其他所有活动
}
```

### 场景 3: 创建摊位（不指定活动）

```python
# 自动关联到当前激活的活动
POST /booths
{
    "name": "美食摊",
    "class_name": "高一(1)班"
    # event_id 省略 - 自动使用当前激活的活动
}
```

### 场景 4: 列出当前活动的摊位

```python
# 自动过滤到当前激活的活动
GET /booths?status=active
# 不需要指定 event_id
```

### 场景 5: 安卓端支付（不指定活动）

```java
// 创建支付请求 - 不需要 event_id
BoothPaymentRequest request = new BoothPaymentRequest(
    cardUid,
    amount,
    productId,
    remark
);

// 后端自动使用当前激活的活动
apiService.processBoothPayment(authHeader, boothId, request);
```

## 错误处理

### NO_ACTIVE_EVENT 错误

当没有激活的活动且未指定 `event_id` 时，系统返回：

```json
{
    "error_code": "NO_ACTIVE_EVENT",
    "message": "No active event found. Please specify event_id or activate an event."
}
```

**解决方案**:
1. 激活一个现有活动：`PATCH /events/{id}` 设置 `status: "active"`
2. 创建并激活新活动：`POST /events` 设置 `status: "active"`
3. 或者在请求中明确指定 `event_id`

## 向后兼容性

### 完全兼容

所有现有的 API 调用仍然有效：
- 可以继续在请求中指定 `event_id`
- 如果指定了 `event_id`，系统会使用指定的值
- 只有在未指定 `event_id` 时才会自动使用当前激活的活动

### 安卓端兼容性

- 保留了所有原有的构造函数
- 新增了不需要 `eventId` 的构造函数
- 现有代码可以继续使用原有构造函数
- 新代码可以使用简化的构造函数

## 数据库影响

### 无需迁移

本次升级不涉及数据库结构变更：
- 不需要运行数据库迁移
- 不需要修改现有数据
- 所有表结构保持不变

### 数据一致性

系统会自动维护活动状态的一致性：
- 确保同一时间只有一个 `active` 状态的活动
- 其他活动自动设置为 `paused` 状态
- 不影响 `draft` 和 `ended` 状态的活动

## 测试建议

### 1. 活动管理测试

```python
# 测试 1: 创建激活的活动
POST /events {"status": "active", ...}
# 验证：其他活动状态变为 paused

# 测试 2: 激活现有活动
PATCH /events/2 {"status": "active"}
# 验证：其他活动状态变为 paused

# 测试 3: 获取当前活动活动
GET /events?status=active
# 验证：只返回一个活动
```

### 2. 摊位管理测试

```python
# 测试 1: 不指定 event_id 创建摊位
POST /booths {"name": "摊位1", "class_name": "班级1"}
# 验证：摊位关联到当前激活的活动

# 测试 2: 没有激活活动时创建摊位
# 先暂停所有活动
POST /booths {"name": "摊位2", "class_name": "班级2"}
# 验证：返回 NO_ACTIVE_EVENT 错误

# 测试 3: 列出摊位
GET /booths
# 验证：只返回当前激活活动的摊位
```

### 3. 支付流程测试

```python
# 测试 1: 不指定 event_id 支付
POST /booths/1/pay {"card_uid": "ABC", "amount": 10.0}
# 验证：使用当前激活的活动

# 测试 2: 指定 event_id 支付
POST /booths/1/pay {"event_id": 2, "card_uid": "ABC", "amount": 10.0}
# 验证：使用指定的活动
```

### 4. 安卓端测试

```java
// 测试 1: 不指定 event_id 的支付
BoothPaymentRequest request = new BoothPaymentRequest(cardUid, amount);
// 验证：支付成功

// 测试 2: 指定 event_id 的支付
BoothPaymentRequest request = new BoothPaymentRequest(eventId, cardUid, amount);
// 验证：支付成功
```

## 部署步骤

### 1. 后端部署

```bash
# 1. 拉取最新代码
git pull

# 2. 重启后端服务
bash restart_backend.sh

# 3. 验证服务状态
curl http://localhost:8000/health
```

### 2. 安卓端部署

```bash
# 1. 在 Android Studio 中打开项目
# 2. 同步 Gradle
# 3. 清理并重新构建
./gradlew clean build

# 4. 安装到设备
./gradlew installDebug
```

### 3. 验证部署

```bash
# 1. 检查当前激活的活动
curl http://localhost:8000/events?status=active

# 2. 测试创建摊位（不指定 event_id）
curl -X POST http://localhost:8000/booths \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "测试摊位", "class_name": "测试班级"}'

# 3. 测试列出摊位
curl http://localhost:8000/booths \
  -H "Authorization: Bearer <token>"
```

## 注意事项

### 1. 活动切换

- 激活新活动时，所有其他活动会自动暂停
- 暂停的活动可以随时重新激活
- 建议在活动结束后将状态设置为 `ended` 而不是 `paused`

### 2. 数据隔离

- 每个活动的数据仍然是隔离的
- 参与者在不同活动下有独立的账户
- 摊位和商品都属于特定活动

### 3. 权限控制

- 只有 `super_admin` 和 `event_admin` 可以管理活动
- `booth_cashier` 只能操作自己的摊位
- 权限规则保持不变

## 相关文件

### 后端文件
- `services/event_service.py` - 活动服务
- `routes/booths.py` - 摊位路由
- `schemas/booth.py` - 摊位 Schema
- `core/security.py` - 安全和认证（已修复数据库会话问题）

### 安卓端文件
- `android/app/src/main/java/com/campus/nfcwallet/models/BoothPaymentRequest.java`
- `android/app/src/main/java/com/campus/nfcwallet/ui/CashierActivity.java`

### 文档文件
- `SINGLE_ACTIVE_EVENT_UPGRADE.md` - 本文档

## 总结

本次升级简化了系统的活动管理：

✅ **自动化**：活动状态自动管理，无需手动暂停其他活动  
✅ **简化**：创建摊位和支付时不再需要指定 event_id  
✅ **安全**：确保同一时间只有一个活动处于激活状态  
✅ **兼容**：完全向后兼容，现有代码无需修改  
✅ **灵活**：仍然支持明确指定 event_id 的场景  

系统现在更加易用，减少了操作错误的可能性，同时保持了灵活性和向后兼容性。
