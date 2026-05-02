# NFC 校园钱包管理后台

基于 React + Vite + TypeScript + Ant Design 的 Web 管理后台系统。

## 功能特性

### 1. 用户认证
- JWT Token 认证
- 登录态管理
- 路由守卫
- 自动登录过期处理

### 2. 核心功能模块

#### 数据看板
- 活动统计概览
- 摊位、参与者、交易数据统计
- 最近交易记录

#### 活动管理
- 创建、编辑、删除活动
- 活动状态管理（待开始、进行中、已结束、已取消）
- 活动时间设置

#### 摊位管理
- 创建、编辑、删除摊位
- 摊位状态管理（营业中、未营业、已关闭）
- 按活动筛选摊位

#### 商品管理
- 创建、编辑、删除商品
- 商品价格、库存管理
- 商品启用/禁用
- 按摊位筛选商品

#### 参与者管理
- 创建、编辑参与者
- NFC 卡绑定
- 参与者状态管理
- 余额充值功能

#### 交易流水
- 交易记录查询
- 多维度筛选（活动、摊位、类型、时间）
- 分页展示
- 交易详情查看

#### 退款审批
- 支付交易列表
- 退款申请处理
- 退款原因记录

#### 用户管理（超级管理员）
- 创建用户账号
- 角色分配（超级管理员、活动管理员、摊位收银员、充值员、审核员）
- 用户状态管理（激活、禁用、冻结）
- 摊位收银员绑定摊位

## 技术栈

- **框架**: React 18
- **构建工具**: Vite 5
- **语言**: TypeScript
- **UI 组件库**: Ant Design 5
- **路由**: React Router 6
- **HTTP 客户端**: Axios
- **日期处理**: Day.js
- **图表**: Recharts

## 项目结构

```
web-admin/
├── public/                 # 静态资源
├── src/
│   ├── components/        # 公共组件
│   │   └── Layout/       # 布局组件
│   ├── pages/            # 页面组件
│   │   ├── Login/        # 登录页
│   │   ├── Dashboard/    # 数据看板
│   │   ├── EventManagement/      # 活动管理
│   │   ├── BoothManagement/      # 摊位管理
│   │   ├── ProductManagement/    # 商品管理
│   │   ├── ParticipantManagement/ # 参与者管理
│   │   ├── TransactionHistory/   # 交易流水
│   │   ├── RefundApproval/       # 退款审批
│   │   └── UserManagement/       # 用户管理
│   ├── services/         # API 服务层
│   │   ├── auth.ts       # 认证服务
│   │   ├── event.ts      # 活动服务
│   │   ├── booth.ts      # 摊位服务
│   │   ├── product.ts    # 商品服务
│   │   ├── participant.ts # 参与者服务
│   │   ├── transaction.ts # 交易服务
│   │   └── user.ts       # 用户服务
│   ├── routes/           # 路由配置
│   ├── utils/            # 工具函数
│   │   ├── auth.ts       # 认证工具
│   │   └── request.ts    # HTTP 请求封装
│   ├── App.tsx           # 应用入口
│   ├── main.tsx          # 主入口
│   └── index.css         # 全局样式
├── index.html            # HTML 模板
├── package.json          # 依赖配置
├── tsconfig.json         # TypeScript 配置
├── vite.config.ts        # Vite 配置
└── README.md             # 项目说明

```

## 快速开始

### 1. 安装依赖

```bash
cd web-admin
npm install
```

### 2. 配置后端 API

后端 API 地址已在 `vite.config.ts` 中配置代理：

```typescript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',  // 后端 API 地址
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),
    },
  },
}
```

如需修改后端地址，请编辑 `vite.config.ts` 文件。

### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 4. 默认登录账号

使用后端创建的管理员账号登录，例如：

- 用户名: `admin`
- 密码: `your_password`

### 5. 构建生产版本

```bash
npm run build
```

构建产物在 `dist` 目录。

### 6. 预览生产版本

```bash
npm run preview
```

