# 创建参与者对话框调试指南

## 问题描述

刷新卡后，当卡片未绑定时，应该弹出"创建新参与者"对话框，但对话框没有显示。

## 预期行为

1. 用户刷卡（例如：`79E733B6`）
2. Android 应用调用 `GET /participants/by-card/79E733B6`
3. 后端返回 400 Bad Request（卡片未绑定）
4. Android 应用弹出对话框，提示创建新参与者
5. 用户输入姓名、班级、学号
6. 点击"创建"按钮，调用 API 创建参与者

## 代码流程

### 1. 刷卡触发

```java
private void handleCardDetected(String uid) {
    Log.d(TAG, "Card detected: " + uid);
    
    currentCardUid = uid;
    cardUidText.setText(uid);
    cardInfoSection.setVisibility(View.VISIBLE);
    cardLoadingProgress.setVisibility(View.VISIBLE);
    
    // Clear previous data
    participantNameText.setText("查询中...");
    balanceText.setText("--");
    
    // Query participant info
    queryParticipant(uid);  // ← 调用查询方法
}
```

### 2. 查询参与者

```java
private void queryParticipant(String cardUid) {
    Log.d(TAG, "Querying participant for card: " + cardUid);
    
    Call<ParticipantInfo> call = apiService.getParticipantByCard(cardUid);
    call.enqueue(new Callback<ParticipantInfo>() {
        @Override
        public void onResponse(Call<ParticipantInfo> call, Response<ParticipantInfo> response) {
            Log.d(TAG, "Participant query response code: " + response.code());
            
            if (response.isSuccessful() && response.body() != null) {
                // 参与者存在
                currentParticipant = response.body();
                participantNameText.setText(currentParticipant.getName());
                queryBalance();
            } else {
                cardLoadingProgress.setVisibility(View.GONE);
                
                // 检查是否是 400 或 404
                if (response.code() == 400 || response.code() == 404) {
                    participantNameText.setText("未绑定");
                    
                    Log.i(TAG, "Showing create participant dialog for card: " + cardUid);
                    showCreateParticipantDialog(cardUid);  // ← 应该调用这里
                } else {
                    // 其他错误
                    String error = ErrorHandler.getErrorMessage(response);
                    participantNameText.setText("查询失败");
                    showError(error);
                }
            }
        }
        
        @Override
        public void onFailure(Call<ParticipantInfo> call, Throwable t) {
            // 网络错误
            cardLoadingProgress.setVisibility(View.GONE);
            Log.e(TAG, "Failed to query participant", t);
            participantNameText.setText("查询失败");
            showError("网络错误");
        }
    });
}
```

### 3. 显示对话框

```java
private void showCreateParticipantDialog(String cardUid) {
    Log.d(TAG, "Creating participant dialog for card: " + cardUid);
    
    AlertDialog.Builder builder = new AlertDialog.Builder(this);
    builder.setTitle("新卡片");
    builder.setMessage("卡片 " + cardUid + " 未绑定，是否创建新参与者？");
    
    // ... 创建输入框 ...
    
    AlertDialog dialog = builder.create();
    dialog.show();  // ← 显示对话框
    
    Log.i(TAG, "Create participant dialog shown");
}
```

## 调试步骤

### 步骤 1: 查看 Logcat 日志

在 Android Studio 中打开 Logcat，过滤 `CashierActivity`：

```
adb logcat | grep CashierActivity
```

或在 Android Studio 的 Logcat 窗口中输入过滤器：
```
tag:CashierActivity
```

### 步骤 2: 刷卡并观察日志

刷一张未绑定的卡片，应该看到以下日志：

```
D/CashierActivity: Card detected: 79E733B6
D/CashierActivity: Querying participant for card: 79E733B6
D/CashierActivity: Participant query response code: 400
W/CashierActivity: Participant not found, response code: 400
I/CashierActivity: Showing create participant dialog for card: 79E733B6
D/CashierActivity: Creating participant dialog for card: 79E733B6
I/CashierActivity: Create participant dialog shown
```

### 步骤 3: 检查可能的问题

#### 问题 1: 响应码不是 400

**症状**: 日志显示响应码不是 400 或 404

**解决方案**: 检查后端返回的状态码

```bash
# 使用 curl 测试
curl -X GET "http://your-server/participants/by-card/79E733B6" -v
```

#### 问题 2: 对话框被创建但没有显示

**症状**: 看到 "Creating participant dialog" 但没有看到 "Create participant dialog shown"

**可能原因**:
- Activity 已经被销毁
- 在后台线程中调用（但我们使用了 Retrofit 的回调，应该在主线程）

**解决方案**: 确保在主线程中显示对话框

