# 🔄 后端服务重启指南

## ⚡ 快速重启

### Windows PowerShell

```powershell
# 1. 查找Python进程
Get-Process python

# 2. 停止进程 (替换 <PID> 为实际进程ID，例如 4736)
Stop-Process -Id 4736 -Force

# 3. 重新启动
python start_server.py
```

### 一键重启 (推荐)

```powershell
# 停止所有Python进程并重启
Get-Process python | Stop-Process -Force; python start_server.py
```

## 📋 详细步骤

### 步骤1: 停止当前服务

**方法A: 使用 Ctrl+C**
- 如果服务在当前终端运行，按 `Ctrl+C` 停止

**方法B: 查找并停止进程**
```powershell
# 查找8000端口的进程
netstat -ano | findstr :8000

# 输出示例:
# TCP    0.0.0.0:8000    0.0.0.0:0    LISTENING    4736
#                                                   ^^^^
#                                                   进程ID

# 停止进程
taskkill /F /PID 4736
```

**方法C: 停止所有Python进程**
```powershell
Get-Process python | Stop-Process -Force
```

### 步骤2: 启动服务

```bash
python start_server.py
```

### 步骤3: 验证服务

```bash
# 测试健康检查
curl http://localhost:8000/health

# 或在浏览器打开
# http://localhost:8000/health
```

**期望输出**:
```json
{"status":"healthy","service":"nfc-campus-wallet"}
```

### 步骤4: 测试CORS

```bash
python test_cors.py
```

**期望输出**:
```
✅ 请求成功: 200
✅ CORS头存在
✅ 所有CORS头检查通过
```

## 🧪 验证前端连接

### 1. 清除浏览器缓存

**Chrome/Edge**:
- 按 `Ctrl+Shift+Delete`
- 选择"缓存的图片和文件"
- 点击"清除数据"

**或者硬刷新**:
- 按 `Ctrl+Shift+R` (Windows)
- 或 `Cmd+Shift+R` (Mac)

### 2. 刷新前端页面

1. 打开 http://localhost:3000
2. 打开开发者工具 (F12)
3. 切换到 Network 标签
4. 刷新页面

### 3. 检查网络请求

查看报表API请求:
- `/reports/summary` - 应该返回 200 或 401
- `/reports/booths` - 应该返回 200 或 401
- 响应头应包含 `access-control-allow-origin: *`

## ❌ 故障排除

### 问题: 端口被占用

**错误信息**:
```
Error: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000): 
通常每个套接字地址(协议/网络地址/端口)只允许使用一次。
```

**解决方案**:
```powershell
# 查找占用8000端口的进程
netstat -ano | findstr :8000

# 停止该进程
taskkill /F /PID <进程ID>

# 重新启动
python start_server.py
```

### 问题: 模块未找到

**错误信息**:
```
ModuleNotFoundError: No module named 'xxx'
```

**解决方案**:
```bash
# 激活虚拟环境
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 重新启动
python start_server.py
```

### 问题: 数据库连接失败

**错误信息**:
```
Failed to connect to database
```

**解决方案**:
```bash
# 检查 .env 文件配置
cat .env

# 确认MySQL服务运行
# Windows: 服务管理器中检查MySQL服务

# 测试数据库连接
mysql -u root -p
```

### 问题: CORS错误仍然存在

**解决方案**:
1. 确认后端服务已重启
2. 清除浏览器缓存
3. 硬刷新页面 (Ctrl+Shift+R)
4. 运行 `python test_cors.py` 验证
5. 检查浏览器控制台的错误信息

## 📊 服务状态检查

### 检查服务是否运行

```powershell
# 方法1: 检查端口
netstat -ano | findstr :8000

# 方法2: 检查进程
Get-Process python

# 方法3: 测试API
curl http://localhost:8000/health
```

### 查看服务日志

如果使用 `start_server.py` 启动，日志会输出到终端。

查看最近的日志:
```bash
# 如果日志输出到文件
tail -f logs/app.log

# 或在Windows上
Get-Content logs/app.log -Tail 50 -Wait
```

## 🎯 完整重启流程

```powershell
# 1. 停止服务
Get-Process python | Stop-Process -Force

# 2. 等待2秒
Start-Sleep -Seconds 2

# 3. 启动服务
python start_server.py

# 4. 等待服务启动
Start-Sleep -Seconds 3

# 5. 测试服务
curl http://localhost:8000/health

# 6. 测试CORS
python test_cors.py
```

## ✅ 成功标志

服务成功重启后，你应该看到:

1. **终端输出**:
```
INFO:     Started server process [xxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

2. **健康检查成功**:
```json
{"status":"healthy","service":"nfc-campus-wallet"}
```

3. **CORS测试通过**:
```
✅ 所有CORS头检查通过
✅ 报表端点CORS头存在
✅ OPTIONS预检请求成功
```

4. **前端无错误**:
- 浏览器控制台没有CORS错误
- Network标签显示API请求成功
- 报表数据正常加载

---

**文档版本**: 1.0  
**创建时间**: 2026-05-09  
**适用系统**: Windows  
**需要权限**: 普通用户
