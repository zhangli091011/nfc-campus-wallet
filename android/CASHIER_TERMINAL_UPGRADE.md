# Android 收银端升级文档

## 概述

本次升级将基础版 NFC 钱包 App 升级为功能完整的"活动收银端"，支持商品选择、购物车、自定义金额等功能。

## 升级内容

### 一、新增 Activity

#### 1. LoginActivity (登录页面)
- **路径**: `ui/LoginActivity.java`
- **布局**: `layout/activity_login.xml`
- **功能**:
  - 用户名密码登录
  - JWT Token 管理
  - 自动跳转到摊位选择或收银页面

#### 2. BoothSelectionActivity (摊位选择页面)
- **路径**: `ui/BoothSelectionActivity.java`
- **布局**: `layout/activity_booth_selection.xml`
- **功能**:
  - 显示用户可操作的摊位列表
  - 选择摊位后进入收银页面

#### 3. CashierActivity (收银页面 - 核心)
- **路径**: `ui/CashierActivity.java`
- **布局**: `layout/activity_cashier.xml`
- **功能**:
  - 显示活动名称、摊位名称、收银员信息
  - NFC 刷卡自动查询参与者和余额
  - 商品快捷按钮（网格布局）
  - 购物车管理（增删改）
  - 自定义金额输入
  - 支付和充值功能
  - 详细的错误提示

### 二、新增 Adapter

#### 1. ProductAdapter
- **路径**: `ui/ProductAdapter.java`
- **布局**: `layout/item_product.xml`
- **功能**: 商品网格展示

#### 2. CartAdapter
- **路径**: `ui/CartAdapter.java`
- **布局**: `layout/item_cart.xml`
- **功能**: 购物车列表展示，支持数量调整

### 三、更新的文件

#### 1. ErrorHandler
- **路径**: `utils/ErrorHandler.java`
- **更新**: 添加 `getErrorMessage(Response)` 方法，支持从 API 响应解析错误

#### 2. AndroidManifest.xml
- 将 LoginActivity 设为启动页
- 添加 CashierActivity 和 BoothSelectionActivity
- MainActivity 保留为 legacy 模式

#### 3. strings.xml
- 添加中文字符串资源
- 添加所有错误提示文本

#### 4. colors.xml
- 添加 `background_gray`, `text_primary`, `text_secondary`, `divider_gray`

### 四、保留的现有功能

#### 1. NFC 读取模块
- **路径**: `nfc/NFCReader.java`
- **保持不变**: 完整保留现有的 NFC 读取逻辑

#### 2. 签名生成模块
- **路径**: `signature/SignatureGenerator.java`
- **保持不变**: 完整保留现有的签名逻辑

#### 3. API 服务
- **路径**: `api/WalletAPIService.java`
- **保持不变**: 已包含所有需要的 API 端点

#### 4. 会话管理
- **路径**: `utils/SessionManager.java`
- **保持不变**: 已支持 Token 和用户信息管理

## 完整目录结构

```
android/app/src/main/
├── AndroidManifest.xml                    # 更新：添加新 Activity
├── java/com/campus/nfcwallet/
│   ├── api/
│   │   ├── APIClient.java                 # 保留
│   │   └── WalletAPIService.java          # 保留
│   ├── models/
│   │   ├── BalanceResponse.java           # 保留
│   │   ├── BoothInfo.java                 # 保留
│   │   ├── BoothPaymentRequest.java       # 保留
│   │   ├── CartItem.java                  # 保留
│   │   ├── ErrorResponse.java             # 保留
│   │   ├── EventInfo.java                 # 保留
│   │   ├── LoginRequest.java              # 保留
│   │   ├── LoginResponse.java             # 保留
│   │   ├── ParticipantInfo.java           # 保留
│   │   ├── PaymentRequest.java            # 保留
│   │   ├── Product.java                   # 保留
│   │   ├── RechargeRequest.java           # 保留
│   │   ├── Transaction.java               # 保留
│   │   ├── TransactionHistoryResponse.java # 保留
│   │   ├── TransactionResponse.java       # 保留
│   │   └── UserInfo.java                  # 保留
│   ├── nfc/
│   │   └── NFCReader.java                 # 保留
│   ├── signature/
│   │   └── SignatureGenerator.java        # 保留
│   ├── ui/
│   │   ├── LoginActivity.java             # 新增
│   │   ├── BoothSelectionActivity.java    # 新增
│   │   ├── CashierActivity.java           # 新增 (核心)
│   │   ├── ProductAdapter.java            # 新增
│   │   ├── CartAdapter.java               # 新增
│   │   ├── MainActivity.java              # 保留 (legacy)
│   │   ├── TransactionAdapter.java        # 保留
│   │   └── TransactionHistoryActivity.java # 保留
│   └── utils/
│       ├── ErrorHandler.java              # 更新
│       └── SessionManager.java            # 保留
└── res/
    ├── layout/
    │   ├── activity_login.xml             # 新增
    │   ├── activity_booth_selection.xml   # 新增
    │   ├── activity_cashier.xml           # 新增
    │   ├── item_product.xml               # 新增
    │   ├── item_cart.xml                  # 新增
    │   ├── activity_main.xml              # 保留
    │   ├── activity_transaction_history.xml # 保留
    │   └── item_transaction.xml           # 保留
    ├── values/
    │   ├── strings.xml                    # 更新
    │   ├── colors.xml                     # 更新
    │   └── themes.xml                     # 保留
    └── drawable/                          # 保留所有图标
```

## 业务流程

