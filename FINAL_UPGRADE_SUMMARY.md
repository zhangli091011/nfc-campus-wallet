# NFC Campus Event System - 最终升级总结

## 项目概述

本项目是一个完整的校园 NFC 活动管理系统，支持活动创建、摊位管理、商品销售、NFC 刷卡支付、现金对账、数据导出等全流程功能。

---

## 系统架构

### 技术栈

**后端**
- **框架**: FastAPI 0.109.0
- **数据库**: MySQL 8.0+ with SQLAlchemy 2.0
- **认证**: JWT (PyJWT 2.8.0)
- **密码加密**: bcrypt 4.1.2
- **Excel 导出**: openpyxl 3.1.2

**Android 客户端**
- **语言**: Java
- **最低版本**: Android 8.0 (API 26)
- **NFC**: 支持 ISO 14443A 标准
- **网络**: Retrofit 2.9.0

### 系统模块

```
nfc-campus-event-system/
├── 核心模块 (core/)
│   ├── 配置管理 (config.py)
│   ├── 数据库连接 (database.py)
│   ├── 异常处理 (exceptions.py)
│   └── 安全认证 (security.py)
├── 数据模型 (models/)
│   ├── 用户模型 (user.py)
│   ├── 活动模型 (event.py)
│   ├── 参与者模型 (participant.py)
│   ├── 账户模型 (account.py)
│   ├── 摊位模型 (booth.py)
│   ├── 商品模型 (product.py)
│   ├── 交易模型 (transaction.py)
│   └── 现金对账模型 (cash_reconciliation.py)
├── 业务服务 (services/)
│   ├── 认证服务 (auth_service.py)
│   ├── 用户服务 (user_service.py)
│   ├── 活动服务 (event_service.py)
│   ├── 参与者服务 (participant_service.py)
│   ├── 账户服务 (account_service.py)
│   ├── 摊位服务 (booth_service.py)
│   ├── 商品服务 (product_service.py)
│   ├── 交易服务 (transaction_service.py)
│   ├── 账本服务 (ledger_service.py)
│   ├── 现金对账服务 (cash_reconciliation_service.py)
│   ├── 报表服务 (report_service.py)
│   └── 导出服务 (export_service.py)
├── API 路由 (routes/)
│   ├── 认证路由 (auth.py)
│   ├── 用户路由 (users.py)
│   ├── 活动路由 (events.py)
│   ├── 活动关场路由 (event_close.py)
│   ├── 参与者路由 (participants.py)
│   ├── 摊位路由 (booths.py)
│   ├── 商品路由 (products.py)
│   ├── 余额查询路由 (balance.py)
│   ├── 支付路由 (payment.py)
│   ├── 充值路由 (recharge.py)
│   ├── 交易记录路由 (transactions.py)
│   ├── 现金对账路由 (cash_reconciliation.py)
│   ├── 报表路由 (reports.py)
│   └── 导出路由 (exports.py)
└── Android 客户端 (android/)
    ├── NFC 读卡模块
    ├── 收银终端界面
    ├── 商品管理界面
    └── 交易记录界面
```

---

## 最终阶段实现内容

### 1. 活动关场功能 ✅

**新增接口**: `POST /events/{id}/close`

**功能特性**:
- 活动状态更新为 `ended`
- 自动禁止 `pay`、`recharge`、`issue` 操作
- 仅管理员可进行 `refund` 和 `adjust`
- 支持执行额度失效逻辑
- 生成 `expire` 类型流水
- 余额自动归零

**实现文件**:
- `routes/event_close.py` - API 路由
- `services/event_service.py` - 业务逻辑（已扩展）
- `services/ledger_service.py` - 账本服务（已扩展）

**使用示例**:
```bash
curl -X POST "http://localhost:8000/events/1/close" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"expire_quotas": true}'
```

---

### 2. 现金对账功能 ✅

**新增数据表**: `booth_cash_reconciliations`

