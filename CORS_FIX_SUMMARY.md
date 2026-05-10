# 🔧 CORS 和认证问题修复

## 问题描述

前端访问股市API时出现认证错误：
```
Authentication failed: Missing parameters - method=OPTIONS, path=/api/stock/stats/1
```

## 根本原因

1. **CORS预检请求被拦截**: 浏览器发送OPTIONS请求进行CORS预检，但签名验证中间件要求认证
2. **股市API路径未加入白名单**: `/api/stock/*` 路径使用JWT认证，但未加入签名验证中间件的bypass列表

## 解决方案

### 修改文件: `middleware/signature_verification.py`

#### 1. 添加OPTIONS请求绕过

```python
async def dispatch(self, request: Request, call_next):
    # Bypass authentication for OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return await call_next(request)
    
    # ... 其他代码
```

**原因**: CORS预检请求不包含认证信息，必须允许通过

#### 2. 添加股市API路径到白名单

```python
# Path prefixes that bypass authentication (for JWT-authenticated endpoints)
self.bypass_prefixes = [
    "/booths", 
    "/products", 
    "/auth", 
    "/events", 
    "/participants", 
    "/api/stock"  # ← 新增
]
```

**原因**: 股市API使用JWT认证（Bearer Token），不需要签名验证

## 认证机制说明

### 系统中的两种认证方式

#### 1. 签名认证（Signature Authentication）
- **用途**: NFC终端设备（Android收银端、投资端）
- **参数**: `uid`, `timestamp`, `signature`
- **适用路径**: `/recharge`, `/pay`, `/balance`

#### 2. JWT认证（Bearer Token）
- **用途**: Web管理后台
- **Header**: `Authorization: Bearer <token>`
- **适用路径**: `/auth/*`, `/events/*`, `/booths/*`, `/api/stock/*`

### 中间件处理流程

```
请求到达
    ↓
OPTIONS请求? → 是 → 直接通过（CORS预检）
    ↓ 否
路径在bypass_paths? → 是 → 直接通过
    ↓ 否
路径前缀在bypass_prefixes? → 是 → 直接通过（JWT认证由路由处理）
    ↓ 否
提取签名参数
    ↓
验证签名
    ↓
通过/拒绝
```

## 测试验证

### 1. 测试CORS预检

```bash
curl -X OPTIONS http://localhost:8000/api/stock/stats/1 \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Authorization"
```

**期望结果**: 返回200，包含CORS头

### 2. 测试股市API

```bash
# 先登录获取token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'

# 使用token访问股市API
curl http://localhost:8000/api/stock/stats/1 \
  -H "Authorization: Bearer <your_token>"
```

**期望结果**: 返回股市统计数据

### 3. 测试前端访问

1. 启动后端: `python start_server.py`
2. 启动前端: `cd web-admin && npm run dev`
3. 登录系统
4. 点击"股市大屏"菜单
5. 检查浏览器控制台是否有错误

**期望结果**: 大屏正常显示数据，无认证错误

## 影响范围

### 修改的文件
- `middleware/signature_verification.py`

### 影响的功能
- ✅ 股市大屏数据加载
- ✅ 所有使用JWT认证的API
- ✅ CORS预检请求

### 不影响的功能
- ✅ NFC终端签名认证
- ✅ 现有的支付、充值功能
- ✅ 其他管理后台功能

## 安全性说明

### 为什么允许OPTIONS请求通过？

OPTIONS请求是浏览器自动发送的CORS预检请求，不包含任何敏感操作：
- 不读取数据
- 不修改数据
- 仅用于检查CORS策略

### 为什么股市API不需要签名验证？

股市API使用JWT认证，安全性由以下机制保证：
1. **JWT Token验证**: 每个请求必须包含有效的JWT token
2. **Token过期机制**: Token有时效性
3. **角色权限检查**: 路由层面检查用户角色
4. **HTTPS传输**: 生产环境使用HTTPS加密

## 后续优化建议

### 1. 统一认证中间件

考虑将签名认证和JWT认证统一到一个中间件中：

```python
class UnifiedAuthMiddleware:
    async def dispatch(self, request, call_next):
        # 1. 检查是否OPTIONS
        # 2. 检查JWT token
        # 3. 检查签名
        # 4. 根据路径选择认证方式
```

### 2. 更细粒度的路径控制

使用正则表达式或路径模式匹配：

```python
self.jwt_auth_patterns = [
    r"^/api/stock/.*",
    r"^/auth/.*",
    r"^/events/.*"
]
```

### 3. 添加速率限制

为API添加速率限制防止滥用：

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.get("/api/stock/stats/{event_id}")
@limiter.limit("10/minute")
async def get_stats(...):
    ...
```

## 相关文档

- **认证文档**: `docs/AUTHENTICATION_AUTHORIZATION.md`
- **API文档**: `docs/API_DOCUMENTATION.md`
- **股市系统**: `docs/STOCK_MARKET_SYSTEM.md`

## 变更日志

- **2026-05-09**: 修复CORS预检和股市API认证问题
  - 添加OPTIONS请求绕过
  - 添加`/api/stock`到JWT认证白名单

---

**修复完成！** 🎉

现在前端应该可以正常访问股市API了。
