# 报表系统升级总结

## 📊 项目概述

本次升级为 NFC 校园钱包系统新增了完整的报表、排行榜、经营分析和导出功能。所有统计数据均基于账本流水（transactions 表），确保数据准确性和可审计性。

## ✅ 已完成功能

### 一、后端 API 实现

#### 1. 总览统计 API
- **接口**: `GET /reports/summary`
- **功能**: 提供活动总览数据
- **统计指标**:
  - 总发放额度（issue 类型交易）
  - 总充值额（recharge 类型交易）
  - 总消费额（pay 类型交易）
  - 总退款额（refund 类型交易）
  - 净消费额（总消费 - 总退款）
  - 总交易笔数
  - 参与者数量
  - 摊位数量

#### 2. 摊位维度报表 API
- **接口**: `GET /reports/booths`
- **功能**: 提供摊位经营数据分析
- **统计指标**:
  - 营业额（pay 类型交易总额）
  - 退款额（refund 类型交易总额）
  - 净收入（营业额 - 退款）
  - 销量（pay 类型交易笔数）
  - 总成本（基于商品成本价和销量）
  - 利润（净收入 - 成本）
  - 利润率（利润 / 净收入 * 100%）

#### 3. 商品维度报表 API
- **接口**: `GET /reports/products`
- **功能**: 提供商品销售数据分析
- **统计指标**:
  - 销量（件数）
  - 收入（元）
  - 总成本（元）
  - 利润（元）
  - 利润率（%）

#### 4. 排行榜 API
- **营业额排行榜**: `GET /leaderboard/revenue`
  - 按摊位营业额降序排序
  
- **利润排行榜**: `GET /leaderboard/profit`
  - 按摊位利润降序排序
  
- **利润率排行榜**: `GET /leaderboard/roi`
  - 按摊位利润率降序排序
  
- **商品排行榜**: `GET /leaderboard/products`
  - 支持按销量、收入、利润排序
  - 参数: `metric` (sales/revenue/profit)

#### 5. 异常审计日志 API
- **接口**: `GET /reports/audit-logs`
- **功能**: 检测和标记异常交易
- **异常类型**:
  - **高频退款**: 同一操作员在1小时内退款超过5次
  - **大额更正**: adjust 类型且金额 > 1000元
  - **可疑操作**: 深夜交易（22:00-06:00）

#### 6. 导出功能 API
- **接口**: `GET /reports/export/excel`
- **功能**: 导出报表为 Excel 文件
- **支持类型**:
  - summary: 总览统计
  - booths: 摊位报表
  - products: 商品报表
  - transactions: 交易流水（最多10000条）

### 二、前端页面实现

#### 1. 报表看板页 (`/reports/dashboard`)
- **文件**: `web-admin/src/pages/Reports/Dashboard.tsx`
- **功能**:
  - 展示8个关键指标卡片
  - 支持按活动筛选
  - 一键导出 Excel

#### 2. 摊位报表页 (`/reports/booths`)
- **文件**: `web-admin/src/pages/Reports/BoothReport.tsx`
- **功能**:
  - 表格展示所有摊位经营数据
  - 支持按活动筛选
  - 支持多列排序
  - 利润率彩色标签显示
  - 导出 Excel

#### 3. 摊位排行榜页 (`/reports/booth-leaderboard`)
- **文件**: `web-admin/src/pages/Reports/BoothLeaderboard.tsx`
- **功能**:
  - 三种排行榜切换（营业额/利润/利润率）
  - 前三名特殊样式和图标
  - 支持 TOP 10/20/50 切换
  - 支持按活动筛选

#### 4. 商品排行榜页 (`/reports/product-leaderboard`)
- **文件**: `web-admin/src/pages/Reports/ProductLeaderboard.tsx`
- **功能**:
  - 三种排行榜切换（销量/收入/利润）
  - 前三名特殊样式和图标
  - 支持 TOP 10/20/50 切换
  - 支持按活动筛选

#### 5. 异常审计日志页 (`/reports/audit-logs`)
- **文件**: `web-admin/src/pages/Reports/AuditLogs.tsx`
- **功能**:
  - 展示异常交易记录
  - 支持按异常类型筛选
  - 彩色标签和图标标识异常类型
  - 支持按活动筛选
  - 显示最近 50/100/200/500 条

