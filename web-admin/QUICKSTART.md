# 🚀 股市大屏快速启动指南

## 3分钟快速上手

### 第一步：安装依赖

```bash
cd web-admin
npm install
```

### 第二步：启动后端

```bash
# 在项目根目录
python start_server.py
```

✅ 后端运行在: `http://localhost:8000`

### 第三步：启动前端

```bash
# 在 web-admin 目录
npm run dev
```

✅ 前端运行在: `http://localhost:5173`

### 第四步：访问大屏

1. 打开浏览器访问: `http://localhost:5173/login`
2. 登录系统
3. 在左侧菜单找到 **"股市大屏"** 菜单项（在"报表中心"下方）
4. 点击菜单项，大屏将在新窗口打开

或直接访问: `http://localhost:5173/stock-dashboard`

---

## 📸 效果预览

### 菜单位置
```
📊 数据看板
📅 活动管理
🏪 摊位管理
🛒 商品管理
👥 参与者管理
💳 交易流水
✅ 退款审批
📈 报表中心
📊 股市大屏 ← 点击这里！
👤 用户管理
```

### 大屏界面

- **左侧**: 全局奖金池 + 市场概况
- **中央**: 经营分排行（ECharts柱状图）
- **右侧**: 股价实时看板（表格）

---

## ⚙️ 配置检查

### 1. 环境变量

确保 `web-admin/.env` 包含:

```env
VITE_API_URL=http://localhost:8000
```

### 2. 依赖检查

```bash
npm list echarts
```

应该显示: `echarts@5.4.3`

### 3. 后端检查

访问: `http://localhost:8000/docs`

应该能看到 FastAPI 文档页面

---

## 🎯 测试数据

### 创建测试数据（可选）

如果系统中没有数据，可以：

1. **创建活动**: 在"活动管理"中创建一个活动
2. **创建摊位**: 在"摊位管理"中添加几个摊位
3. **模拟交易**: 使用Android终端或API进行股票购买
4. **期末结算**: 调用结算API

### 快速测试API

```bash
# 获取市场统计
curl http://localhost:8000/api/stock/stats/1

# 获取结算数据
curl http://localhost:8000/api/stock/settlement/event/1
```

---

## 🐛 常见问题

### Q1: 菜单项不显示？

**A**: 确认已登录，清除浏览器缓存并刷新

### Q2: 点击菜单无反应？

**A**: 检查浏览器是否阻止弹出窗口，允许后重试

### Q3: 大屏显示空白？

**A**: 
1. 检查后端是否运行
2. 检查浏览器控制台错误
3. 确认有数据（需要先有交易记录）

### Q4: 图表不显示？

**A**: 
```bash
npm install echarts
npm run dev
```

---

## 📚 更多文档

- **完整集成文档**: [INTEGRATION_COMPLETE.md](./INTEGRATION_COMPLETE.md)
- **使用手册**: [STOCK_DASHBOARD_README.md](./STOCK_DASHBOARD_README.md)
- **高级功能**: [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)

---

## ✅ 完成！

现在你可以：

1. ✅ 在管理后台看到"股市大屏"菜单
2. ✅ 点击菜单在新窗口打开大屏
3. ✅ 查看实时市场数据和股价排行
4. ✅ 享受高端深色科技风界面

**祝使用愉快！** 🎉

---

*最后更新: 2026-05-09*