## API 接口说明

所有 API 请求通过 `/api` 前缀代理到后端服务器。

### 认证相关
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

### 活动管理
- `GET /api/events` - 获取活动列表
- `POST /api/events` - 创建活动
- `PATCH /api/events/:id` - 更新活动
- `DELETE /api/events/:id` - 删除活动

### 摊位管理
- `GET /api/booths` - 获取摊位列表
- `POST /api/booths` - 创建摊位
- `PATCH /api/booths/:id` - 更新摊位
- `DELETE /api/booths/:id` - 删除摊位

### 商品管理
- `GET /api/products` - 获取商品列表
- `POST /api/products` - 创建商品
- `PATCH /api/products/:id` - 更新商品
- `DELETE /api/products/:id` - 删除商品

### 参与者管理
- `GET /api/participants` - 获取参与者列表
- `POST /api/participants` - 创建参与者
- `PATCH /api/participants/:id` - 更新参与者
- `POST /api/recharge` - 充值

### 交易管理
- `GET /api/transactions` - 获取交易列表
- `POST /api/refund` - 退款

### 用户管理
- `GET /api/users` - 获取用户列表
- `POST /api/users` - 创建用户
- `PATCH /api/users/:id/status` - 更新用户状态

详细 API 文档请参考后端项目的 `docs/API_DOCUMENTATION.md`。

## 权限说明

### 角色权限

1. **超级管理员 (super_admin)**
   - 所有功能权限
   - 用户管理

2. **活动管理员 (event_admin)**
   - 活动、摊位、商品管理
   - 参与者管理
   - 交易查询
   - 退款审批

3. **摊位收银员 (booth_cashier)**
   - 仅能查看和操作分配的摊位
   - 商品查看
   - 交易处理

4. **充值员 (issuer)**
   - 参与者充值
   - 交易查询

5. **审核员 (reviewer)**
   - 交易查询
   - 退款审批

### 路由守卫

- 未登录用户访问受保护路由会自动跳转到登录页
- Token 过期会自动清除登录信息并跳转到登录页
- 用户管理页面仅超级管理员可访问

## 开发说明

### 添加新页面

1. 在 `src/pages/` 创建页面组件
2. 在 `src/routes/index.tsx` 添加路由配置
3. 在 `src/components/Layout/index.tsx` 添加菜单项

### 添加新 API

1. 在 `src/services/` 创建或编辑服务文件
2. 定义 TypeScript 接口
3. 使用 `request` 工具发起请求

### 错误处理

所有 API 错误已在 `src/utils/request.ts` 的响应拦截器中统一处理：

- 401: 自动跳转登录页
- 403: 显示权限不足提示
- 404: 显示资源不存在提示
- 400/500: 显示错误信息

## 常见问题

### 1. 登录后立即跳转回登录页

检查后端 API 是否正常运行，JWT Token 是否正确返回。

### 2. API 请求失败

- 检查后端服务是否启动（默认 http://localhost:8000）
- 检查 `vite.config.ts` 中的代理配置
- 查看浏览器控制台网络请求

### 3. 页面空白

- 检查浏览器控制台是否有错误
- 确认 Node.js 版本 >= 16
- 尝试删除 `node_modules` 重新安装依赖

### 4. 构建失败

- 检查 TypeScript 类型错误
- 运行 `npm run lint` 检查代码规范

## 后续优化建议

1. **性能优化**
   - 添加 React.memo 优化组件渲染
   - 使用虚拟滚动处理大数据列表
   - 添加请求缓存

2. **功能增强**
   - 添加数据导出功能（Excel）
   - 添加图表可视化
   - 添加实时数据推送
   - 添加批量操作

3. **用户体验**
   - 添加加载骨架屏
   - 添加操作确认提示
   - 优化移动端适配
   - 添加快捷键支持

4. **安全性**
   - 添加 CSRF 防护
   - 添加请求签名
   - 添加操作日志

## 许可证

MIT

## 联系方式

如有问题，请联系项目维护者。
