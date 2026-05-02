# 部署说明

## 最新更改

### 修复内容
1. 修复参与者管理页面不显示问题
2. 修复安卓端活动信息加载失败问题
3. 修复事件模式余额查询 API 认证问题
4. 修复充值 API 事件模式支持
5. 修复充值按钮显示问题

### 需要部署的文件

#### 后端文件
```bash
# 核心文件
middleware/signature_verification.py
routes/balance.py
routes/recharge.py
routes/booths.py
schemas/transaction.py
app/main.py

# 工具脚本
setup_test_data.py
restart_server.sh
```

#### 前端文件
```bash
# Web Admin
web-admin/dist/  # 需要重新构建
web-admin/src/pages/ParticipantManagement/index.tsx
web-admin/src/services/participant.ts
```

#### 安卓端文件
```bash
android/app/src/main/java/com/campus/nfcwallet/ui/LoginActivity.java
android/app/src/main/java/com/campus/nfcwallet/ui/BoothSelectionActivity.java
android/app/src/main/java/com/campus/nfcwallet/ui/CashierActivity.java
android/app/src/main/java/com/campus/nfcwallet/api/WalletAPIService.java
android/app/src/main/java/com/campus/nfcwallet/models/RechargeRequest.java
```

## 部署步骤

### 1. 备份当前代码
```bash
cd /home/ubuntu/nfc-campus-wallet
cp -r . ../nfc-campus-wallet-backup-$(date +%Y%m%d-%H%M%S)
```

### 2. 拉取最新代码
```bash
git pull origin main
```

### 3. 重启后端服务
```bash
sudo systemctl restart nfc-wallet
# 或使用脚本
bash restart_server.sh
```

### 4. 检查服务状态
```bash
sudo systemctl status nfc-wallet
# 查看日志
sudo journalctl -u nfc-wallet -f
```

### 5. 设置测试数据（如果需要）
```bash
source .venv/bin/activate
python setup_test_data.py
```

### 6. 构建 Web Admin（如果需要）
```bash
cd web-admin
npm run build
# 部署 dist 目录到 Web 服务器
```

### 7. 构建安卓 APK（如果需要）
```bash
cd android
./gradlew assembleRelease
# APK 位于: app/build/outputs/apk/release/
```

## 验证

### 1. 测试余额查询
```bash
curl "http://localhost:8000/balance?event_id=2&card_uid=2BC8694C"
```

### 2. 测试充值
```bash
curl -X POST http://localhost:8000/recharge \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 2,
    "card_uid": "2BC8694C",
    "amount": 50.0,
    "remark": "测试充值"
  }'
```

### 3. 检查日志
```bash
# 查看最近的日志
sudo journalctl -u nfc-wallet -n 100

# 实时查看日志
sudo journalctl -u nfc-wallet -f
```

## 故障排查

### 问题：401 Unauthorized
- 检查中间件代码是否正确部署
- 检查服务器是否重启
- 查看日志中的调试信息

### 问题：活动信息加载失败
- 运行 `python setup_test_data.py` 创建测试数据
- 检查数据库中是否有活动和摊位记录

### 问题：参与者不显示
- 检查 Web Admin 是否重新构建
- 清除浏览器缓存
- 检查后端 API 是否正常

## 回滚

如果出现问题，可以回滚到备份：
```bash
cd /home/ubuntu
sudo systemctl stop nfc-wallet
rm -rf nfc-campus-wallet
mv nfc-campus-wallet-backup-YYYYMMDD-HHMMSS nfc-campus-wallet
cd nfc-campus-wallet
sudo systemctl start nfc-wallet
```
