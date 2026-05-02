# 摊位收款账号设计文档

## 需求概述

为每个摊位创建一个专用的收款账号，用于收集营业额：
- ✅ 可以在安卓端管理（添加、查看）
- ✅ 只能接收付款（被扣款），不能充值
- ✅ 用于统计摊位营业额
- ✅ 与普通参与者账号区分

## 设计方案

### 方案选择：使用特殊类型的Participant

**优点**：
- 复用现有的Participant和Account体系
- 无需修改数据库结构
- 利用现有的交易和账本逻辑
- 简单且易于维护

**实现方式**：
1. 为每个摊位创建一个特殊的Participant
2. 使用特殊的命名规则：`BOOTH_{booth_id}_{booth_name}`
3. 使用特殊的卡号规则：`BOOTH_{booth_id}`
4. 在Participant中添加`participant_type`字段区分类型

### 数据库修改

#### 1. 修改Participant表
添加`participant_type`字段：
```sql
ALTER TABLE participants 
ADD COLUMN participant_type VARCHAR(20) DEFAULT 'person' NOT NULL;

ALTER TABLE participants
ADD CONSTRAINT chk_participant_type 
CHECK (participant_type IN ('person', 'booth_collection'));

CREATE INDEX idx_participants_type ON participants(participant_type);
```

#### 2. 修改Booth表
添加`collection_participant_id`字段：
```sql
ALTER TABLE booths
ADD COLUMN collection_participant_id INTEGER;

ALTER TABLE booths
ADD CONSTRAINT fk_booth_collection_participant
FOREIGN KEY (collection_participant_id) 
REFERENCES participants(id) ON DELETE SET NULL;
```

### 业务逻辑

#### 1. 创建摊位时自动创建收款账号
```python
def create_booth_with_collection_account(event_id, name, class_name):
    # 1. 创建摊位
    booth = Booth(event_id=event_id, name=name, class_name=class_name)
    db.add(booth)
    db.flush()  # 获取booth.id
    
    # 2. 创建收款参与者
    collection_participant = Participant(
        name=f"【收款】{name}",
        card_uid=f"BOOTH_{booth.id}",
        participant_type='booth_collection',
        status='active'
    )
    db.add(collection_participant)
    db.flush()
    
    # 3. 关联摊位和收款参与者
    booth.collection_participant_id = collection_participant.id
    
    # 4. 创建账户
    account = Account(
        participant_id=collection_participant.id,
        event_id=event_id,
        balance=0
    )
    db.add(account)
    
    db.commit()
    return booth
```

#### 2. 支付时可选择付款到收款账号
修改`CashierActivity`，添加选项：
- 普通支付：从参与者账户扣款
- 收款支付：从参与者账户扣款，同时给摊位收款账号充值

#### 3. 权限控制
- 收款账号不能充值（在充值API中检查participant_type）
- 收款账号可以被扣款（用于退款或调整）
- 只有管理员可以操作收款账号

### API修改

#### 1. 创建摊位API
```python
POST /booths
{
    "event_id": 1,
    "name": "美食摊",
    "class_name": "高一(1)班",
    "create_collection_account": true  # 新增参数
}

Response:
{
    "id": 1,
    "name": "美食摊",
    "class_name": "高一(1)班",
    "collection_participant_id": 100,
    "collection_account": {
        "participant_id": 100,
        "participant_name": "【收款】美食摊",
        "card_uid": "BOOTH_1",
        "balance": 0.00
    }
}
```

#### 2. 查询摊位收款账号
```python
GET /booths/{booth_id}/collection-account

Response:
{
    "participant_id": 100,
    "participant_name": "【收款】美食摊",
    "card_uid": "BOOTH_1",
    "balance": 1500.00,
    "transaction_count": 50
}
```

#### 3. 修改充值API
```python
# 在充值时检查participant_type
if participant.participant_type == 'booth_collection':
    raise ValidationError("收款账号不能充值")
```

#### 4. 新增收款支付API
```python
POST /payment/to-collection
{
    "event_id": 1,
    "card_uid": "A1B2C3D4",  # 付款人
    "booth_id": 1,
    "amount": 25.00,
    "product_id": 5
}

# 执行两笔交易：
# 1. 从付款人扣款
# 2. 给收款账号充值（记录为特殊类型的交易）
```

### 安卓端修改

#### 1. 在BoothSelectionActivity显示收款账号
```java
// 显示摊位信息时，同时显示收款账号余额
TextView collectionBalanceText;
collectionBalanceText.setText(
    String.format("收款账号余额: ¥%.2f", collectionBalance)
);
```

#### 2. 在CashierActivity添加收款模式切换
```java
// 添加开关：是否使用收款账号
Switch useCollectionAccountSwitch;

// 支付时根据开关决定是否同时给收款账号充值
if (useCollectionAccountSwitch.isChecked()) {
    // 调用收款支付API
    processPaymentToCollection();
} else {
    // 调用普通支付API
    processPayment();
}
```

#### 3. 添加收款账号管理界面
新建`CollectionAccountActivity`：
- 显示收款账号信息
- 显示收款交易历史
- 显示统计数据（总收款、交易笔数）

### Web管理后台修改

#### 1. 摊位管理页面
- 显示收款账号信息
- 显示收款账号余额
- 提供查看收款交易历史的入口

#### 2. 参与者管理页面
- 过滤掉收款账号（默认不显示）
- 添加"显示收款账号"选项

#### 3. 报表页面
- 摊位报表中包含收款账号余额
- 新增"收款账号汇总"报表

## 实施步骤

### Phase 1: 数据库和模型修改
1. ✅ 创建数据库迁移脚本
2. ✅ 修改Participant模型
3. ✅ 修改Booth模型
4. ✅ 运行迁移

### Phase 2: 后端API开发
1. ✅ 修改创建摊位API
2. ✅ 添加查询收款账号API
3. ✅ 修改充值API（添加权限检查）
4. ✅ 添加收款支付API
5. ✅ 添加收款账号管理服务

### Phase 3: 安卓端开发
1. ⏳ 修改BoothSelectionActivity
2. ⏳ 修改CashierActivity
3. ⏳ 创建CollectionAccountActivity
4. ⏳ 测试

### Phase 4: Web管理后台开发
1. ⏳ 修改摊位管理页面
2. ⏳ 修改参与者管理页面
3. ⏳ 添加收款账号报表
4. ⏳ 测试

### Phase 5: 测试和部署
1. ⏳ 集成测试
2. ⏳ 用户验收测试
3. ⏳ 部署到生产环境
4. ⏳ 编写用户文档

## 注意事项

### 1. 数据一致性
- 创建摊位时必须同时创建收款账号
- 删除摊位时需要处理收款账号（软删除或保留）

### 2. 权限控制
- 收款账号只能由管理员操作
- 普通收银员不能直接操作收款账号

### 3. 报表统计
- 摊位营业额 = 收款账号余额 + 已提现金额
- 需要记录提现操作

### 4. 向后兼容
- 现有摊位需要补充创建收款账号
- 提供迁移脚本

## 替代方案（不推荐）

### 方案2：在Booth表中直接添加balance字段
**缺点**：
- 无法利用现有的交易和账本逻辑
- 需要重新实现余额管理
- 无法使用NFC卡查询余额

### 方案3：创建新的CollectionAccount表
**缺点**：
- 增加系统复杂度
- 需要实现新的交易逻辑
- 代码重复

## 总结

推荐使用**方案1**（特殊类型的Participant），因为：
- ✅ 复用现有逻辑，开发成本低
- ✅ 保持系统一致性
- ✅ 易于维护和扩展
- ✅ 支持NFC卡操作（可选）
