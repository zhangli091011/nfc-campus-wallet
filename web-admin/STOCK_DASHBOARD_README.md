# 📊 期末结算与动态市值大屏

## 功能概述

高端深色科技风数据可视化大屏，用于实时展示校园模拟股市的交易数据和期末结算结果。

### 核心特性
- 🎨 **深色科技风UI**: 深蓝 + 银色 + 黑金配色
- 📈 **实时数据刷新**: 每5秒自动更新数据
- 📊 **ECharts可视化**: 动态横向柱状图展示经营分排行
- 💰 **全局奖金池**: 实时显示奖金池和手续费
- 🏆 **股价看板**: 展示各摊位股价、涨跌幅、投资数据
- ⚡ **流畅动画**: 数字滚动、图表过渡动画

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd web-admin
npm install
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
VITE_API_URL=http://localhost:8000
```

### 3. 启动开发服务器

```bash
npm run dev
```

### 4. 访问大屏

打开浏览器访问：`http://localhost:5173/dashboard`

---

## 📐 页面布局

### 顶部标题栏
- **左侧**: 活动标题 + 图标
- **右侧**: 状态指示灯 + 实时时钟

### 三栏布局

#### 左侧面板 - 宏观资金池 (350px)
- **全局奖金池卡片**
  - 当前奖金池金额（大号金色发光数字）
  - 总投资额
  - 手续费总额
  
- **市场概况卡片**
  - 参与摊位数
  - 投资人数
  - 订单总数

#### 中央面板 - 经营指数排行 (自适应)
- **ECharts横向柱状图**
  - 各摊位综合经营分排行
  - 第一名金色渐变，其他蓝色渐变
  - 平滑动画过渡

#### 右侧面板 - 模拟股价看板 (450px)
- **最被看好公司**
  - 金色高亮显示第一名
  - 显示摊位名称和股价
  
- **股价数据表格**
  - 排名（第一名显示奖杯图标）
  - 摊位名称 + 班级
  - 当前股价 + 涨跌幅
  - 售出股数
  - 总投资额
  - 经营分

---

## 🎨 设计规范

### 配色方案

| 用途 | 颜色 | 色值 |
|------|------|------|
| 主背景 | 深蓝黑 | `#0A0E27` |
| 次背景 | 深蓝灰 | `#1A2F4F` |
| 主色调 | 金色 | `#FFD700` |
| 辅助色 | 蓝色 | `#4A90E2` |
| 文字主色 | 银色 | `#C0C0C0` |
| 文字次色 | 灰蓝 | `#8B9DC3` |
| 成功色 | 绿色 | `#50C878` |
| 警告色 | 红色 | `#E74C3C` |

### 字体规范

- **标题**: SF Pro Display, 32px, Bold
- **卡片标题**: 18px, Semi-bold
- **数据大号**: 48px, Bold, Courier New
- **数据中号**: 24px, Bold
- **正文**: 14-16px, Regular

### 动画效果

1. **金色发光动画** (`glow`)
   - 奖金池金额持续发光
   - 2秒循环

2. **状态灯脉冲** (`pulse`)
   - 状态指示灯闪烁
   - 2秒循环

3. **卡片悬停**
   - 边框变金色
   - 轻微上浮
   - 阴影增强

4. **图表动画**
   - 柱状图从左到右展开
   - 1秒缓动动画

---

## 🔌 API接口

### 1. 获取市场统计

```
GET /api/stock/stats/{event_id}
```

**响应**:
```json
{
  "event_id": 1,
  "total_investment": 240000,
  "total_investment_yuan": 2400.0,
  "global_pool": 228000,
  "global_pool_yuan": 2280.0,
  "fee_collected": 12000,
  "fee_collected_yuan": 120.0,
  "total_orders": 50,
  "total_investors": 30,
  "total_booths": 3,
  "is_settled": true
}
```

### 2. 获取结算数据

```
GET /api/stock/settlement/event/{event_id}
```

