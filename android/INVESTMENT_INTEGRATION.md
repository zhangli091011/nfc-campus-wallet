# 投资办理终端集成指南

## 📱 功能概述

**官方中央银行 - 模拟投资办理终端** 是一个高科技感的Android界面，用于现场工作人员为学生办理模拟股票投资业务。

### 核心特性
- ✨ 黑金配色，未来科技感UI设计
- 🎴 NFC卡片识别，自动读取参与者信息
- 💰 双账户体系展示（活动账户 + 投资币账户）
- 📊 实时计算投资金额
- 🔒 悲观锁机制，防止并发超卖
- ⚡ 流畅的动画效果

---

## 🚀 快速集成

### 1. 在主界面添加入口按钮

在 `MainActivity.java` 或其他主界面中添加一个按钮：

```java
// MainActivity.java

import android.content.Intent;
import android.widget.Button;
import com.campus.nfcwallet.ui.InvestmentActivity;

public class MainActivity extends AppCompatActivity {
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        // 添加投资办理入口
        Button btnInvestment = findViewById(R.id.btn_investment);
        btnInvestment.setOnClickListener(v -> {
            Intent intent = new Intent(MainActivity.this, InvestmentActivity.class);
            intent.putExtra("event_id", getCurrentEventId());  // 传递活动ID
            startActivity(intent);
        });
    }
    
    private int getCurrentEventId() {
        // 从SessionManager或其他地方获取当前活动ID
        SessionManager sessionManager = new SessionManager(this);
        return sessionManager.getEventId();
    }
}
```

### 2. 在主界面布局中添加按钮

在 `activity_main.xml` 中添加：

```xml
<Button
    android:id="@+id/btn_investment"
    android:layout_width="match_parent"
    android:layout_height="64dp"
    android:text="📈 模拟投资办理"
    android:textSize="18sp"
    android:textStyle="bold"
    android:background="@drawable/bg_button_primary"
    android:layout_margin="16dp" />
```

### 3. 在 AndroidManifest.xml 中注册 Activity

```xml
<activity
    android:name=".ui.InvestmentActivity"
    android:label="投资办理终端"
    android:theme="@style/Theme.NFCWallet"
    android:screenOrientation="portrait" />
```

---

## 🎨 UI/UX 设计说明

### 配色方案
- **背景色**: `#0A0E27` (深蓝黑)
- **卡片背景**: `#1A1F3A` (深蓝灰)
- **主色调**: `#FFD700` (金色)
- **文字色**: `#FFFFFF` (白色)
- **次要文字**: `#B0B0B0` (灰色)

### 界面结构
1. **顶部标题**: "官方中央银行 - 模拟投资办理终端"
2. **NFC感应区**: 带脉冲动画的NFC图标
3. **账户信息卡**: 显示活动账户和投资币余额
4. **投资表单卡**: 摊位选择 + 股数输入
5. **确认按钮**: 大型金色按钮

### 动画效果
- NFC图标脉冲动画（等待读卡时）
- 卡片淡入动画（读卡成功后）
- 按钮点击反馈

---

## 🔧 API 接口说明

### 1. 购买股票
```
POST /api/stock/buy
```

**请求参数**:
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

**响应**:
```json
{
  "success": true,
  "order_id": 123,
  "booth_name": "美食摊",
  "shares": 10,
  "buy_price_yuan": 10.0,
  "total_amount_yuan": 100.0,
  "new_stock_balance_yuan": 400.0,
  "message": "成功购买 美食摊 10股"
}
```

### 2. 账户互转
```
POST /api/stock/transfer
```

**请求参数**:
```json
{
  "card_uid": "A1B2C3D4",
  "event_id": 1,
  "transfer_type": "to_stock",  // "to_stock" 或 "from_stock"
  "amount": 10000,  // 单位：分
  "timestamp": 1234567890,
  "signature": "abc123..."
}
```

---

## 📋 使用流程

### 工作人员操作流程

1. **打开投资办理终端**
   - 从主界面点击"模拟投资办理"按钮

2. **等待学生刷卡**
   - 界面显示NFC感应动画
   - 学生将NFC卡贴近设备

3. **查看账户信息**
   - 自动识别参与者信息
   - 显示活动账户和投资币余额

4. **填写投资信息**
   - 选择要投资的摊位
   - 输入购买股数
   - 系统自动计算总金额

5. **确认投资**
   - 点击"确认投资"按钮
   - 弹出确认对话框
   - 确认后发起购买请求

6. **查看结果**
   - 显示投资成功信息
   - 更新投资币余额
   - 可继续办理下一笔业务

---

## 🔐 安全机制

### 1. 悲观锁防止并发
- 使用 `SELECT ... FOR UPDATE` 锁定投资币账户
- 防止并发购买导致余额扣成负数

### 2. 签名验证
- 所有请求都需要签名验证
- 签名算法: `SHA256(card_uid + amount + timestamp + secret_key)`

### 3. 余额检查
- 购买前检查投资币余额是否充足
- 不足时拒绝交易

---

## 🎯 扩展功能

### 可选功能（未实现）

1. **账户互转功能**
   - 添加"账户互转"按钮
   - 支持活动账户 ↔ 投资币账户互转

2. **持仓查询**
   - 显示参与者的股票持仓
   - 查看历史投资记录

3. **实时统计**
   - 显示当前活动的投资统计
   - 各摊位的投资热度排行

4. **离线模式**
   - 支持离线记录交易
   - 网络恢复后自动同步

---

## 🐛 故障排查

### 常见问题

**1. NFC无法读卡**
- 检查设备是否支持NFC
- 确认NFC已在系统设置中启用
- 检查卡片是否为ISO 14443A标准

**2. 网络请求失败**
- 检查后端服务是否运行
- 确认API地址配置正确
- 查看网络连接状态

**3. 余额不足**
- 确认投资币账户有足够余额
- 可使用账户互转功能充值

**4. 摊位列表为空**
- 确认活动中有激活的摊位
- 检查API权限配置

---

## 📞 技术支持

如有问题，请联系开发团队或查看以下文档：
- [API文档](../docs/API_DOCUMENTATION.md)
- [Android README](./README.md)
- [后端README](../README.md)

---

**Made with ❤️ for campus financial education**
