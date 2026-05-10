# CORS 完整修复方案

## 🔍 问题分析

### 问题1: CORS头在某些响应中缺失
- ✅ 健康检查端点 (`/health`) 有CORS头
- ❌ 认证失败响应 (401) 缺少CORS头
- ❌ 缺少 `access-control-allow-methods` 和 `access-control-allow-headers`

### 根本原因
FastAPI的 `HTTPException` 不会自动添加CORS头，需要通过异常处理器来确保所有响应都包含CORS头。

## ✅ 完整修复方案

### 修改1: 添加异常处理器

**文件**: `app/main.py`

**添加导入**:
```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
```

**添加异常处理器** (在注册路由之前):
```python
# Add exception handlers to ensure CORS headers are included in error responses
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions and ensure CORS headers are included"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.exception_handler(HTTPException)
async def fastapi_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTP exceptions and ensure CORS headers are included"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )
```

### 修改2: 调整中间件顺序和配置

**CORS中间件配置**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 允许所有来源
    allow_credentials=True,       # 允许携带凭证
    allow_methods=["*"],          # 允许所有HTTP方法
    allow_headers=["*"],          # 允许所有请求头
    expose_headers=["*"],         # 暴露所有响应头
)
```

**中间件顺序** (从外到内):
1. RequestLoggingMiddleware (最外层)
2. CORSMiddleware
3. SignatureVerificationMiddleware (最内层)

## 🔄 应用修复

### 步骤1: 确认修改已保存

检查 `app/main.py` 文件是否包含上述修改。

### 步骤2: 重启后端服务

**方法A: 使用 start_server.py**
```bash
# 停止当前服务 (Ctrl+C 或 Cmd+C)
# 然后重新启动
python start_server.py
```

**方法B: 使用 uvicorn**
```bash
# 停止当前服务 (Ctrl+C)
# 然后重新启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**方法C: 在Windows上强制停止并重启**
```powershell
# 查找进程
Get-Process | Where-Object {$_.ProcessName -like "*python*"}

# 停止进程 (替换 <PID> 为实际进程ID)
Stop-Process -Id <PID> -Force

# 重新启动
python start_server.py
```

### 步骤3: 验证修复

运行测试脚本:
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

🔍 CORS头检查:
  ✅ access-control-allow-origin
  ✅ access-control-allow-credentials
  ✅ access-control-allow-methods
  ✅ access-control-allow-headers

============================================================
🔍 测试报表端点（需要认证）...
状态码: 401
✅ 端点存在（需要认证）
✅ CORS头存在:
  access-control-allow-origin: *
  access-control-allow-credentials: true
  access-control-allow-methods: *
  access-control-allow-headers: *

============================================================
🔍 测试OPTIONS预检请求...
状态码: 200
✅ OPTIONS请求成功
✅ CORS预检响应头:
  access-control-allow-origin: *
  access-control-allow-credentials: true
  access-control-allow-methods: *
  access-control-allow-headers: *
```

## 🌐 前端验证

### 步骤1: 清除浏览器缓存

1. 打开浏览器开发者工具 (F12)
2. 右键点击刷新按钮
3. 选择"清空缓存并硬性重新加载"

或者:
- Chrome/Edge: Ctrl+Shift+Delete
- Firefox: Ctrl+Shift+Delete
- Safari: Cmd+Option+E

### 步骤2: 刷新前端页面

1. 打开前端应用 (http://localhost:3000)
2. 打开开发者工具 (F12)
3. 切换到 Network 标签
4. 刷新页面 (F5 或 Ctrl+R)

### 步骤3: 检查网络请求

查看报表相关的API请求:
- `/reports/summary`
- `/reports/booths`
- `/leaderboard/revenue`
- 等等

**成功标志**:
- ✅ 状态码: 200 (已登录) 或 401 (未登录)
- ✅ 响应头包含: `access-control-allow-origin: *`
- ✅ 没有CORS错误消息
- ✅ 数据正常加载

### 步骤4: 测试报表功能

1. 登录系统
2. 访问报表中心各个页面:
   - 总览看板
   - 摊位报表
   - 摊位排行榜
   - 商品排行榜
   - 异常审计
   - 报表导出

3. 确认:
   - ✅ 数据正常加载
   - ✅ 没有网络错误
   - ✅ 表格显示正常
   - ✅ 导出功能正常

## 🔧 故障排除

### 问题1: 重启后仍有CORS错误

**可能原因**:
- 浏览器缓存未清除
- 后端服务未真正重启
- 修改未保存

**解决方案**:
```bash
# 1. 确认后端服务已停止
netstat -ano | findstr :8000

# 2. 如果有进程，强制停止
# 在Windows上:
taskkill /F /PID <进程ID>

# 3. 重新启动
python start_server.py

# 4. 验证服务运行
curl http://localhost:8000/health

# 5. 清除浏览器缓存并刷新
```

### 问题2: OPTIONS请求失败

**症状**:
```
Access to XMLHttpRequest has been blocked by CORS policy: 
Response to preflight request doesn't pass access control check
```

**解决方案**:
1. 确认CORS中间件配置正确
2. 确认异常处理器已添加
3. 检查是否有其他中间件拦截OPTIONS请求
4. 重启服务

### 问题3: 某些端点有CORS，某些没有

**可能原因**:
- 中间件顺序不正确
- 某些路由没有经过CORS中间件

**解决方案**:
1. 检查中间件顺序
2. 确保所有路由都在CORS中间件之后注册
3. 检查是否有自定义中间件提前返回响应

### 问题4: 生产环境CORS配置

**开发环境** (当前):
```python
allow_origins=["*"]  # 允许所有来源
```

**生产环境** (推荐):
```python
allow_origins=[
    "https://your-domain.com",
    "https://admin.your-domain.com",
]
```

## 📊 完整的 app/main.py 结构

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

def create_app() -> FastAPI:
    # ... 初始化代码 ...
    
    app = FastAPI(...)
    
    # 1. 添加日志中间件
    app.add_middleware(RequestLoggingMiddleware)
    
    # 2. 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # 3. 添加签名验证中间件
    app.add_middleware(SignatureVerificationMiddleware)
    
    # 4. 添加异常处理器
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    
    @app.exception_handler(HTTPException)
    async def fastapi_exception_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    
    # 5. 注册路由
    app.include_router(auth_router, tags=["authentication"])
    # ... 其他路由 ...
    
    return app
```

## ✅ 验证清单

完成修复后，请确认以下项目:

- [ ] `app/main.py` 已添加异常处理器
- [ ] CORS中间件配置包含 `expose_headers=["*"]`
- [ ] 后端服务已重启
- [ ] 运行 `python test_cors.py` 全部通过
- [ ] 浏览器缓存已清除
- [ ] 前端页面刷新后没有CORS错误
- [ ] 报表中心所有页面正常加载
- [ ] API请求返回正确数据
- [ ] 导出功能正常工作

## 📚 相关资源

- [FastAPI CORS文档](https://fastapi.tiangolo.com/tutorial/cors/)
- [FastAPI异常处理](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [MDN CORS指南](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/CORS)
- [CORS预检请求](https://developer.mozilla.org/zh-CN/docs/Glossary/Preflight_request)

---

**修复版本**: 2.0  
**修复时间**: 2026-05-09  
**修复状态**: ✅ 完整方案  
**需要操作**: 🔄 重启后端服务 + 清除浏览器缓存