**响应**:
```json
{
  "booths": [
    {
      "booth_id": 1,
      "booth_name": "美食摊",
      "class_name": "高一(1)班",
      "revenue": 5000,
      "revenue_yuan": 50.0,
      "profit": 3000,
      "profit_yuan": 30.0,
      "order_count": 50,
      "score": 3900.0,
      "ratio": 0.4149,
      "sold_shares": 100,
      "total_investment": 100000,
      "total_investment_yuan": 1000.0,
      "final_price": 946,
      "final_price_yuan": 9.46
    }
  ]
}
```

---

## 📱 响应式设计

### 大屏 (>1600px)
- 三栏布局: 350px | 自适应 | 450px
- 完整显示所有数据

### 中屏 (1200px - 1600px)
- 三栏布局: 300px | 自适应 | 400px
- 字体略小

### 小屏 (<1200px)
- 单栏布局，垂直排列
- 左侧 → 中央 → 右侧

---

## 🔧 自定义配置

### 修改刷新间隔

在 `StockDashboard.tsx` 中修改：

```typescript
const interval = setInterval(loadData, 5000); // 5秒刷新
```

### 修改活动ID

```typescript
const eventId = 1; // 修改为实际活动ID
```

### 修改图表配置

在 `updateChart()` 函数中修改 ECharts 配置：

```typescript
const option: echarts.EChartsOption = {
  // 自定义配置
};
```

---

## 🎯 使用场景

### 场景1: 活动期间实时监控

1. 打开大屏页面
2. 系统自动每5秒刷新数据
3. 实时查看各摊位经营情况
4. 监控投资热度和资金流向

### 场景2: 期末结算展示

1. 管理员触发期末结算
2. 大屏自动切换到"已结算"状态
3. 显示最终股价和排名
4. 展示各摊位经营分和分红占比

### 场景3: 大屏投影展示

1. 连接投影仪或大屏幕
2. 全屏显示（F11）
3. 适合活动现场展示
4. 吸引参与者关注

---

## 🐛 故障排查

### 问题1: 数据不显示

**原因**: 
- 后端服务未启动
- API地址配置错误
- 未登录或token过期

**解决**:
```bash
# 检查后端服务
curl http://localhost:8000/health

# 检查环境变量
cat .env

# 重新登录获取token
```

### 问题2: 图表不显示

**原因**: 
- ECharts未正确安装
- 数据格式错误

**解决**:
```bash
# 重新安装依赖
npm install echarts

# 检查控制台错误
```

### 问题3: 样式错乱

**原因**: 
- CSS文件未正确导入
- Ant Design样式冲突

**解决**:
```typescript
// 确保导入CSS
import './StockDashboard.css';
```

---

## 📊 数据流程

```
┌─────────────┐
│   大屏组件   │
└──────┬──────┘
       │
       │ 每5秒请求
       ↓
┌─────────────┐
│  后端API    │
└──────┬──────┘
       │
       │ 查询数据库
       ↓
┌─────────────┐
│   MySQL     │
└─────────────┘
```

---

## 🚀 性能优化

### 1. 图表优化
- 使用 `echarts.init()` 单例模式
- 避免频繁重新创建图表实例
- 使用 `setOption(option, true)` 合并配置

### 2. 数据缓存
- 使用 React State 缓存数据
- 避免不必要的重新渲染

### 3. 动画优化
- 使用 CSS3 动画代替 JavaScript
- 使用 `transform` 代替 `top/left`
- 使用 `will-change` 提示浏览器优化

---

## 📝 开发指南

### 添加新的数据卡片

```typescript
<Card className="data-card" bordered={false}>
  <div className="card-header">
    <YourIcon className="card-icon" />
    <span>卡片标题</span>
  </div>
  {/* 卡片内容 */}
</Card>
```

### 添加新的统计指标

```typescript
<Statistic
  title={<span className="stat-title">指标名称</span>}
  value={value}
  suffix="单位"
  valueStyle={{ color: '#4A90E2', fontSize: 32 }}
/>
```

### 修改图表样式

```typescript
const option: echarts.EChartsOption = {
  backgroundColor: 'transparent',
  // 其他配置...
};
```

---

## 📞 技术支持

如有问题，请查看以下文档：
- [股票市场系统文档](../../docs/STOCK_MARKET_SYSTEM.md)
- [API文档](../../docs/API_DOCUMENTATION.md)
- [后端README](../../README.md)

---

**Made with ❤️ for campus financial education**
