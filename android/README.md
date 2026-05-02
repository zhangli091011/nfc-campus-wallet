# NFC Campus E-Wallet - Android Client

这是NFC校园电子钱包系统的Android客户端应用。

## 项目结构

```
android/
├── app/
│   ├── build.gradle                    # 应用级Gradle配置
│   ├── proguard-rules.pro             # ProGuard混淆规则
│   └── src/main/
│       ├── AndroidManifest.xml        # 应用清单文件
│       ├── java/com/campus/nfcwallet/
│       │   ├── api/                   # API客户端
│       │   │   ├── APIClient.java     # Retrofit配置
│       │   │   └── WalletAPIService.java  # API接口定义
│       │   ├── models/                # 数据模型
│       │   │   ├── BalanceResponse.java
│       │   │   ├── TransactionResponse.java
│       │   │   ├── Transaction.java
│       │   │   ├── PaymentRequest.java
│       │   │   ├── RechargeRequest.java
│       │   │   └── ErrorResponse.java
│       │   ├── nfc/                   # NFC读卡器
│       │   │   └── NFCReader.java
│       │   ├── signature/             # 签名生成
│       │   │   └── SignatureGenerator.java
│       │   └── ui/                    # UI界面
│       │       ├── MainActivity.java  # 主界面（需要创建）
│       │       └── TransactionHistoryActivity.java  # 交易历史（需要创建）
│       └── res/                       # 资源文件
│           ├── layout/
│           │   ├── activity_main.xml
│           │   └── activity_transaction_history.xml  # 需要创建
│           ├── values/
│           │   ├── strings.xml
│           │   ├── colors.xml
│           │   └── themes.xml
│           └── xml/
│               ├── nfc_tech_filter.xml
│               ├── backup_rules.xml
│               └── data_extraction_rules.xml
├── build.gradle                       # 项目级Gradle配置
├── settings.gradle                    # Gradle设置
└── gradle.properties                  # Gradle属性

```

## 如何在Android Studio中打开

1. **打开Android Studio**

2. **导入项目**:
   - 选择 `File` -> `Open`
   - 导航到 `android` 文件夹
   - 点击 `OK`

3. **等待Gradle同步**:
   - Android Studio会自动下载依赖
   - 这可能需要几分钟时间

4. **配置后端URL**:
   - 打开 `app/src/main/java/com/campus/nfcwallet/api/APIClient.java`
   - 修改 `BASE_URL` 常量:
     - 模拟器: `http://10.0.2.2:8000/`
     - 真机: `http://YOUR_COMPUTER_IP:8000/`

5. **配置密钥**:
   - 在 `MainActivity.java` 中设置 `SECRET_KEY`
   - 必须与后端的 `SECRET_KEY` 一致

## ✅ 所有文件已创建完成

所有必要的Android代码文件已经创建完成！包括：

1. ✅ **MainActivity.java** - 主界面逻辑
2. ✅ **TransactionHistoryActivity.java** - 交易历史界面
3. ✅ **TransactionAdapter.java** - 交易列表适配器
4. ✅ **activity_main.xml** - 主界面布局
5. ✅ **activity_transaction_history.xml** - 交易历史布局
6. ✅ **item_transaction.xml** - 交易项布局
7. ✅ 所有数据模型、API客户端、NFC读取器、签名生成器

## 依赖项

项目使用以下主要依赖：

- **AndroidX**: 核心Android库
- **Material Components**: Material Design组件
- **Retrofit 2.9.0**: HTTP客户端
- **OkHttp 4.12.0**: HTTP引擎
- **Gson 2.10.1**: JSON解析
- **JUnit 4.13.2**: 单元测试
- **Mockito 5.3.1**: Mock框架
- **jqwik 1.7.4**: 属性测试

## 功能特性

- ✅ NFC卡片读取（ISO14443兼容）
- ✅ SHA256签名生成
- ✅ 余额查询
- ✅ 支付处理
- ✅ 充值处理（管理员）
- ✅ 交易历史查看
- ✅ 错误处理和重试逻辑
- ✅ Material Design UI

## 最低要求

- **Android SDK**: 21 (Android 5.0 Lollipop)
- **目标SDK**: 34 (Android 14)
- **NFC硬件**: 必需
- **网络权限**: 必需

## 测试

运行单元测试:
```bash
./gradlew test
```

运行仪器测试:
```bash
./gradlew connectedAndroidTest
```

## 注意事项

