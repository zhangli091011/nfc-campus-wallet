# 服务器快速设置指南

## 1. 创建管理员账户

### 方法1: 使用SQL脚本（推荐）

在服务器上执行：

```bash
# 进入项目目录
cd ~/nfc-campus-wallet

# 执行SQL脚本创建管理员
mysql -u your_db_user -p nfc_wallet < create_admin.sql
```

**默认管理员账户：**
- 用户名: `admin`
- 密码: `admin123`

### 方法2: 直接使用MySQL命令

```bash
mysql -u your_db_user -p nfc_wallet
```

然后执行：

```sql
INSERT INTO users (username, hashed_password, role, is_active, created_at)
VALUES (
    'admin',
    '$2b$12$1k1YoueJ786gm.O139qqmuhSI.QsMPl.evIZycDYJYnV2afo7MGvK',
    'super_admin',
    1,
    NOW()
);
```

### 方法3: 生成自定义密码

如果你想使用不同的密码：

```bash
# 在本地或服务器上运行
python generate_password_hash.py

# 输入你想要的密码，脚本会生成SQL语句
# 然后在服务器上执行生成的SQL
```

## 2. 验证管理员账户

### 测试登录API

```bash
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

成功响应示例：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "super_admin"
  }
}
```

### 测试获取用户信息

```bash
# 使用上面获取的token
TOKEN="your_access_token_here"

curl -X GET "http://localhost:8001/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

## 3. 常见问题

### Q: 忘记管理员密码怎么办？

A: 重新运行SQL脚本或使用`generate_password_hash.py`生成新密码哈希，然后更新数据库：

```sql
INSERT INTO users (username, password_hash, role, status, created_at, updated_at)
VALUES (
    'admin',
    '$2b$12$新的密码哈希',
    'super_admin',
    'active',
    NOW(),
    NOW()
);
```

### Q: 如何创建其他管理员？

A: 使用API创建（需要super_admin权限）：

```bash
curl -X POST "http://localhost:8001/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin2",
    "password": "password123",
    "role": "event_admin"
  }'
```

### Q: API返回404错误

A: 检查：
1. API服务是否正在运行：`ps aux | grep uvicorn`
2. 端口是否正确：默认是8001
3. 路由是否正确：使用`/auth/login`而不是`/auth/register`

## 4. 安全建议

⚠️ **重要：生产环境安全措施**

1. **立即修改默认密码**
   ```bash
   # 登录后通过API修改密码
   curl -X PUT "http://localhost:8001/users/1/password" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "old_password": "admin123",
       "new_password": "your_strong_password_here"
     }'
   ```

2. **修改JWT密钥**
   - 编辑`.env`文件
   - 设置强随机的`JWT_SECRET_KEY`（至少32字符）

3. **限制数据库访问**
   - 只允许应用服务器IP访问数据库
   - 使用强密码

4. **启用HTTPS**
   - 使用Nginx反向代理
   - 配置SSL证书

5. **定期备份数据库**
   ```bash
   mysqldump -u user -p nfc_wallet > backup_$(date +%Y%m%d).sql
   ```

## 5. 下一步

创建管理员后，你可以：

1. 创建活动（Event）
2. 创建摊位（Booth）
3. 创建商品（Product）
4. 导入参与者（Participant）
5. 配置Android收银终端

详见 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
