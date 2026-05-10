# 投资办理系统 - 完整方案

## 📋 概览

"官方中央银行 - 模拟投资办理终端" 是一个三端协同系统：

- **后端**：FastAPI，提供股票买入、账户互转、结算 API
- **Android**：使用 Kotlin + Jetpack Compose 构建的极简黑金风界面
- **Web 管理后台**：React + Ant Design 的投资管理与结算控制台

## 🗄️ 数据库（已完成）

运行 `python add_investment_system.py` 已创建：

| 内容 | 值 |
|------|-----|
| 活动ID | 2（2026春季校园美食节） |
| 投资摊位ID | 18（官方中央银行） |
| 投资办理员账号 | `bank_clerk` / `invest123` |
| 角色 | `super_admin`（便于调用受保护接口） |

> 该摊位仅用于"身份识别"，不作为投资目标。ViewModel 中已过滤掉它。

## 🔐 Android 端

### 架构

```
android/app/src/main/java/com/campus/nfcwallet/ui/investment/
├── InvestmentScreen.kt            Compose UI（黑金科技风）
├── InvestmentViewModel.kt         业务逻辑（NFC → 查卡 → 查余额 → 自动划转 → 买股）
└── InvestmentComposeActivity.kt   Activity 载体（NFC、退出）
```

### 登录流程

1. `bank_clerk / invest123` 登录
2. `BoothSelectionActivity` 识别用户名为 `bank_clerk` → 直接进入 `InvestmentComposeActivity`
3. 其他用户（`admin`、`booth_cashier` 等）流程不变

### 用户交互流程

1. **等待贴卡**：脉冲环动画吸引注意
2. **识别卡片**：自动查询参与者信息和余额
3. **选择投资摊位**：下拉框（已过滤"官方中央银行"）
4. **输入股数**：固定单价 ¥10.00/股，实时计算合计
5. **确认投资**：
   - 若投资币余额不足，自动从活动余额划转差额（`POST /api/stock/transfer`）
   - 调用 `POST /api/stock/buy` 完成买股
   - 成功/失败以高科技感 Snackbar 展示

### UI 风格

- **配色**：黑金（`#0A0A0F` 背景 + `#FFD700` 金）
- **元素**：金色细描边、渐变卡片、呼吸灯般的 NFC 脉冲环
- **字体**：大字距，突出科技/工业感

### 技术栈

- Kotlin 1.9.22
- Jetpack Compose BOM 2024.02.00
- Material 3
- Activity Compose / ViewModel Compose
- Kotlin Coroutines

> 原有 Java 项目已升级：`applyKotlin`, `compose true`, `minSdk 24`, `jvmTarget 17`。需要 Android Studio Hedgehog+ 或 JDK 17。

## 🖥️ Web 管理后台

### 新增页面

- **路径**：`/investment`
- **菜单位置**：主菜单 → 投资管理
- **文件**：
  - `web-admin/src/pages/Investment/index.tsx`
  - `web-admin/src/services/investment.ts`

### 功能

1. **股市概览**：
   - 总投资额、全局奖金池、投资人数、摊位数
   - 订单数、手续费、结算状态
2. **期末一键结算**：
   - 可调整手续费率（默认 5%）
   - 结算完成后弹框展示各摊位分数与最终股价
3. **结算逻辑说明**：卡片内内置公式提示

## 🔌 后端接口（已存在，复用）

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/stock/transfer` | POST | 活动余额 ↔ 投资币互转 |
| `/api/stock/buy` | POST | 购买股票（悲观锁防超卖） |
| `/api/stock/stats/{event_id}` | GET | 股市统计 |
| `/api/stock/settle` | POST | 期末结算（管理员） |
| `/api/stock/orders/{participant_id}` | GET | 查询订单 |

签名验证中间件已对 `/api/stock/*` 前缀全部放行（JWT 路径）。

## ✅ 测试方式

### 1. 后端已重启（本轮自动完成）

验证：`curl http://localhost:8000/health`

### 2. Android

1. 用 Android Studio 打开 `android` 目录，等待 Gradle sync 自动下载 Kotlin + Compose 依赖
2. 首次同步完成后，构建安装到设备
3. `bank_clerk / invest123` 登录 → 自动进入投资终端
4. 贴学生卡 → 选择摊位 → 输入股数 → 确认投资

### 3. Web

1. `cd web-admin && npm run dev`
2. 登录 admin → 左侧菜单「投资管理」
3. 选择活动查看股市概览 / 执行期末结算

## ⚠️ 注意

- **签名 Secret Key**：`SignatureGenerator.java` 中的 `secretKey` 仍是 hardcoded `"your_secret_key_here"`。目前后端中间件已对 `/api/stock/*` 放行，所以该 key 的值并不影响此功能。如果后续启用严格签名校验，需要将 Android 端的 key 与后端 `.env` 的 `SECRET_KEY` 保持一致。
- **Android 首次构建较慢**：需要下载 Compose BOM 与 Kotlin stdlib。
- **最低 SDK 由 21 升到 24**：Compose 要求 API 24+。若要支持更老设备，需单独处理。

## 📁 改动清单

### 新增
- `add_investment_system.py`
- `android/app/src/main/java/com/campus/nfcwallet/ui/investment/InvestmentScreen.kt`
- `android/app/src/main/java/com/campus/nfcwallet/ui/investment/InvestmentViewModel.kt`
- `android/app/src/main/java/com/campus/nfcwallet/ui/investment/InvestmentComposeActivity.kt`
- `web-admin/src/pages/Investment/index.tsx`
- `web-admin/src/services/investment.ts`
- `INVESTMENT_SYSTEM_GUIDE.md`（本文档）

### 修改
- `android/build.gradle`（添加 Kotlin 插件）
- `android/app/build.gradle`（添加 Kotlin + Compose）
- `android/app/src/main/AndroidManifest.xml`（注册 InvestmentComposeActivity）
- `android/app/src/main/res/values/themes.xml`（新增 Investment 主题）
- `android/app/src/main/java/com/campus/nfcwallet/ui/BoothSelectionActivity.java`（bank_clerk 分支）
- `web-admin/src/routes/index.tsx`（新增 /investment 路由）
- `web-admin/src/components/Layout/index.tsx`（新增菜单项）