1. **NFC权限**: 应用需要NFC权限，设备必须支持NFC
2. **网络配置**: 确保后端服务器正在运行
3. **密钥安全**: 在生产环境中，不要硬编码密钥
4. **HTTPS**: 生产环境应使用HTTPS而不是HTTP

## 下一步

1. 我会继续创建剩余的UI文件
2. 然后你可以在Android Studio中打开项目
3. 连接Android设备或启动模拟器
4. 运行应用并测试NFC功能


## 🚀 快速开始指南

### 步骤 1: 准备环境

1. **安装Android Studio**
   - 下载地址: https://developer.android.com/studio
   - 安装最新版本（推荐 Android Studio Hedgehog 或更新版本）

2. **配置Android SDK**
   - 打开Android Studio
   - 进入 `Tools` -> `SDK Manager`
   - 确保安装了 Android SDK Platform 34 和 Android SDK Build-Tools

### 步骤 2: 导入项目

1. **打开Android Studio**

2. **导入项目**:
   - 选择 `File` -> `Open`
   - 导航到 `android` 文件夹（包含 build.gradle 的文件夹）
   - 点击 `OK`

3. **等待Gradle同步**:
   - Android Studio会自动下载依赖
   - 首次同步可能需要5-10分钟
   - 确保网络连接正常

4. **创建 local.properties 文件**:
   - 复制 `local.properties.example` 为 `local.properties`
   - 更新 `sdk.dir` 为你的Android SDK路径
   - 或者让Android Studio自动创建

### 步骤 3: 配置应用

1. **配置后端URL**:
   
   打开 `app/src/main/java/com/campus/nfcwallet/api/APIClient.java`
   
   修改 `BASE_URL`:
   ```java
   // 如果使用Android模拟器
   private static final String BASE_URL = "http://10.0.2.2:8000/";
   
   // 如果使用真实设备，替换为你的电脑IP地址
   // private static final String BASE_URL = "http://192.168.1.100:8000/";
   ```

2. **配置密钥**:
   
   打开 `app/src/main/java/com/campus/nfcwallet/ui/MainActivity.java`
   
   修改 `SECRET_KEY`:
   ```java
   // 必须与后端的SECRET_KEY完全一致
   private static final String SECRET_KEY = "your_secret_key_here";
   ```

### 步骤 4: 运行应用

#### 选项 A: 使用Android模拟器

1. **创建虚拟设备**:
   - 点击 `Tools` -> `Device Manager`
   - 点击 `Create Device`
   - 选择一个设备（推荐 Pixel 6）
   - 选择系统镜像（推荐 API 34）
   - 完成创建

2. **启动模拟器**:
   - 在Device Manager中点击启动按钮
   - 等待模拟器完全启动

3. **运行应用**:
   - 点击工具栏的绿色运行按钮（▶️）
   - 或按 `Shift + F10`

**注意**: 模拟器不支持真实的NFC硬件，你需要使用真实设备测试NFC功能。

#### 选项 B: 使用真实Android设备（推荐）

1. **启用开发者选项**:
   - 进入 `设置` -> `关于手机`
   - 连续点击 `版本号` 7次
   - 返回设置，找到 `开发者选项`

2. **启用USB调试**:
   - 在开发者选项中启用 `USB调试`
   - 启用 `USB安装`（如果有）

3. **连接设备**:
   - 用USB线连接手机到电脑
   - 在手机上允许USB调试授权

4. **运行应用**:
   - 在Android Studio顶部选择你的设备
   - 点击运行按钮（▶️）

5. **启用NFC**:
   - 确保设备支持NFC
   - 进入 `设置` -> `连接设备` -> `NFC`
   - 启用NFC功能

### 步骤 5: 测试应用