### 1. 启动流程
```
App 启动
  ↓
LoginActivity (检查登录状态)
  ↓
已登录? → BoothSelectionActivity → CashierActivity
  ↓
未登录? → 显示登录表单
```

### 2. 刷卡流程
```
用户刷 NFC 卡
  ↓
读取 card_uid
  ↓
调用 GET /participants/by-card/{card_uid}
  ↓
显示参与者姓名
  ↓
自动调用 GET /balance?uid=...
  ↓
显示余额
  ↓
显示商品区和操作按钮
```

### 3. 商品支付流程
```
用户点击商品
  ↓
加入购物车
  ↓
调整数量
  ↓
点击"扣款"按钮
  ↓
确认对话框
  ↓
调用 POST /booths/{booth_id}/pay
  ↓
显示结果和新余额
  ↓
清空购物车
```

### 4. 自定义金额流程
```
用户输入金额
  ↓
可选填写备注
  ↓
点击"扣款"或"充值"
  ↓
确认对话框
  ↓
调用相应 API
  ↓
显示结果
```

## 错误处理

### 错误类型分类

#### 1. 网络错误
- 显示: "网络错误"
- 处理: Toast + 状态文本

#### 2. 认证错误
- `TOKEN_EXPIRED`: "登录已过期，请重新登录"
- `AUTHENTICATION_REQUIRED`: "需要登录"
- 处理: 跳转到登录页

#### 3. 权限错误
- `PERMISSION_DENIED`: "权限不足"
- `BOOTH_ACCESS_DENIED`: "无权访问此摊位"
- 处理: Toast + 禁用操作

#### 4. 业务错误
- `INSUFFICIENT_FUNDS`: "余额不足"
- `EVENT_INACTIVE`: "活动未开启"
- `BOOTH_INACTIVE`: "摊位未开启"
- `PARTICIPANT_NOT_FOUND`: "参与者不存在或卡未绑定"
- 处理: Toast + 状态文本

#### 5. 签名错误
- `SIGNATURE_VERIFICATION_FAILED`: "签名验证失败"
- `TIMESTAMP_EXPIRED`: "请求已过期"
- 处理: Toast + 重试提示

## API 端点使用

### 认证相关
- `POST /auth/login` - 用户登录
- `GET /auth/me` - 获取当前用户信息

### 活动和摊位
- `GET /events/{event_id}` - 获取活动信息
- `GET /booths/{booth_id}` - 获取摊位信息
- `GET /products?booth_id={booth_id}&enabled=true` - 获取商品列表

### 参与者和余额
- `GET /participants/by-card/{card_uid}` - 通过卡号查询参与者
- `GET /balance?uid={uid}&timestamp={ts}&signature={sig}` - 查询余额

### 交易
- `POST /booths/{booth_id}/pay` - 摊位支付（支持购物车）
- `POST /recharge` - 充值（仅管理员）

## 配置说明

### 1. API Base URL
在 `APIClient.java` 中配置:
```java
private static final String BASE_URL = "http://your-server:8000/";
```

### 2. Secret Key
在 `CashierActivity.java` 中配置:
```java
private static final String SECRET_KEY = "your_secret_key";
```

### 3. Booth ID
启动 CashierActivity 时传入:
```java
Intent intent = new Intent(this, CashierActivity.class);
intent.putExtra("booth_id", 1);
startActivity(intent);
```

## 权限说明

### 必需权限
- `android.permission.NFC` - NFC 读取
- `android.permission.INTERNET` - 网络请求
- `android.permission.ACCESS_NETWORK_STATE` - 网络状态检查

### NFC 硬件要求
- `android.hardware.nfc` (required=true)

## 测试建议

### 1. 登录测试
- 正确的用户名密码
- 错误的用户名密码
- 网络断开情况

### 2. NFC 测试
- 刷已绑定的卡
- 刷未绑定的卡
- 快速重复刷卡

### 3. 支付测试
- 商品模式支付
- 自定义金额支付
- 余额不足情况
- 活动/摊位关闭情况

### 4. 权限测试
- 普通用户不显示充值按钮
- 管理员显示充值按钮
- 无权限访问摊位

## 升级步骤

1. **备份现有代码**
   ```bash
   cp -r android android_backup
   ```

2. **添加新文件**
   - 复制所有新增的 Java 文件
   - 复制所有新增的 XML 布局文件

3. **更新现有文件**
   - 更新 `AndroidManifest.xml`
   - 更新 `strings.xml`
   - 更新 `colors.xml`
   - 更新 `ErrorHandler.java`

4. **配置 API**
   - 在 `APIClient.java` 中设置正确的 BASE_URL
   - 在 `CashierActivity.java` 中设置正确的 SECRET_KEY

5. **编译测试**
   ```bash
   cd android
   ./gradlew assembleDebug
   ```

6. **安装测试**
   ```bash
   ./gradlew installDebug
   ```

## 注意事项

1. **保持向后兼容**: MainActivity 保留为 legacy 模式，不影响现有功能
2. **NFC 逻辑不变**: 完全保留现有的 NFC 读取逻辑
3. **签名逻辑不变**: 完全保留现有的签名生成逻辑
4. **增量升级**: 所有新功能都是增量添加，不删除现有代码

## 版本信息

- **当前版本**: v1.1.0
- **升级类型**: 功能增强（收银端）
- **兼容性**: 向后兼容 v1.0.0

## 后续优化建议

1. 添加离线缓存功能
2. 添加交易记录本地存储
3. 优化商品图片显示
4. 添加打印小票功能
5. 添加统计报表功能