```java
runOnUiThread(() -> showCreateParticipantDialog(cardUid));
```

#### 问题 3: 网络请求失败

**症状**: 看到 "Failed to query participant" 错误

**可能原因**:
- 网络连接问题
- API 地址配置错误
- 服务器未运行

**解决方案**: 检查网络连接和 API 配置

```java
// 在 APIClient.java 中检查 BASE_URL
private static final String BASE_URL = "http://your-server:8000/";
```

#### 问题 4: JSON 解析错误

**症状**: 看到 JSON 解析相关的错误

**可能原因**: 后端返回的错误响应格式不符合预期

**解决方案**: 检查后端错误响应格式

```python
# 后端应该返回
return JSONResponse(
    status_code=400,
    content={
        "error_code": "VALIDATION_ERROR",
        "message": "Participant not found"
    }
)
```

## 临时解决方案

如果对话框仍然不显示，可以尝试以下临时解决方案：

### 方案 1: 强制在主线程显示

```java
private void queryParticipant(String cardUid) {
    // ...
    call.enqueue(new Callback<ParticipantInfo>() {
        @Override
        public void onResponse(Call<ParticipantInfo> call, Response<ParticipantInfo> response) {
            if (response.code() == 400 || response.code() == 404) {
                // 强制在主线程显示
                runOnUiThread(() -> {
                    participantNameText.setText("未绑定");
                    showCreateParticipantDialog(cardUid);
                });
            }
        }
    });
}
```

### 方案 2: 使用 Toast 测试

临时添加 Toast 来确认代码执行到这里：

```java
if (response.code() == 400 || response.code() == 404) {
    Toast.makeText(CashierActivity.this, 
        "卡片未绑定: " + cardUid, 
        Toast.LENGTH_LONG).show();
    
    participantNameText.setText("未绑定");
    showCreateParticipantDialog(cardUid);
}
```

### 方案 3: 简化对话框

创建一个最简单的对话框测试：

```java
private void showCreateParticipantDialog(String cardUid) {
    new AlertDialog.Builder(this)
        .setTitle("测试")
        .setMessage("卡片: " + cardUid)
        .setPositiveButton("确定", null)
        .show();
}
```

## 完整的调试日志示例

### 成功的日志

```
D/CashierActivity: Card detected: 79E733B6
D/CashierActivity: Querying participant for card: 79E733B6
D/CashierActivity: Participant query response code: 400
W/CashierActivity: Participant not found, response code: 400
I/CashierActivity: Showing create participant dialog for card: 79E733B6
D/CashierActivity: Creating participant dialog for card: 79E733B6
I/CashierActivity: Create participant dialog shown
```

### 失败的日志（网络错误）

```
D/CashierActivity: Card detected: 79E733B6
D/CashierActivity: Querying participant for card: 79E733B6
E/CashierActivity: Failed to query participant
    java.net.ConnectException: Failed to connect to /192.168.1.100:8000
```

### 失败的日志（JSON 解析错误）

```
D/CashierActivity: Card detected: 79E733B6
D/CashierActivity: Querying participant for card: 79E733B6
E/CashierActivity: Failed to query participant
    com.google.gson.JsonSyntaxException: Expected BEGIN_OBJECT but was STRING
```

## 后端验证

### 测试后端 API

```bash
# 测试未绑定的卡片
curl -X GET "http://your-server:8000/participants/by-card/79E733B6" -v

# 应该返回
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error_code": "VALIDATION_ERROR",
  "message": "Participant not found by card_uid: 79E733B6"
}
```

### 测试已绑定的卡片

```bash
# 测试已绑定的卡片
curl -X GET "http://your-server:8000/participants/by-card/A1B2C3D4" -v

# 应该返回
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": 1,
  "name": "张三",
  "card_uid": "A1B2C3D4",
  "class_name": "高一(1)班",
  "student_no": "2024001",
  "participant_type": "person",
  "status": "active"
}
```

## 相关文件

- `android/app/src/main/java/com/campus/nfcwallet/ui/CashierActivity.java` - 主要逻辑
- `android/app/src/main/java/com/campus/nfcwallet/api/WalletAPIService.java` - API 接口定义
- `android/app/src/main/java/com/campus/nfcwallet/models/ParticipantInfo.java` - 参与者模型
- `routes/participants.py` - 后端参与者路由

## 下一步

1. 重新编译并运行 Android 应用
2. 刷一张未绑定的卡片
3. 查看 Logcat 日志
4. 根据日志信息定位问题
5. 如果对话框仍然不显示，尝试临时解决方案

## 更新日志

- **2026-05-08**: 添加详细的调试日志
- **2026-05-08**: 添加调试指南文档