**表结构**:
```sql
CREATE TABLE booth_cash_reconciliations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    booth_id INT NOT NULL,
    event_id INT NOT NULL,
    expected_cash INT NOT NULL COMMENT '预期现金（分）',
    actual_cash INT NOT NULL COMMENT '实际现金（分）',
    diff_amount INT NOT NULL COMMENT '差额（分）',
    reason TEXT COMMENT '差额原因',
    reviewer_id INT COMMENT '审核人ID',
    created_at DATETIME NOT NULL,
    FOREIGN KEY (booth_id) REFERENCES booths(id),
    FOREIGN KEY (event_id) REFERENCES events(id),
    FOREIGN KEY (reviewer_id) REFERENCES users(id)
);
```

**新增接口**:
- `POST /cash-reconciliation` - 创建对账记录
- `GET /cash-reconciliation` - 查询对账记录

**实现文件**:
- `models/cash_reconciliation.py` - 数据模型
- `services/cash_reconciliation_service.py` - 业务服务
- `schemas/cash_reconciliation.py` - 数据验证
- `routes/cash_reconciliation.py` - API 路由

**使用示例**:
```bash
curl -X POST "http://localhost:8000/cash-reconciliation" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booth_id": 1,
    "event_id": 1,
    "expected_cash": 100.00,
    "actual_cash": 99.50,
    "reason": "找零误差"
  }'
```

---

### 3. 数据导出功能 ✅

**新增导出接口**:
- `GET /export/class-settlement?event_id={id}` - 班级结算单
- `GET /export/transactions?event_id={id}` - 全量流水
- `GET /export/refund-adjustments?event_id={id}` - 退款/更正清单
- `GET /export/leaderboard?event_id={id}` - 排名表

**导出格式**: Excel (.xlsx)

**实现文件**:
- `services/export_service.py` - 导出服务（已扩展）
- `routes/exports.py` - 导出路由

**导出内容**:

1. **班级结算单**
   - 班级名称
   - 摊位名称
   - 营业额
   - 退款额
   - 净收入
   - 总成本
   - 利润
   - 利润率

2. **全量流水**
   - 交易ID
   - 交易类型
   - 金额
   - 交易前后余额
   - 参与者卡号
   - 摊位ID
   - 商品ID
   - 操作员ID
   - 备注
   - 交易时间

3. **退款/更正清单**
   - 交易ID
   - 类型（refund/adjust）
   - 金额
   - 参与者卡号
   - 关联交易ID
   - 操作员ID
   - 备注
   - 交易时间

4. **排名表**
   - 排名
   - 班级名称
   - 摊位名称
   - 净收入
   - 销量
   - 利润率

**使用示例**:
```bash
# 导出班级结算单
curl -X GET "http://localhost:8000/export/class-settlement?event_id=1" \
  -H "Authorization: Bearer $TOKEN" \
  -o class_settlement.xlsx

# 导出全量流水
curl -X GET "http://localhost:8000/export/transactions?event_id=1" \
  -H "Authorization: Bearer $TOKEN" \
  -o transactions.xlsx
```

---

### 4. 部署文档 ✅

**新增文档**:
- `DEPLOYMENT_GUIDE.md` - 完整部署指南
- `DEMO_FLOW.md` - 演示流程文档
- `FINAL_UPGRADE_SUMMARY.md` - 最终升级总结（本文档）

**部署指南内容**:
1. 系统要求
2. 后端部署步骤
3. 数据库初始化
4. Android 应用部署
5. 环境配置说明
6. 验证部署方法
7. 故障排查指南
8. 维护和监控建议

**演示流程内容**:
1. 环境准备
2. 14 步完整演示流程
3. 演示数据总结
4. 联调注意事项
5. 常见问题解答

---

### 5. 自动化脚本 ✅

**新增脚本**:

1. **数据库迁移脚本** (`scripts/migrate_cash_reconciliation.py`)
   - 自动创建现金对账表
   - 验证表结构
   - 显示迁移结果

