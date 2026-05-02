# Android收银端更新总结

## 最新更新（2026-05-02）

### 1. 自动创建参与者功能 ✨

**功能描述：**
当收银员刷一张未注册的NFC卡时，应用会自动弹出对话框，允许收银员现场创建新参与者。

**使用流程：**
1. 收银员刷卡
2. 系统检测到卡片未绑定
3. 弹出对话框提示创建新参与者
4. 收银员输入：
   - 姓名（必填）
   - 班级（可选）
   - 学号（可选）
5. 点击"创建"按钮
6. 系统自动创建参与者并查询余额

**技术实现：**
- `CashierActivity.showCreateParticipantDialog()` - 显示创建对话框
- `CashierActivity.createParticipant()` - 调用API创建参与者
- `WalletAPIService.createParticipant()` - POST /participants API

**优势：**
- ✅ 无需预先导入所有参与者
- ✅ 支持现场注册
- ✅ 提高收银效率
- ✅ 减少管理工作量

### 2. 余额查询API升级 🔄

**变更说明：**
从旧的签名验证模式升级到新的活动模式。

**旧方式（已弃用）：**
```
GET /balance?uid=xxx&timestamp=xxx&signature=xxx
```

**新方式：**
```
GET /balance?event_id=1&card_uid=xxx
```

**技术实现：**
- `WalletAPIService.getBalanceByEvent()` - 新的余额查询方法
- `CashierActivity.queryBalance()` - 使用event_id和card_uid查询

**优势：**
- ✅ 不需要签名计算
- ✅ 支持多活动场景
- ✅ 更简单的API调用
- ✅ 更好的安全性（使用JWT认证）

## 部署步骤

### 服务器端

```bash
# 1. 拉取最新代码
cd ~/nfc-campus-wallet
git pull origin main

# 2. 重启服务
./fix_server.sh
```

### Android端

1. **编译新APK：**
   ```bash
   cd android
   ./gradlew assembleDebug
   ```

2. **APK位置：**
   ```
   android/app/build/outputs/apk/debug/app-debug.apk
   ```

3. **安装到设备：**
   ```bash
   adb install -r app-debug.apk
   ```

## 测试场景

### 场景1：创建新参与者

1. 登录收银端
2. 刷一张未注册的卡（例如：ABCD1234）
3. 在弹出的对话框中输入：
   - 姓名：测试用户
   - 班级：测试班级
   - 学号：TEST001
4. 点击"创建"
5. 验证：
   - ✅ 参与者创建成功
   - ✅ 显示余额（初始为0）
   - ✅ 可以进行充值/扣款操作

### 场景2：查询已存在参与者

1. 刷已注册的卡（例如：2BC8694C）
2. 验证：
   - ✅ 显示参与者姓名（张力）
   - ✅ 显示当前余额
   - ✅ 可以进行交易

### 场景3：取消创建

1. 刷未注册的卡
2. 在对话框中点击"取消"
3. 验证：
   - ✅ 对话框关闭
   - ✅ 卡片信息清除
   - ✅ 可以刷下一张卡

## API变更

### 新增API

#### POST /participants
创建新参与者

**请求：**
```json
{
  "name": "张三",
  "card_uid": "ABCD1234",
  "class_name": "高一(1)班",
  "student_no": "2024001",
  "status": "active"
}
```

**响应：**
```json
{
  "id": 1,
  "name": "张三",
  "card_uid": "ABCD1234",
  "class_name": "高一(1)班",
  "student_no": "2024001",
  "status": "active",
  "created_at": "2026-05-02T10:00:00"
}
```

### 更新API

#### GET /balance
新增活动模式参数

**旧方式（已弃用）：**
```
GET /balance?uid=xxx&timestamp=xxx&signature=xxx
```

**新方式：**
```
GET /balance?event_id=1&card_uid=xxx
```

## 配置要求

### 服务器端

1. **数据库表：**
   - ✅ participants 表已存在
   - ✅ accounts 表已存在
   - ✅ events 表已存在

2. **活动配置：**
   - 至少创建一个活动（event_id=1）
   - 活动状态为 active

3. **用户权限：**
   - 收银员需要有创建参与者的权限
   - 使用JWT token认证

### Android端

1. **API配置：**
   - 在 `local.properties` 中配置正确的 `API_BASE_URL`
   - 例如：`API_BASE_URL=http://your-server:8001/`

2. **活动配置：**
   - 在 `CashierActivity` 中配置 `EVENT_ID`
   - 默认为 1

## 已知问题

### 1. 余额为0的新参与者

**问题：** 新创建的参与者余额为0，无法进行消费。

**解决方案：**
- 收银员需要先为新参与者充值
- 或者在创建时设置初始余额（需要后端支持）

### 2. 活动未创建

**问题：** 如果数据库中没有活动，余额查询会失败。

**解决方案：**
```bash
# 在服务器上创建活动
curl -X POST "http://localhost:8001/events" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "校园活动",
    "start_date": "2026-05-01T00:00:00",
    "end_date": "2026-12-31T23:59:59",
    "status": "active"
  }'
```

## 下一步计划

- [ ] 支持批量导入参与者
- [ ] 添加参与者照片
- [ ] 支持参与者信息编辑
- [ ] 添加参与者搜索功能
- [ ] 支持离线模式

## 技术支持

如有问题，请查看：
- [API文档](docs/API_DOCUMENTATION.md)
- [部署指南](DEPLOYMENT_GUIDE.md)
- [服务器设置](SERVER_SETUP.md)
