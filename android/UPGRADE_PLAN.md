# Android 收银端升级计划

## 升级目标
将基础版 NFC 钱包 App 升级为活动收银端，支持完整的摊位收银功能。

## 新增功能

### 1. 登录功能
- 用户名密码登录
- JWT Token 管理
- 登录态持久化
- 自动登录

### 2. 收银主界面
- 当前活动信息展示
- 当前摊位信息展示
- 登录收银员信息
- 刷卡后显示参与者信息
- 实时余额显示
- 商品快捷按钮区
- 购物车功能
- 自定义金额输入
- 多种操作按钮（查询余额、扣款、充值）

### 3. 商品管理
- 获取摊位商品列表
- 商品快捷选择
- 购物车数量管理
- 自动金额计算

### 4. 交易处理
- 商品模式交易
- 自定义金额交易
- 交易结果展示
- 余额变更提示

### 5. 错误处理
- 网络错误
- 签名错误
- 权限错误
- 余额不足
- 活动关闭
- 卡未绑定
- 用户不存在

## 新增文件

### Models
- `LoginRequest.java` - 登录请求
- `LoginResponse.java` - 登录响应
- `UserInfo.java` - 用户信息
- `EventInfo.java` - 活动信息
- `BoothInfo.java` - 摊位信息
- `ParticipantInfo.java` - 参与者信息
- `Product.java` - 商品信息
- `ProductListResponse.java` - 商品列表响应
- `CartItem.java` - 购物车项
- `BoothPaymentRequest.java` - 摊位支付请求

### API
- 扩展 `WalletAPIService.java` 添加新接口

### UI
- `LoginActivity.java` - 登录界面
- `CashierActivity.java` - 收银主界面（替代 MainActivity）
- `ProductAdapter.java` - 商品列表适配器
- `CartAdapter.java` - 购物车适配器

### Utils
- `SessionManager.java` - 登录态管理
- `ErrorHandler.java` - 统一错误处理

### Layouts
- `activity_login.xml` - 登录界面布局
- `activity_cashier.xml` - 收银界面布局
- `item_product.xml` - 商品项布局
- `item_cart.xml` - 购物车项布局

## 保留功能
- NFC 读取逻辑（NFCReader.java）
- 签名生成逻辑（SignatureGenerator.java）
- API Client 基础设施（APIClient.java）

## 技术要点
1. 使用 SharedPreferences 存储 JWT Token
2. 使用 RecyclerView 展示商品和购物车
3. 使用 Retrofit 进行 API 调用
4. 保持现有的 NFC 读取机制
5. 保持现有的签名验证机制
