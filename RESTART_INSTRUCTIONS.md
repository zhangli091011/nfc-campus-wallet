# 🔄 后端服务器重启说明

## 为什么需要重启？

修改了 `middleware/signature_verification.py` 文件，需要重启后端服务器才能生效。

---

## 方法1: 手动重启（推荐）

### 步骤：

1. **找到运行后端的终端窗口**
   - 查找显示 "NFC Campus Wallet - Server Startup" 的窗口
   - 或者显示 "Uvicorn running on http://0.0.0.0:8000" 的窗口

2. **停止服务器**
   - 在该终端窗口按 `Ctrl + C`
   - 等待服务器完全停止

3. **重新启动**
   ```bash
   python start_server.py
   ```

4. **验证启动成功**
   - 看到 "Application startup complete" 消息
   - 访问 http://localhost:8000/health 应该返回 `{"status":"healthy"}`

---

## 方法2: 使用重启脚本

### Windows PowerShell:

```powershell
.\restart_server.ps1
```

### Windows CMD:

```cmd
restart_server.bat
```

### 说明：
- 脚本会自动查找并停止运行在8000端口的进程
- 然后重新启动服务器
- **注意**: 这会强制终止进程，可能丢失未保存的数据

---

## 方法3: 手动查找并终止进程

### 查找进程：

```powershell
# PowerShell
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
```

```cmd
# CMD
netstat -ano | findstr :8000
```

### 终止进程：

```powershell
# PowerShell (替换 <PID> 为实际进程ID)
Stop-Process -Id <PID> -Force
```

```cmd
# CMD (替换 <PID> 为实际进程ID)
taskkill /F /PID <PID>
```

### 重新启动：

```bash
python start_server.py
```

---

## 验证修复是否生效

### 1. 检查后端日志

重启后，访问股市大屏，后端日志应该显示：

```
INFO: 127.0.0.1:xxxxx - "OPTIONS /api/stock/stats/1 HTTP/1.1" 200 OK
INFO: 127.0.0.1:xxxxx - "GET /api/stock/stats/1 HTTP/1.1" 200 OK
```

**不应该再看到**:
```
WARNING - Authentication failed: Missing parameters - method=OPTIONS
```

### 2. 检查前端

1. 刷新浏览器中的股市大屏页面
2. 打开浏览器开发者工具 (F12)
3. 查看 Network 标签
4. 应该看到 `/api/stock/stats/1` 请求返回 200 状态码

### 3. 测试API

```bash
# 测试OPTIONS请求（CORS预检）
curl -X OPTIONS http://localhost:8000/api/stock/stats/1 \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Authorization" \
  -v

# 应该返回 200 OK
```

---

## 常见问题

### Q: 重启后还是有认证错误？

**A**: 检查以下几点：
1. 确认修改的是正确的文件: `middleware/signature_verification.py`
2. 确认修改已保存
3. 确认重启的是正确的服务器实例
4. 清除浏览器缓存并刷新

### Q: 找不到运行后端的终端窗口？

**A**: 使用方法2或方法3强制重启

### Q: 端口8000被占用？

**A**: 
```powershell
# 查找占用端口的进程
Get-NetTCPConnection -LocalPort 8000

# 终止该进程
Stop-Process -Id <PID> -Force
```

### Q: 重启后前端还是无法连接？

**A**: 
1. 检查后端是否真的在运行: `curl http://localhost:8000/health`
2. 检查防火墙设置
3. 检查前端的API地址配置: `web-admin/.env`

---

## 修改内容摘要

### 文件: `middleware/signature_verification.py`

#### 修改1: 添加OPTIONS请求绕过
```python
# 第63行附近
if request.method == "OPTIONS":
    return await call_next(request)
```

#### 修改2: 添加股市API到白名单
```python
# 第46行附近
self.bypass_prefixes = [
    "/booths", "/products", "/auth", "/events", "/participants", 
    "/api/stock"  # ← 新增这一行
]
```

---

## 完成后的下一步

1. ✅ 重启后端服务器
2. ✅ 刷新前端页面
3. ✅ 验证股市大屏正常工作
4. ✅ 检查无认证错误

---

**需要帮助？** 查看 `CORS_FIX_SUMMARY.md` 了解详细的修复说明。