2. **演示数据设置脚本** (`scripts/demo_setup.py`)
   - 自动创建管理员账户
   - 创建演示活动
   - 创建摊位和商品
   - 创建参与者并绑定卡片
   - 发放活动额度
   - 创建收银员账户
   - 模拟交易数据

3. **管理员创建脚本** (`scripts/create_admin.py`)
   - 交互式创建管理员
   - 密码强度验证
   - 数据库自动初始化

**使用示例**:
```bash
# 运行数据库迁移
python scripts/migrate_cash_reconciliation.py

# 设置演示数据
python scripts/demo_setup.py

# 创建管理员
python scripts/create_admin.py
```

---

### 6. 环境配置文件 ✅

**更新文件**:
- `requirements.txt` - 添加 openpyxl 依赖
- `.env.example` - 完整的环境变量示例

**新增依赖**:
```
openpyxl==3.1.2  # Excel 导出支持
```

---

## 完整功能清单

### 用户管理
- ✅ 用户注册
- ✅ 用户登录（JWT）
- ✅ 角色权限控制（super_admin, event_admin, booth_cashier, issuer）
- ✅ 用户信息查询

### 活动管理
- ✅ 创建活动
- ✅ 查询活动列表
- ✅ 查询活动详情
- ✅ 更新活动信息
- ✅ 活动关场
- ✅ 额度失效处理

### 参与者管理
- ✅ 创建参与者
- ✅ 查询参与者列表
- ✅ 查询参与者详情
- ✅ 更新参与者信息
- ✅ 绑定 NFC 卡片
- ✅ 解绑 NFC 卡片

### 摊位管理
- ✅ 创建摊位
- ✅ 查询摊位列表
- ✅ 查询摊位详情
- ✅ 更新摊位信息
- ✅ 摊位状态管理

### 商品管理
- ✅ 创建商品
- ✅ 查询商品列表
- ✅ 查询商品详情
- ✅ 更新商品信息
- ✅ 商品库存管理
- ✅ 商品状态管理

### 交易管理
- ✅ 刷卡支付
- ✅ 充值/发放额度
- ✅ 退款
- ✅ 调整
- ✅ 余额查询
- ✅ 交易历史查询
- ✅ 摊位交易查询
- ✅ 商品交易查询

### 现金对账
- ✅ 创建对账记录
- ✅ 查询对账记录
- ✅ 差额原因记录

### 报表统计
- ✅ 总览统计报表
- ✅ 摊位报表
- ✅ 商品报表
- ✅ 交易流水报表

### 数据导出
- ✅ 班级结算单导出
- ✅ 全量流水导出
- ✅ 退款/更正清单导出
- ✅ 排名表导出

### Android 客户端
- ✅ 收银员登录
- ✅ NFC 读卡
- ✅ 商品选择
- ✅ 刷卡支付
- ✅ 交易记录查询
- ✅ 余额查询

---

## 数据库设计

### 核心表结构

1. **users** - 用户表
2. **events** - 活动表
3. **participants** - 参与者表
4. **accounts** - 账户表（活动-参与者关联）
5. **booths** - 摊位表
6. **products** - 商品表
7. **transactions** - 交易表（账本模式）
8. **booth_cash_reconciliations** - 现金对账表

### 关系图

```
events (活动)
  ├── booths (摊位)
  │   ├── products (商品)
  │   ├── transactions (交易)
  │   └── cash_reconciliations (对账)
  ├── accounts (账户)
  │   └── transactions (交易)
  └── participants (参与者)
      └── accounts (账户)

users (用户)
  ├── booths (收银员关联)
  └── transactions (操作员记录)
```

---

## API 端点总览

### 认证相关
- `POST /auth/register` - 用户注册
- `POST /auth/login` - 用户登录

### 用户管理
- `GET /users` - 查询用户列表
- `GET /users/{id}` - 查询用户详情