#### 6. 报表导出页 (`/reports/export`)
- **文件**: `web-admin/src/pages/Reports/ExportPage.tsx`
- **功能**:
  - 统一的导出入口
  - 四种报表类型选择
  - 支持按活动筛选
  - 自动生成文件名（包含活动名和日期）

### 三、服务层实现

#### 1. 报表服务 (`services/report_service.py`)
- **类**: `ReportService`
- **方法**:
  - `get_summary_report()`: 总览统计
  - `get_booth_report()`: 摊位报表
  - `get_product_report()`: 商品报表
  - `get_revenue_leaderboard()`: 营业额排行榜
  - `get_profit_leaderboard()`: 利润排行榜
  - `get_roi_leaderboard()`: 利润率排行榜
  - `get_product_leaderboard()`: 商品排行榜
  - `get_audit_logs()`: 异常审计日志

#### 2. 导出服务 (`services/export_service.py`)
- **类**: `ExportService`
- **方法**:
  - `export_to_excel()`: 导出为 Excel
  - `_export_summary_report()`: 导出总览统计
  - `_export_booth_report()`: 导出摊位报表
  - `_export_product_report()`: 导出商品报表
  - `_export_transaction_report()`: 导出交易流水

#### 3. 前端报表服务 (`web-admin/src/services/report.ts`)
- **函数**:
  - `getSummaryReport()`: 获取总览统计
  - `getBoothReport()`: 获取摊位报表
  - `getProductReport()`: 获取商品报表
  - `getRevenueLeaderboard()`: 获取营业额排行榜
  - `getProfitLeaderboard()`: 获取利润排行榜
  - `getRoiLeaderboard()`: 获取利润率排行榜
  - `getProductLeaderboard()`: 获取商品排行榜
  - `getAuditLogs()`: 获取异常审计日志
  - `exportReportExcel()`: 导出 Excel
  - `downloadExcel()`: 下载 Excel 文件

### 四、路由配置

#### 后端路由 (`routes/reports.py` 和 `routes/leaderboard.py`)
- 已在 `app/main.py` 中注册
- 所有接口需要权限验证（super_admin, event_admin, reviewer）

#### 前端路由 (`web-admin/src/routes/index.tsx`)
- 新增报表相关路由：
  - `/reports/dashboard`: 总览看板
  - `/reports/booths`: 摊位报表
  - `/reports/booth-leaderboard`: 摊位排行榜
  - `/reports/product-leaderboard`: 商品排行榜
  - `/reports/audit-logs`: 异常审计
  - `/reports/export`: 报表导出

#### 侧边栏菜单 (`web-admin/src/components/Layout/index.tsx`)
- 新增"报表中心"菜单组
- 包含6个子菜单项

## 🎯 核心特性

### 1. 基于账本流水的统计
- ✅ 所有统计数据从 `transactions` 表计算
- ✅ 不依赖简单的 `balance` 字段
- ✅ 确保数据准确性和可审计性

### 2. 多维度分析
- ✅ 总览维度：全局统计
- ✅ 摊位维度：经营分析
- ✅ 商品维度：销售分析
- ✅ 排行榜维度：竞争分析

### 3. 异常检测
- ✅ 高频退款检测
- ✅ 大额更正检测
- ✅ 可疑操作检测（深夜交易）

### 4. 数据导出
- ✅ Excel 格式导出
- ✅ 支持多种报表类型
- ✅ 自动格式化和样式设置

### 5. 用户体验
- ✅ 响应式设计
- ✅ 实时数据加载
- ✅ 多种筛选和排序选项
- ✅ 直观的数据可视化

## 📁 文件结构

