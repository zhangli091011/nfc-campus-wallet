# 收银端快速开始指南

## 前置条件

1. Android Studio 已安装
2. Android SDK API 24+ 已安装
3. 支持 NFC 的 Android 设备（用于测试）
4. 后端服务已启动并可访问

## 配置步骤

### 1. 配置 API 地址

编辑 `android/app/src/main/java/com/campus/nfcwallet/api/APIClient.java`:

```java
private static final String BASE_URL = "http://192.168.1.100:8000/";  // 改为你的服务器地址
```

### 2. 配置签名密钥

编辑 `android/app/src/main/java/com/campus/nfcwallet/ui/CashierActivity.java`:

```java
private static final String SECRET_KEY = "your_secret_key_here";  // 与后端 .env 中的 SECRET_KEY 一致
```

### 3. 配置本地属性（可选）

如果需要配置 SDK 路径，编辑 `android/local.properties`:

```properties
sdk.dir=/path/to/your/Android/Sdk
```

## 编译和安装

### 方法 1: 使用 Android Studio

1. 打开 Android Studio
2. 选择 "Open an Existing Project"
3. 选择 `android` 目录
4. 等待 Gradle 同步完成
5. 连接 Android 设备（启用 USB 调试）
6. 点击 "Run" 按钮（绿色三角形）

### 方法 2: 使用命令行

```bash
cd android

# 编译 Debug 版本
./gradlew assembleDebug

# 安装到设备
./gradlew installDebug

# 或者一步完成
./gradlew installDebug
```

## 使用流程

### 1. 首次登录

1. 启动 App
2. 输入用户名和密码
3. 点击"登录"按钮

**测试账号**（需要在后端创建）:
- 用户名: `cashier1`
- 密码: `password123`
- 角色: `cashier`

### 2. 进入收银页面

登录成功后会自动进入收银页面（需要在代码中指定 booth_id）。

**临时方案**: 在 `BoothSelectionActivity.java` 中硬编码 booth_id:

```java
int boothId = 1;  // 改为你的摊位 ID
```

### 3. 刷卡操作

1. 将 NFC 卡靠近设备背面
2. App 自动读取卡号
3. 自动查询参与者信息和余额
4. 显示参与者姓名和当前余额

### 4. 商品支付

1. 点击商品按钮添加到购物车
2. 调整数量（点击 +/- 按钮）
3. 查看合计金额
4. 点击"扣款"按钮
5. 确认支付
6. 显示支付结果和新余额

### 5. 自定义金额

1. 在"自定义金额"区域输入金额
2. 可选填写备注
3. 点击"扣款"按钮
4. 确认支付

### 6. 充值（仅管理员）

1. 确保登录用户角色为 `admin`
2. 刷卡后会显示"充值"按钮
3. 输入充值金额
4. 点击"充值"按钮
5. 确认充值

## 常见问题

### Q1: 提示"设备不支持 NFC"

**A**: 确保你的测试设备支持 NFC 功能。可以在设备的"设置 > 连接 > NFC"中查看。

### Q2: 提示"请在设置中启用 NFC"

**A**: 进入设备的"设置 > 连接 > NFC"，打开 NFC 开关。

### Q3: 提示"网络错误"

**A**: 检查以下几点:
1. 设备和服务器在同一网络
2. `BASE_URL` 配置正确
3. 后端服务正在运行
4. 防火墙允许访问

### Q4: 提示"签名验证失败"

**A**: 确保 App 中的 `SECRET_KEY` 与后端 `.env` 文件中的 `SECRET_KEY` 完全一致。

### Q5: 提示"参与者不存在或卡未绑定"

**A**: 需要先在后端创建参与者并绑定 NFC 卡:

```bash
# 使用 API 创建参与者
curl -X POST http://localhost:8000/participants \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "event_id": 1,
    "name": "张三",
    "card_uid": "04A1B2C3D4E5F6"
  }'
```

### Q6: 提示"权限不足"

**A**: 确保登录用户有访问该摊位的权限。检查用户的 `role` 和摊位的 `cashier_id`。

### Q7: 商品列表为空

**A**: 需要先在后端为摊位创建商品:

```bash
# 使用 API 创建商品
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "booth_id": 1,
    "name": "可乐",
    "price": 300,
    "enabled": true
  }'
```

## 测试数据准备

### 1. 创建活动

```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{
    "name": "校园文化节",
    "start_date": "2024-05-01",
    "end_date": "2024-05-03",
    "is_active": true
  }'
```

### 2. 创建摊位

```bash
curl -X POST http://localhost:8000/booths \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{
    "event_id": 1,
    "name": "饮料摊",
    "cashier_id": 2,
    "is_active": true
  }'
```

### 3. 创建商品

```bash
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "booth_id": 1,
    "name": "可乐",
    "price": 300,
    "enabled": true
  }'

curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "booth_id": 1,
    "name": "雪碧",
    "price": 300,
    "enabled": true
  }'
```

### 4. 创建参与者并绑定卡

```bash
curl -X POST http://localhost:8000/participants \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "event_id": 1,
    "name": "张三",
    "card_uid": "04A1B2C3D4E5F6",
    "initial_balance": 10000
  }'
```

## 调试技巧

### 1. 查看日志

使用 Android Studio 的 Logcat 查看日志:

```
Filter: com.campus.nfcwallet
Tag: CashierActivity, NFCReader, APIClient
```

### 2. 网络请求调试

在 `APIClient.java` 中已配置 HttpLoggingInterceptor，可以在 Logcat 中看到所有 HTTP 请求和响应。

### 3. NFC 调试

在 `NFCReader.java` 中添加日志:

```java
Log.d("NFCReader", "Card detected: " + uid);
```

### 4. 模拟器测试

**注意**: 模拟器不支持 NFC 功能，必须使用真实设备测试。

## 性能优化建议

1. **图片加载**: 如果添加商品图片，使用 Glide 或 Picasso
2. **列表优化**: RecyclerView 已使用 ViewHolder 模式
3. **网络优化**: 考虑添加请求缓存
4. **离线支持**: 考虑添加本地数据库缓存

## 安全注意事项

1. **生产环境**: 不要在代码中硬编码 SECRET_KEY
2. **HTTPS**: 生产环境必须使用 HTTPS
3. **Token 存储**: SessionManager 使用 SharedPreferences，考虑加密存储
4. **权限检查**: 确保后端有完善的权限验证

## 下一步

1. 完善摊位选择功能
2. 添加交易历史查看
3. 添加统计报表
4. 添加离线模式
5. 添加打印小票功能

## 获取帮助

- 查看完整文档: `CASHIER_TERMINAL_UPGRADE.md`
- 查看 API 文档: `docs/API_DOCUMENTATION.md`
- 查看错误代码: `docs/ERROR_CODES.md`