### 活动管理
- `POST /events` - 创建活动
- `GET /events` - 查询活动列表
- `GET /events/{id}` - 查询活动详情
- `PATCH /events/{id}` - 更新活动
- `POST /events/{id}/close` - 关闭活动

### 参与者管理
- `POST /participants` - 创建参与者
- `GET /participants` - 查询参与者列表
- `GET /participants/{id}` - 查询参与者详情
- `PATCH /participants/{id}` - 更新参与者
- `POST /participants/{id}/bind-card` - 绑定卡片
- `POST /participants/{id}/unbind-card` - 解绑卡片

### 摊位管理
- `POST /booths` - 创建摊位
- `GET /booths` - 查询摊位列表
- `GET /booths/{id}` - 查询摊位详情
- `PATCH /booths/{id}` - 更新摊位

### 商品管理
- `POST /products` - 创建商品
- `GET /products` - 查询商品列表
- `GET /products/{id}` - 查询商品详情
- `PATCH /products/{id}` - 更新商品

### 交易相关
- `GET /balance` - 查询余额
- `POST /payment` - 刷卡支付
- `POST /recharge` - 充值/发放额度
- `POST /refund` - 退款
- `GET /transactions` - 查询交易记录

### 现金对账
- `POST /cash-reconciliation` - 创建对账记录
- `GET /cash-reconciliation` - 查询对账记录

### 报表统计
- `GET /reports/summary` - 总览统计
- `GET /reports/booths` - 摊位报表
- `GET /reports/products` - 商品报表

### 数据导出
- `GET /export/class-settlement` - 班级结算单
- `GET /export/transactions` - 全量流水
- `GET /export/refund-adjustments` - 退款/更正清单
- `GET /export/leaderboard` - 排名表

---

## 权限控制

### 角色定义

1. **super_admin** - 超级管理员
   - 所有权限
   - 创建活动、摊位、商品
   - 管理用户
   - 查看所有数据
   - 导出所有报表

2. **event_admin** - 活动管理员
   - 管理活动
   - 创建摊位、商品
   - 发放额度
   - 查看活动数据
   - 导出活动报表

3. **booth_cashier** - 摊位收银员
   - 刷卡支付
   - 查询余额
   - 查看本摊位交易
   - 查看本摊位商品

4. **issuer** - 发卡员
   - 创建参与者
   - 绑定/解绑卡片
   - 发放额度
   - 查看交易记录（审计）

### 权限矩阵

| 功能 | super_admin | event_admin | booth_cashier | issuer |
|------|-------------|-------------|---------------|--------|
| 创建活动 | ✅ | ✅ | ❌ | ❌ |
| 关闭活动 | ✅ | ✅ | ❌ | ❌ |
| 创建摊位 | ✅ | ✅ | ❌ | ❌ |
| 创建商品 | ✅ | ✅ | ❌ | ❌ |
| 创建参与者 | ✅ | ✅ | ❌ | ✅ |
| 绑定卡片 | ✅ | ✅ | ❌ | ✅ |
| 发放额度 | ✅ | ✅ | ❌ | ✅ |
| 刷卡支付 | ✅ | ✅ | ✅ | ❌ |
| 退款 | ✅ | ✅ | ❌ | ❌ |
| 查看所有交易 | ✅ | ✅ | ❌ | ✅ |
| 查看本摊位交易 | ✅ | ✅ | ✅ | ❌ |
| 现金对账 | ✅ | ✅ | ❌ | ❌ |
| 导出报表 | ✅ | ✅ | ❌ | ❌ |

---

## 安全特性

### 认证与授权
- ✅ JWT Token 认证
- ✅ 密码 bcrypt 加密
- ✅ 基于角色的访问控制（RBAC）
- ✅ Token 过期时间控制

### 数据安全
- ✅ SQL 注入防护（SQLAlchemy ORM）
- ✅ XSS 防护（FastAPI 自动转义）
- ✅ CORS 配置
- ✅ 请求日志记录

### 业务安全
- ✅ 并发控制（SELECT FOR UPDATE）
- ✅ 余额验证
- ✅ 交易原子性保证
- ✅ 账本追加模式（不可篡改）