```
backend/
├── routes/
│   ├── reports.py              # 报表路由（已存在，已完善）
│   └── leaderboard.py          # 排行榜路由（已存在，已完善）
├── services/
│   ├── report_service.py       # 报表服务（已存在，已完善）
│   └── export_service.py       # 导出服务（已存在，已完善）
└── schemas/
    └── report.py               # 报表 Schema（已存在，已完善）

frontend/
├── src/
│   ├── pages/
│   │   └── Reports/
│   │       ├── Dashboard.tsx           # 总览看板（新增）
│   │       ├── BoothReport.tsx         # 摊位报表（新增）
│   │       ├── BoothLeaderboard.tsx    # 摊位排行榜（新增）
│   │       ├── ProductLeaderboard.tsx  # 商品排行榜（新增）
│   │       ├── AuditLogs.tsx           # 异常审计（新增）
│   │       ├── ExportPage.tsx          # 报表导出（新增）
│   │       └── index.ts                # 导出索引（新增）
│   ├── services/
│   │   └── report.ts           # 报表服务（新增）
│   ├── routes/
│   │   └── index.tsx           # 路由配置（已更新）
│   └── components/
│       └── Layout/
│           └── index.tsx       # 布局组件（已更新）
```

## 🔧 技术栈

### 后端
- **框架**: FastAPI
- **ORM**: SQLAlchemy
- **数据库**: SQLite/PostgreSQL
- **Excel 导出**: openpyxl
- **权限控制**: JWT + 角色验证

### 前端
- **框架**: React 18 + TypeScript
- **UI 库**: Ant Design 5
- **路由**: React Router 6
- **HTTP 客户端**: Axios
- **日期处理**: dayjs
- **构建工具**: Vite

## 📊 数据流程

### 统计数据计算流程
```
1. 前端发起请求 → 2. 后端接收请求
                    ↓
3. 查询 transactions 表 ← 4. 应用筛选条件（event_id, booth_id 等）
                    ↓
5. 按交易类型分组统计 → 6. 计算派生指标（利润、利润率等）
                    ↓
7. 格式化数据 → 8. 返回 JSON 响应
                    ↓
9. 前端接收数据 → 10. 渲染页面
```

### Excel 导出流程
```
1. 前端点击导出按钮 → 2. 调用导出 API
                        ↓
3. 后端查询数据 → 4. 创建 Excel 工作簿
                        ↓
5. 写入数据和样式 → 6. 返回二进制流
                        ↓
7. 前端接收 Blob → 8. 触发浏览器下载
```

## 🚀 使用说明

### 后端启动
```bash
# 确保已安装依赖
pip install openpyxl

# 启动服务
python -m uvicorn app.main:app --reload
```

### 前端启动
```bash
cd web-admin

# 安装依赖（如果还没安装）
npm install

# 启动开发服务器
npm run dev
```

### 访问报表功能
1. 登录系统（需要 super_admin, event_admin 或 reviewer 角色）
2. 点击侧边栏"报表中心"菜单
3. 选择相应的报表页面
4. 使用筛选器和排序功能
5. 点击"导出 Excel"按钮下载报表

## 🔐 权限要求

所有报表功能需要以下角色之一：
- `super_admin`: 超级管理员
- `event_admin`: 活动管理员
- `reviewer`: 审核员

## 📝 注意事项

### 1. 性能优化
- 交易流水导出限制为最多 10000 条记录
- 大数据量查询使用索引优化
- 前端表格支持分页和虚拟滚动

### 2. 数据准确性
- 所有金额单位统一为"分"存储，"元"展示
- 利润计算依赖商品成本价，未设置成本价的商品利润为 0
- 净消费额 = 总消费 - 总退款

### 3. 异常检测规则
- 高频退款：1小时内同一操作员退款 > 5次
- 大额更正：adjust 类型且金额 > 1000元
- 可疑操作：22:00-06:00 时段的交易

### 4. Excel 导出
- 需要安装 `openpyxl` 库
- 文件名自动包含活动名和日期
- 支持中文文件名

## 🎉 总结

本次升级成功实现了完整的报表、排行榜、经营分析和导出功能，为系统提供了强大的数据分析能力。所有功能均基于账本流水设计，确保数据准确性和可审计性。前后端代码结构清晰，易于维护和扩展。

### 主要成果
- ✅ 8 个后端 API 接口
- ✅ 6 个前端页面组件
- ✅ 完整的数据统计逻辑
- ✅ Excel 导出功能
- ✅ 异常检测机制
- ✅ 权限控制
- ✅ 响应式设计

### 技术亮点
- 基于账本流水的准确统计
- 多维度数据分析
- 实时异常检测
- 灵活的筛选和排序
- 优雅的 UI 设计
- 完善的错误处理

系统现已具备完整的经营分析能力，可以帮助管理员全面了解活动运营情况，及时发现异常，做出数据驱动的决策。
