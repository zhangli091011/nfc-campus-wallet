# Android 退出登录功能

## 更新说明

为 Android 收银终端应用添加了退出登录功能。

## 更新内容

### 1. 布局文件更新

**文件**: `android/app/src/main/res/layout/activity_cashier.xml`

在头部信息卡片中添加了退出登录按钮：

```xml
<Button
    android:id="@+id/logoutButton"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:text="退出登录"
    android:textSize="12sp"
    android:backgroundTint="@color/error_red"
    android:paddingHorizontal="16dp"
    android:paddingVertical="8dp"
    style="@style/Widget.MaterialComponents.Button.TextButton" />
```

**位置**: 在收银员姓名旁边，右上角位置

### 2. Activity 代码更新

**文件**: `android/app/src/main/java/com/campus/nfcwallet/ui/CashierActivity.java`

#### 添加的变量
```java
private Button logoutButton;
```

#### 添加的初始化代码
```java
logoutButton = findViewById(R.id.logoutButton);
logoutButton.setOnClickListener(v -> performLogout());
```

#### 添加的方法
```java
/**
 * Perform logout.
 */
private void performLogout() {
    new AlertDialog.Builder(this)
        .setTitle("退出登录")
        .setMessage("确定要退出登录吗？")
        .setPositiveButton("确定", (dialog, which) -> {
            // Clear session
            sessionManager.clearSession();
            
            // Navigate to login activity
            Intent intent = new Intent(this, LoginActivity.class);
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
            startActivity(intent);
            finish();
        })
        .setNegativeButton("取消", null)
        .show();
}
```

#### 添加的 import
```java
import android.content.Intent;
```

## 功能说明

### 用户体验流程

1. **点击退出登录按钮**
   - 用户在收银终端界面右上角看到"退出登录"按钮
   - 按钮使用红色背景，表示这是一个重要操作

2. **确认对话框**
   - 点击后弹出确认对话框
   - 标题：退出登录
   - 消息：确定要退出登录吗？
   - 两个选项：
     - "确定"：执行退出登录
     - "取消"：关闭对话框，继续使用

3. **退出登录**
   - 清除本地会话数据（token 和用户信息）
   - 跳转到登录界面
   - 清除活动栈，防止用户按返回键回到收银界面

### 技术实现

#### SessionManager 清除会话
```java
sessionManager.clearSession();
```

这会清除以下数据：
- 访问令牌 (access_token)
- 用户信息 (user_info)
- 登录状态标志 (is_logged_in)

#### Activity 跳转
```java
Intent intent = new Intent(this, LoginActivity.class);
intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
startActivity(intent);
finish();
```

使用的标志：
- `FLAG_ACTIVITY_NEW_TASK`: 创建新的任务栈
- `FLAG_ACTIVITY_CLEAR_TASK`: 清除现有任务栈
- `finish()`: 关闭当前 Activity

这确保用户退出登录后无法通过返回键回到收银界面。

## 安全性

1. **确认对话框**: 防止误操作
2. **清除会话**: 完全清除本地认证信息
3. **清除活动栈**: 防止未授权访问

## 测试建议

### 功能测试
1. 登录后进入收银界面
2. 点击"退出登录"按钮
3. 验证确认对话框显示
4. 点击"取消"，验证对话框关闭，继续使用
5. 再次点击"退出登录"
6. 点击"确定"，验证跳转到登录界面
7. 尝试按返回键，验证无法返回收银界面
8. 重新登录，验证功能正常

### 边界测试
1. 在有未完成交易时退出登录
2. 在网络请求进行中时退出登录
3. 在 NFC 读卡过程中退出登录

## UI 设计

### 按钮样式
- **文字**: "退出登录"
- **字体大小**: 12sp
- **背景颜色**: error_red (红色)
- **样式**: TextButton (文本按钮)
- **内边距**: 水平 16dp，垂直 8dp

### 布局位置
- 位于头部信息卡片中
- 收银员姓名右侧
- 右对齐

### 对话框样式
- 标准 Material Design AlertDialog
- 标题：退出登录
- 消息：确定要退出登录吗？
- 按钮：确定（主要操作）、取消（次要操作）

## 相关文件

- `android/app/src/main/res/layout/activity_cashier.xml` - 布局文件
- `android/app/src/main/java/com/campus/nfcwallet/ui/CashierActivity.java` - Activity 代码
- `android/app/src/main/java/com/campus/nfcwallet/utils/SessionManager.java` - 会话管理
- `android/app/src/main/java/com/campus/nfcwallet/ui/LoginActivity.java` - 登录界面

## 后续优化建议

1. **添加退出登录动画**: 使界面过渡更流畅
2. **保存草稿**: 退出前保存未完成的购物车
3. **自动登出**: 长时间无操作自动退出登录
4. **多设备管理**: 支持在后端管理多个登录会话
5. **退出日志**: 记录退出登录操作，用于审计

## 版本信息

- **更新日期**: 2026-05-08
- **版本**: v2.1
- **更新人**: Kiro AI Assistant