1. **启动后端服务器**:
   ```bash
   cd /path/to/backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **测试NFC读取**:
   - 打开应用
   - 将NFC卡靠近手机背面
   - 应该能看到卡片UID和余额

3. **测试支付**:
   - 读取卡片后
   - 输入金额
   - 点击"Pay"按钮
   - 查看交易结果

4. **测试充值**:
   - 读取卡片后
   - 输入金额
   - 点击"Recharge (Admin)"按钮
   - 查看交易结果

5. **查看交易历史**:
   - 读取卡片后
   - 点击"View History"按钮
   - 查看交易记录列表

## 📱 应用功能

### 主界面 (MainActivity)

- **NFC卡片读取**: 自动检测并读取ISO14443兼容的NFC卡
- **余额查询**: 显示当前卡片余额
- **支付功能**: 输入金额并完成支付交易
- **充值功能**: 管理员可以为卡片充值
- **实时反馈**: 显示交易状态和结果
- **自动清除**: 5秒后自动清除状态消息

### 交易历史界面 (TransactionHistoryActivity)

- **交易列表**: 显示所有交易记录
- **交易详情**: 显示类型、金额、余额、时间
- **颜色区分**: 支付显示红色，充值显示绿色
- **商户信息**: 显示商户ID（如果有）

## 🔧 故障排除

### 问题 1: Gradle同步失败

**解决方案**:
- 检查网络连接
- 尝试使用VPN
- 清除Gradle缓存: `File` -> `Invalidate Caches` -> `Invalidate and Restart`

### 问题 2: 无法连接后端

**解决方案**:
- 确保后端服务器正在运行
- 检查防火墙设置
- 对于真实设备，确保手机和电脑在同一WiFi网络
- 检查BASE_URL配置是否正确

### 问题 3: NFC不工作

**解决方案**:
- 确保设备支持NFC（检查设置中是否有NFC选项）
- 确保NFC已启用
- 尝试将卡片靠近手机背面不同位置
- 检查AndroidManifest.xml中的NFC权限

### 问题 4: 签名验证失败

**解决方案**:
- 确保Android应用和后端的SECRET_KEY完全一致
- 检查时间戳是否在60秒窗口内
- 确保设备时间正确

### 问题 5: 编译错误（图标资源缺失）

**错误信息**: `resource mipmap/ic_launcher not found`

**解决方案**:
- 已修复！所有必需的图标资源已创建
- 如果仍有问题：
  1. `Build` -> `Clean Project`
  2. `Build` -> `Rebuild Project`
  3. 重新运行应用
- 查看 `ICON_FIX.md` 了解详情

### 问题 6: 编译错误

**解决方案**:
- 清理项目: `Build` -> `Clean Project`
- 重新构建: `Build` -> `Rebuild Project`
- 同步Gradle: `File` -> `Sync Project with Gradle Files`

## 📝 开发建议

### 调试技巧

1. **查看日志**:
   - 打开 `Logcat` 窗口（底部工具栏）
   - 过滤标签: `MainActivity`, `APIClient`, `NFCReader`

2. **网络调试**:
   - OkHttp日志已启用，可以在Logcat中看到所有HTTP请求和响应

3. **断点调试**:
   - 在代码行号左侧点击设置断点
   - 使用Debug模式运行（🐛图标）

### 代码修改建议

1. **修改UI样式**:
   - 编辑 `res/values/colors.xml` 修改颜色
   - 编辑 `res/values/strings.xml` 修改文本
   - 编辑布局文件修改界面

2. **添加新功能**:
   - 在 `WalletAPIService.java` 添加新的API接口
   - 在 `MainActivity.java` 添加新的业务逻辑
   - 创建新的Activity处理新功能

3. **修改网络配置**:
   - 在 `APIClient.java` 中修改超时时间
   - 修改重试逻辑
   - 添加请求拦截器

## 🔐 安全注意事项

1. **不要硬编码密钥**:
   - 在生产环境中，使用Android Keystore存储密钥
   - 或从安全的配置服务器获取密钥

2. **使用HTTPS**:
   - 生产环境必须使用HTTPS
   - 修改 `BASE_URL` 为 `https://` 开头

3. **证书固定**:
   - 考虑实现SSL证书固定防止中间人攻击

4. **混淆代码**:
   - 发布版本启用ProGuard混淆
   - 编辑 `proguard-rules.pro` 配置混淆规则

## 📚 相关文档

- [Android开发文档](https://developer.android.com/docs)
- [Retrofit文档](https://square.github.io/retrofit/)
- [Material Design指南](https://material.io/design)
- [NFC开发指南](https://developer.android.com/guide/topics/connectivity/nfc)

## 🎯 下一步计划

- [ ] 添加用户认证
- [ ] 实现离线模式
- [ ] 添加交易统计图表
- [ ] 支持多语言
- [ ] 添加生物识别认证
- [ ] 实现推送通知

## 💡 提示

- 第一次运行可能需要较长时间编译
- 建议使用真实设备测试NFC功能
- 保持Android Studio和Gradle插件更新
- 定期清理项目缓存以避免问题

祝你开发顺利！🎉
