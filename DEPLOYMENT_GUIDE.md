# NFC Campus Event System - 部署指南

## 目录
1. [系统要求](#系统要求)
2. [后端部署](#后端部署)
3. [数据库初始化](#数据库初始化)
4. [Android 应用部署](#android-应用部署)
5. [环境配置](#环境配置)
6. [验证部署](#验证部署)

---

## 系统要求

### 后端服务器
- **操作系统**: Linux (Ubuntu 20.04+) / Windows 10+ / macOS 10.15+
- **Python**: 3.9 或更高版本
- **数据库**: MySQL 8.0 或更高版本
- **内存**: 最低 2GB RAM
- **磁盘**: 最低 10GB 可用空间

### Android 设备
- **Android 版本**: 8.0 (API 26) 或更高
- **NFC 支持**: 必须支持 NFC 功能
- **网络**: 需要连接到后端服务器的网络

---

## 后端部署

### 1. 克隆代码仓库

```bash
git clone <repository-url>
cd nfc-campus-event-system
```

### 2. 创建 Python 虚拟环境

```bash
# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制 `.env.example` 到 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=nfc_campus_wallet

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# JWT 配置
JWT_SECRET_KEY=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 签名验证（可选）
SIGNATURE_VERIFICATION_ENABLED=false
SIGNATURE_SECRET_KEY=your-signature-secret-key
```

### 5. 启动后端服务

```bash
# 开发模式（自动重载）
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 6. 验证后端服务

访问 http://localhost:8000/health 应该返回：

```json
{
  "status": "healthy",
  "service": "nfc-campus-wallet"
}
```

访问 http://localhost:8000/docs 查看 API 文档。

---

## 数据库初始化

### 1. 创建数据库

```sql
CREATE DATABASE nfc_campus_wallet CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 创建数据库用户（可选）

```sql
CREATE USER 'nfc_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON nfc_campus_wallet.* TO 'nfc_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 初始化数据库表

后端服务启动时会自动创建所有表。如果需要手动初始化：

```python
# 运行 Python 脚本
python -c "from core.database import init_database; init_database()"
```

### 4. 创建初始管理员账户

```bash
# 使用提供的脚本创建管理员
python scripts/create_admin.py
```

或通过 API 创建：

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123",
    "role": "super_admin"
  }'
```

---

## Android 应用部署

### 1. 配置后端地址

编辑 `android/local.properties`：

```properties
sdk.dir=/path/to/Android/Sdk
backend.url=http://your-server-ip:8000
```

或复制示例文件：

```bash
cd android
cp local.properties.example local.properties
```

### 2. 构建 APK

```bash
cd android
./gradlew assembleDebug
```

生成的 APK 位于：`android/app/build/outputs/apk/debug/app-debug.apk`

### 3. 安装到设备

```bash
# 通过 ADB 安装
adb install app/build/outputs/apk/debug/app-debug.apk

# 或直接传输 APK 到设备安装
```

### 4. 配置应用

首次启动应用后：
1. 在登录界面点击"设置"
2. 输入后端服务器地址：`http://your-server-ip:8000`
3. 保存配置

---

## 环境配置

### .env 文件完整示例

```env
# ===========================================
# NFC Campus Event System - Environment Configuration
# ===========================================

# -----------------
# 数据库配置
# -----------------
DB_HOST=localhost
DB_PORT=3306
DB_USER=nfc_user
DB_PASSWORD=secure_password_here
DB_NAME=nfc_campus_wallet

# -----------------
# 服务器配置
# -----------------
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# -----------------
# JWT 认证配置
# -----------------
# 密钥（生产环境必须修改）
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production

# 算法
JWT_ALGORITHM=HS256

# Token 过期时间（分钟）
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# -----------------
# 签名验证配置（可选）
# -----------------
# 是否启用签名验证
SIGNATURE_VERIFICATION_ENABLED=false

# 签名密钥
SIGNATURE_SECRET_KEY=your-signature-secret-key

# -----------------
# 日志配置
# -----------------
LOG_LEVEL=INFO

# -----------------
# CORS 配置
# -----------------
CORS_ORIGINS=*
```

### 生产环境安全建议

1. **修改所有默认密钥**
   ```bash
   # 生成随机密钥
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **启用 HTTPS**
   - 使用 Nginx 或 Apache 作为反向代理
   - 配置 SSL 证书（Let's Encrypt）

3. **限制 CORS**
   ```env
   CORS_ORIGINS=https://your-frontend-domain.com
   ```

4. **启用签名验证**
   ```env
   SIGNATURE_VERIFICATION_ENABLED=true
   SIGNATURE_SECRET_KEY=your-production-signature-key
   ```

5. **数据库安全**
   - 使用强密码
   - 限制数据库访问 IP
   - 定期备份数据

---

## 验证部署

### 1. 健康检查

```bash
curl http://localhost:8000/health
```

预期响应：
```json
{
  "status": "healthy",
  "service": "nfc-campus-wallet"
}
```

### 2. 登录测试

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

预期响应：
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "super_admin"
  }
}
```

### 3. 创建测试活动

```bash
TOKEN="your-access-token"

curl -X POST "http://localhost:8000/events" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试活动",
    "start_time": "2024-03-01T08:00:00Z",
    "end_time": "2024-03-03T20:00:00Z",
    "status": "active"
  }'
```

### 4. Android 应用测试

1. 启动应用
2. 使用管理员账户登录
3. 选择活动
4. 测试 NFC 读卡功能

---

## 故障排查

### 后端无法启动

1. **检查 Python 版本**
   ```bash
   python --version  # 应该是 3.9+
   ```

2. **检查依赖安装**
   ```bash
   pip list | grep fastapi
   ```

3. **检查数据库连接**
   ```bash
   mysql -h localhost -u nfc_user -p nfc_campus_wallet
   ```

### Android 应用无法连接

1. **检查网络连接**
   - 确保设备和服务器在同一网络
   - 检查防火墙设置

2. **检查后端地址**
   - 使用 IP 地址而非 localhost
   - 确保端口正确（默认 8000）

3. **查看应用日志**
   ```bash
   adb logcat | grep NFC
   ```

### 数据库错误

1. **检查数据库服务**
   ```bash
   systemctl status mysql  # Linux
   ```

2. **检查数据库权限**
   ```sql
   SHOW GRANTS FOR 'nfc_user'@'localhost';
   ```

3. **查看错误日志**
   ```bash
   tail -f /var/log/mysql/error.log
   ```

---

## 维护和监控

### 日志管理

后端日志位置：
- 标准输出（控制台）
- 可配置到文件：修改 `app/main.py` 中的 logging 配置

### 数据库备份

```bash
# 备份数据库
mysqldump -u nfc_user -p nfc_campus_wallet > backup_$(date +%Y%m%d).sql

# 恢复数据库
mysql -u nfc_user -p nfc_campus_wallet < backup_20240301.sql
```

### 性能监控

推荐工具：
- **Prometheus + Grafana**: 监控系统指标
- **ELK Stack**: 日志分析
- **New Relic / DataDog**: APM 监控

---

## 联系支持

如有问题，请联系：
- 技术支持邮箱: support@example.com
- 项目文档: https://docs.example.com
- GitHub Issues: https://github.com/your-repo/issues
