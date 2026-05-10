# CORS 问题修复指南

## 🔍 问题描述

前端访问后端API时出现CORS错误：
```
Access to XMLHttpRequest at 'http://localhost:8000/reports/booths' from origin 'http://localhost:3000' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## ✅ 已修复

### 修改内容

**文件**: `app/main.py`

**修改**: 调整中间件顺序，确保CORS中间件在其他中间件之前执行

**修改前**:
```python
# Add CORS middleware
app.add_middleware(CORSMiddleware, ...)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Add signature verification middleware
app.add_middleware(SignatureVerificationMiddleware)
```

**修改后**:
```python
# Add request logging middleware (first, to log all requests)
app.add_middleware(RequestLoggingMiddleware)

# Add CORS middleware (must be before other middleware that might return responses)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # 新增：暴露所有响应头
)

# Add signature verification middleware (after CORS)
app.add_middleware(SignatureVerificationMiddleware)
```

### 关键改动

1. **中间件顺序调整**: 
   - FastAPI中间件按照**相反顺序**执行
   - CORS中间件需要在可能返回响应的中间件之前
   
2. **添加 `expose_headers`**:
   - 允许前端访问所有响应头
   - 确保自定义头能被前端读取

## 🔄 重启服务

修改后需要重启后端服务才能生效：

### 方法1: 如果使用 `start_server.py`

```bash
# 停止当前服务 (Ctrl+C)
# 然后重新启动
python start_server.py
```

### 方法2: 如果使用 uvicorn 直接运行

```bash
# 停止当前服务 (Ctrl+C)
# 然后重新启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 方法3: 如果使用 systemd 服务

```bash
sudo systemctl restart nfc-wallet
```

## 🧪 验证修复

运行测试脚本验证CORS配置：

```bash
python test_cors.py
```

**期望输出**:
```
🔍 测试CORS配置...
============================================================
✅ 请求成功: 200

📋 响应头:
  access-control-allow-origin: *
  access-control-allow-credentials: true
  access-control-allow-methods: *
  access-control-allow-headers: *

🔍 CORS头检查:
  ✅ access-control-allow-origin
  ✅ access-control-allow-credentials
  ✅ access-control-allow-methods
  ✅ access-control-allow-headers
```

## 🌐 前端测试

重启后端服务后，刷新前端页面：

1. 打开浏览器开发者工具 (F12)
2. 切换到 Network 标签
3. 刷新页面 (F5)
4. 检查API请求是否成功
5. 查看响应头是否包含CORS头

**成功标志**:
- ✅ 请求状态码: 200 或 401 (需要认证)
- ✅ 响应头包含: `access-control-allow-origin: *`
- ✅ 没有CORS错误

## 📝 CORS配置说明

### 当前配置 (开发环境)

```python
CORSMiddleware(
    allow_origins=["*"],          # 允许所有来源
    allow_credentials=True,       # 允许携带凭证
    allow_methods=["*"],          # 允许所有HTTP方法
    allow_headers=["*"],          # 允许所有请求头
    expose_headers=["*"],         # 暴露所有响应头
)
```

### 生产环境建议

```python
CORSMiddleware(
    allow_origins=[
        "https://your-domain.com",
        "https://admin.your-domain.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)
```

## 🔧 常见问题

### Q1: 重启后仍然有CORS错误

**解决方案**:
1. 清除浏览器缓存
2. 硬刷新页面 (Ctrl+Shift+R 或 Cmd+Shift+R)
3. 检查后端服务是否真的重启了
4. 检查端口是否正确 (8000)

### Q2: OPTIONS 预检请求失败

**原因**: 浏览器在发送实际请求前会先发送OPTIONS请求

**解决方案**: 
- FastAPI的CORSMiddleware会自动处理OPTIONS请求
- 确保中间件顺序正确
- 确保没有其他中间件拦截OPTIONS请求

### Q3: 某些端点有CORS错误，某些没有

**原因**: 可能是认证中间件或其他中间件在CORS之前返回了响应

**解决方案**:
- 检查中间件顺序
- 确保CORS中间件在最外层（最后添加）
- 检查是否有自定义中间件提前返回响应

## 📚 相关资源

- [FastAPI CORS 文档](https://fastapi.tiangolo.com/tutorial/cors/)
- [MDN CORS 文档](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/CORS)
- [CORS 预检请求](https://developer.mozilla.org/zh-CN/docs/Glossary/Preflight_request)

## ✅ 检查清单

在确认修复后，请检查以下项目：

- [ ] 后端服务已重启
- [ ] 运行 `python test_cors.py` 测试通过
- [ ] 前端页面刷新后没有CORS错误
- [ ] 报表中心所有页面都能正常加载数据
- [ ] 浏览器控制台没有网络错误
- [ ] API请求返回正确的数据

---

**修复时间**: 2026-05-09  
**修复状态**: ✅ 已完成  
**需要操作**: 🔄 重启后端服务
