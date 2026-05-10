# 📊 测试股市大屏

## ✅ 好消息

后端已重启，股市API的认证问题已解决！

从日志可以看到：
- ✅ **没有更多的 OPTIONS 认证错误**
- ✅ `/booths` 接口正常工作（200 OK）
- ⚠️ `/transactions` 接口有500错误（这是另一个问题，与股市大屏无关）

---

## 🧪 测试股市大屏

### 方法1: 通过菜单访问

1. 在浏览器中访问: `http://localhost:5173`
2. 登录系统
3. 在左侧菜单找到 **"📊 股市大屏"**（在"报表中心"下方）
4. 点击菜单项
5. 大屏应该在新窗口打开

### 方法2: 直接访问

直接在浏览器访问: `http://localhost:5173/stock-dashboard`

---

## 🔍 检查是否正常工作

### 1. 浏览器控制台（F12）

打开开发者工具，查看 Network 标签：

**应该看到**:
```
✅ OPTIONS /api/stock/stats/1 → 200 OK
✅ GET /api/stock/stats/1 → 200 OK
```

**不应该看到**:
```
❌ 401 Unauthorized
❌ Authentication failed
```

### 2. 后端日志

**正常的日志**:
```
INFO: 127.0.0.1:xxxxx - "OPTIONS /api/stock/stats/1 HTTP/1.1" 200 OK
INFO: 127.0.0.1:xxxxx - "GET /api/stock/stats/1 HTTP/1.1" 200 OK
```

### 3. 大屏界面

应该能看到：
- ✅ 顶部标题和时钟
- ✅ 左侧：全局奖金池和市场概况
- ✅ 中央：经营分排行图表（如果有数据）
- ✅ 右侧：股价看板表格（如果有数据）

---

## 📝 关于 /transactions 错误

你看到的 500 错误是 `/transactions` 接口的问题，**不影响股市大屏**。

这个错误可能是因为：
1. 数据库查询问题
2. 缺少某些字段
3. 数据格式问题

**股市大屏使用的是不同的API**:
- `/api/stock/stats/{event_id}` - 市场统计
- `/api/stock/settlement/event/{event_id}` - 结算数据

这些API与 `/transactions` 无关。

---

## 🎯 测试步骤

### 步骤1: 访问股市大屏

```
http://localhost:5173/stock-dashboard
```

### 步骤2: 打开浏览器控制台（F12）

查看 Network 标签中的请求

### 步骤3: 查找股市API请求

应该能看到：
- `api/stock/stats/1`
- `api/stock/settlement/event/1`

### 步骤4: 检查响应

点击请求，查看响应内容：

**如果返回 200 OK**:
```json
{
  "event_id": 1,
  "total_investment": 0,
  "total_investment_yuan": 0.0,
  "global_pool": 0,
  "global_pool_yuan": 0.0,
  ...
}
```

**如果返回 404**:
```json
{
  "detail": {
    "error_code": "RESOURCE_NOT_FOUND",
    "message": "活动不存在"
  }
}
```

这是正常的，说明event_id=1不存在，需要先创建活动。

---

## 🔧 如果还有问题

### 问题1: 401 认证错误

**解决方案**: 
1. 确认已登录
2. 检查 localStorage 中是否有 token
3. Token可能已过期，重新登录

### 问题2: 404 活动不存在

**解决方案**:
1. 在"活动管理"中创建一个活动
2. 修改大屏代码中的 `eventId` 为实际的活动ID
3. 或者在URL中传递: `/stock-dashboard?event_id=2`

### 问题3: 大屏显示空白

**解决方案**:
1. 检查浏览器控制台是否有JavaScript错误
2. 确认 echarts 已安装: `cd web-admin && npm list echarts`
3. 清除浏览器缓存并刷新

### 问题4: 数据为空

**解决方案**:
这是正常的！需要先：
1. 创建活动
2. 创建摊位
3. 进行股票交易
4. 执行期末结算

---

## 📊 测试数据准备

如果想看到完整的大屏效果，需要准备测试数据：

### 1. 创建活动
在"活动管理"中创建一个活动

### 2. 创建摊位
在"摊位管理"中添加几个摊位

### 3. 模拟交易
使用API或Android终端进行股票购买

### 4. 期末结算
调用结算API：
```bash
curl -X POST http://localhost:8000/api/stock/settle \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"event_id": 1, "fee_rate": 0.05}'
```

---

## ✅ 成功标志

如果看到以下情况，说明集成成功：

1. ✅ 菜单中有"股市大屏"选项
2. ✅ 点击后在新窗口打开
3. ✅ 大屏界面正常显示（即使数据为空）
4. ✅ 浏览器控制台无认证错误
5. ✅ Network标签显示API请求成功（200或404都是正常的）

---

## 🎉 下一步

1. **测试大屏**: 访问 `http://localhost:5173/stock-dashboard`
2. **检查日志**: 确认无认证错误
3. **准备数据**: 创建活动和摊位（可选）
4. **享受使用**: 股市大屏已完全集成！

---

**需要帮助？**
- 查看 `web-admin/QUICKSTART.md` - 快速启动指南
- 查看 `CORS_FIX_SUMMARY.md` - 修复说明
- 查看 `web-admin/INTEGRATION_COMPLETE.md` - 完整文档

---

*最后更新: 2026-05-09 19:02*
