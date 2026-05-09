# 摊位选择权限问题修复

## 问题描述

### 错误日志
```
2026-05-08 18:45:42 - GET /booths?status=active HTTP/1.0" 403 Forbidden
服务器返回了错误的数据格式可能是服务器内部错误请联系管理员检查服务器日志
```

### 问题原因

1. **权限不匹配**: `booth_cashier` 用户登录后，Android 应用尝试调用 `/booths?status=active` 接口获取摊位列表
2. **后端限制**: `/booths` 接口只允许 `super_admin` 和 `event_admin` 角色访问
3. **返回 403**: `booth_cashier` 用户没有权限，后端返回 403 Forbidden
4. **解析错误**: Android 应用期望返回 JSON 数组，但收到错误响应，导致解析失败

### 根本原因

`booth_cashier` 用户在数据库中已经有 `booth_id` 字段，表示他们被分配到特定的摊位。他们不需要选择摊位，应该直接进入自己的摊位。

## 解决方案

### 修改 Android 端逻辑

**文件**: `android/app/src/main/java/com/campus/nfcwallet/ui/BoothSelectionActivity.java`

#### 修改内容

在 `loadBooths()` 方法开始处添加角色检查：

```java
private void loadBooths() {
    String authHeader = sessionManager.getAuthHeader();
    if (authHeader == null) {
        navigateToLogin();
        return;
    }
    
    // Check user role and booth assignment
    if (sessionManager.getUserInfo() != null) {
        String role = sessionManager.getUserInfo().getRole();
        Integer boothId = sessionManager.getUserInfo().getBoothId();
        
        // If user is booth_cashier and has assigned booth, go directly to it
        if ("booth_cashier".equals(role) && boothId != null && boothId > 0) {
            Log.i(TAG, "Booth cashier with assigned booth, navigating directly to booth " + boothId);
            navigateToCashier(boothId);
            return;
        }
    }
    
    // ... 继续原有的加载摊位列表逻辑（仅用于管理员）
}
```

#### 逻辑说明

1. **检查用户信息**: 从 SessionManager 获取当前用户信息
2. **检查角色**: 如果用户角色是 `booth_cashier`
3. **检查摊位分配**: 如果用户有分配的 `booth_id`（不为 null 且大于 0）
4. **直接跳转**: 跳过摊位列表加载，直接进入收银界面
5. **管理员流程**: 其他角色（admin）继续原有的摊位选择流程

## 用户体验改进

### 收银员登录流程

**修复前**:
```
登录 → 尝试加载摊位列表 → 403 错误 → 显示错误信息
```

**修复后**:
```
登录 → 检测到 booth_cashier 角色 → 直接进入分配的摊位
```

### 管理员登录流程

**保持不变**:
```
登录 → 加载摊位列表 → 选择摊位 → 进入收银界面
```

## 技术细节

### UserInfo 模型

确保 `UserInfo` 模型包含以下字段：

```java
public class UserInfo {
    private int id;
    private String username;
    private String role;
    private Integer boothId;  // 可能为 null
    private String status;
    
    // Getters
    public String getRole() { return role; }
    public Integer getBoothId() { return boothId; }
}
```

### 角色类型

系统支持的角色：
- `super_admin`: 超级管理员，可以选择任意摊位
- `event_admin`: 活动管理员，可以选择任意摊位
- `booth_cashier`: 摊位收银员，只能访问分配的摊位
- `issuer`: 充值员
- `reviewer`: 审核员

### 数据库结构

`users` 表结构：
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('super_admin', 'event_admin', 'booth_cashier', 'issuer', 'reviewer') NOT NULL,
    booth_id INT NULL,  -- 仅 booth_cashier 角色使用
    status ENUM('active', 'inactive', 'blocked') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (booth_id) REFERENCES booths(id)
);
```

## 测试建议

### 测试用例 1: 收银员登录
1. 使用 `booth1_cashier` / `cashier123` 登录
2. 验证直接进入摊位 1 的收银界面
3. 验证不会显示摊位选择界面
4. 验证不会出现 403 错误

### 测试用例 2: 管理员登录
1. 使用 `admin` / `admin123` 登录
2. 验证显示摊位选择界面
3. 验证可以看到所有活动摊位
4. 验证可以选择任意摊位

### 测试用例 3: 未分配摊位的收银员
1. 创建一个 `booth_cashier` 用户但不分配 `booth_id`
2. 登录后验证显示摊位选择界面（或错误提示）
3. 建议：在后端创建用户时强制要求收银员必须分配摊位

## 后端 API 权限说明

### `/booths` 接口权限

**当前权限**: `super_admin`, `event_admin`

**原因**: 
- 摊位列表包含所有摊位的敏感信息
- 收银员不需要看到其他摊位的信息
- 收银员通过 `booth_id` 直接访问自己的摊位

### `/booths/{booth_id}` 接口权限

**当前权限**: `super_admin`, `event_admin`, `booth_cashier`（仅自己的摊位）

**验证逻辑**:
```python
@router.get("/booths/{booth_id}")
async def get_booth(
    booth_id: int,
    current_user: User = Depends(get_current_user),
    _: None = Depends(validate_booth_ownership),  # 验证摊位所有权
    db: Session = Depends(get_db)
):
    # ...
```

## 安全性考虑

1. **权限隔离**: 收银员只能访问自己的摊位，无法看到其他摊位信息
2. **后端验证**: 所有摊位相关操作都在后端验证权限
3. **前端优化**: 前端根据角色优化用户体验，减少不必要的 API 调用

## 相关文件

- ✅ `android/app/src/main/java/com/campus/nfcwallet/ui/BoothSelectionActivity.java` - 已修复
- `android/app/src/main/java/com/campus/nfcwallet/models/UserInfo.java` - 用户信息模型
- `android/app/src/main/java/com/campus/nfcwallet/utils/SessionManager.java` - 会话管理
- `routes/booths.py` - 后端摊位路由
- `core/security.py` - 后端权限验证

## 版本信息

- **修复日期**: 2026-05-08
- **版本**: v2.1.1
- **问题**: 收银员登录后 403 错误
- **解决**: 收银员直接进入分配的摊位，跳过摊位选择