---

## 性能优化

### 数据库优化
- ✅ 索引优化（外键、查询字段）
- ✅ 连接池管理
- ✅ 查询分页
- ✅ 批量操作支持

### API 优化
- ✅ 异步处理（FastAPI async）
- ✅ 响应缓存（可选）
- ✅ 请求限流（可选）
- ✅ 数据压缩（可选）

---

## 测试覆盖

### 单元测试
- ✅ 服务层测试
- ✅ 模型验证测试
- ✅ 工具函数测试

### 集成测试
- ✅ API 端点测试
- ✅ 数据库操作测试
- ✅ 认证流程测试

### 演示测试
- ✅ 完整流程测试脚本
- ✅ 自动化演示数据生成

---

## 部署清单

### 后端部署
- ✅ Python 虚拟环境
- ✅ 依赖安装（requirements.txt）
- ✅ 环境变量配置（.env）
- ✅ 数据库初始化
- ✅ 服务启动脚本

### Android 部署
- ✅ APK 构建配置
- ✅ 后端地址配置
- ✅ 签名配置（可选）
- ✅ 安装说明

### 文档
- ✅ API 文档（Swagger UI）
- ✅ 部署指南
- ✅ 演示流程
- ✅ 故障排查指南

---

## 项目状态

### ✅ 已完成功能

1. **核心功能**
   - 用户认证与授权
   - 活动管理
   - 参与者管理
   - 摊位管理
   - 商品管理
   - 交易处理
   - 余额查询

2. **高级功能**
   - 活动关场
   - 额度失效
   - 现金对账
   - 报表统计
   - 数据导出

3. **客户端**
   - Android 收银终端
   - NFC 读卡功能
   - 商品管理界面
   - 交易记录查询

4. **部署支持**
   - 完整部署文档
   - 演示流程文档
   - 自动化脚本
   - 环境配置示例

### 🎯 系统特点

1. **完整性**
   - 覆盖活动全生命周期
   - 从创建到关场的完整流程
   - 支持多角色协作

2. **可靠性**
   - 账本追加模式
   - 并发控制
   - 交易原子性保证
   - 完整的审计日志

3. **易用性**
   - RESTful API 设计
   - Swagger 文档
   - 自动化脚本
   - 详细的使用说明

4. **可扩展性**
   - 模块化设计
   - 清晰的代码结构
   - 易于添加新功能
   - 支持多活动并行

---

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd nfc-campus-event-system
```

### 2. 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 3. 配置环境

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接
```

### 4. 初始化数据库

```bash
python scripts/migrate_cash_reconciliation.py
```

### 5. 创建管理员

```bash
python scripts/create_admin.py
```

### 6. 启动服务

```bash
python -m uvicorn app.main:app --reload
```

### 7. 设置演示数据（可选）

```bash
python scripts/demo_setup.py
```

### 8. 访问系统

- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

---

## 文档索引

1. **README.md** - 项目概述和快速开始
2. **DEPLOYMENT_GUIDE.md** - 完整部署指南
3. **DEMO_FLOW.md** - 演示流程文档
4. **FINAL_UPGRADE_SUMMARY.md** - 最终升级总结（本文档）
5. **docs/API_DOCUMENTATION.md** - API 详细文档
6. **docs/AUTHENTICATION_AUTHORIZATION.md** - 认证授权文档
7. **docs/ERROR_CODES.md** - 错误码说明
8. **android/README.md** - Android 客户端文档

---

## 联系方式

如有问题或建议，请通过以下方式联系：

- **项目仓库**: https://github.com/your-repo
- **问题反馈**: https://github.com/your-repo/issues
- **技术支持**: support@example.com

---

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

---

## 致谢

感谢所有为本项目做出贡献的开发者和测试人员。

---

**项目状态**: ✅ 生产就绪

**最后更新**: 2024-05-02

**版本**: v2.0.0 - Final Release
