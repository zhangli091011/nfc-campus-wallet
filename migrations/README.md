# 数据库迁移文件说明

## 文件列表

### 完整初始化脚本（推荐用于新安装）

- **`complete_database_init.sql`** - 完整数据库初始化脚本
  - 包含所有表结构、索引、视图、存储过程
  - 适用于全新安装
  - 已整合所有迁移功能

### 原始迁移文件（用于理解演进历史）

1. **`init_database_mysql.sql`** - 基础数据库结构
   - Events（活动表）
   - Participants（参与者表）
   - Accounts（账户表）
   - Booths（摊位表）
   - Products（商品表）
   - Users（用户表）
   - Transactions（交易表）

2. **`001_upgrade_to_ledger_mode.sql`** - 升级到账本追加模式
   - 扩展交易表字段（balance_before, related_txn_id, remark等）
   - 金额单位从元改为分
   - 添加交易类型验证

3. **`002_upgrade_to_event_system.sql`** - 升级到活动额度系统
   - 创建活动表（events）
   - 创建参与者表（participants）
   - 创建账户表（accounts）
   - 添加活动关联

4. **`003_booth_management_system.sql`** - 摊位经营系统
   - 创建摊位表（booths）
   - 创建商品表（products）
   - 创建用户表（users）
   - 添加摊位和商品关联
   - 创建统计视图

5. **`004_booth_collection_accounts.sql`** - 摊位收款账户
   - 添加participant_type字段
   - 添加collection_participant_id字段
   - 支持摊位收款账户功能

6. **`005_add_missing_columns.sql`** - 添加缺失字段
   - 检查并添加participant_type
   - 检查并添加collection_participant_id
   - 兼容性修复

## 使用方法

### 方法一：全新安装（推荐）

```bash
# 1. 创建数据库
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS nfc_wallet CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 2. 执行完整初始化脚本
mysql -u root -p nfc_wallet < migrations/complete_database_init.sql
```

### 方法二：使用初始化脚本

```bash
# 使用项目提供的初始化脚本
bash init_database.sh
```

### 方法三：逐步迁移（用于现有数据库升级）

```bash
# 按顺序执行迁移文件
mysql -u root -p nfc_wallet < migrations/init_database_mysql.sql
mysql -u root -p nfc_wallet < migrations/001_upgrade_to_ledger_mode.sql
mysql -u root -p nfc_wallet < migrations/002_upgrade_to_event_system.sql
mysql -u root -p nfc_wallet < migrations/003_booth_management_system.sql
mysql -u root -p nfc_wallet < migrations/004_booth_collection_accounts.sql
mysql -u root -p nfc_wallet < migrations/005_add_missing_columns.sql
```

## 数据库结构概览

### 核心表

| 表名 | 说明 | 主要字段 |
|------|------|----------|
| events | 活动表 | id, name, start_date, end_date, status |
| participants | 参与者表 | id, name, card_uid, participant_type |
| accounts | 账户表 | id, participant_id, event_id, balance |
| booths | 摊位表 | id, event_id, name, collection_participant_id |
| products | 商品表 | id, booth_id, name, price, stock |
| users | 用户表 | id, username, password_hash, role, booth_id |
| transactions | 交易表 | id, type, amount, balance_before, balance_after |

### 统计视图

| 视图名 | 说明 |
|--------|------|
| booth_transaction_stats | 摊位交易统计 |
| product_sales_stats | 商品销售统计 |
| account_details_view | 账户详情视图 |

### 存储过程

| 存储过程名 | 说明 | 参数 |
|-----------|------|------|
| sp_get_or_create_account | 获取或创建账户 | IN: participant_id, event_id; OUT: account_id, balance |
| sp_get_booth_revenue | 获取摊位收入统计 | IN: booth_id, start_date, end_date; OUT: total_sales, total_refunds, net_revenue, transaction_count |

## 默认账户

初始化后会自动创建一个超级管理员账户：

- **用户名**: `admin`
- **密码**: `admin123`
- **角色**: `super_admin`

⚠️ **重要**: 首次登录后请立即修改默认密码！

## 数据类型说明

### 金额单位
所有金额字段使用 **分（cent）** 作为单位，存储为 `INT` 类型：
- `balance`: 账户余额（分）
- `amount`: 交易金额（分）
- `price`: 商品价格（分）
- `cost_price`: 成本价（分）

例如：100元 = 10000分

### 交易类型
- `pay`: 支付
- `recharge`: 充值
- `refund`: 退款

### 用户角色
- `super_admin`: 超级管理员
- `event_admin`: 活动管理员
- `booth_cashier`: 摊位收银员
- `issuer`: 发卡员
- `reviewer`: 审核员

### 参与者类型
- `person`: 普通参与者
- `booth_collection`: 摊位收款账户

### 状态类型
- `active`: 活跃
- `inactive`: 未激活
- `blocked`: 已封禁
- `closed`: 已关闭

## 索引优化

数据库已创建以下索引以优化查询性能：

### 单列索引
- 所有外键字段
- 常用查询字段（status, card_uid等）

### 复合索引
- `idx_accounts_participant_event`: (participant_id, event_id)
- `idx_transactions_booth_created`: (booth_id, created_at)
- `idx_transactions_event_participant`: (event_id, participant_id)
- `idx_users_role_status`: (role, status)

## 数据完整性约束

### 外键约束
- 所有关联表都设置了外键约束
- 删除策略：CASCADE 或 SET NULL

### 检查约束
- 余额非负检查
- 金额正数检查
- 状态枚举检查
- 日期逻辑检查

### 唯一约束
- 参与者卡片UID唯一
- 用户名唯一
- 账户（参与者+活动）唯一

## 备份建议

在执行任何数据库操作前，建议先备份：

```bash
# 备份整个数据库
mysqldump -u root -p nfc_wallet > backup_$(date +%Y%m%d_%H%M%S).sql

# 仅备份结构
mysqldump -u root -p --no-data nfc_wallet > schema_backup.sql

# 仅备份数据
mysqldump -u root -p --no-create-info nfc_wallet > data_backup.sql
```

## 故障排除

### 问题1：字符集错误
```sql
ALTER DATABASE nfc_wallet CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 问题2：外键约束失败
检查是否按顺序创建表，确保被引用的表先创建。

### 问题3：权限不足
```sql
GRANT ALL PRIVILEGES ON nfc_wallet.* TO 'your_user'@'localhost';
FLUSH PRIVILEGES;
```

## 版本历史

- **v1.0** (2026-05-09): 完整数据库结构，整合所有迁移
- **v0.6** (2026-05-01): 添加缺失字段修复
- **v0.5** (2026-05-01): 摊位收款账户功能
- **v0.4** (2026-05-01): 摊位经营系统
- **v0.3** (2026-05-01): 活动额度系统
- **v0.2** (2026-05-01): 账本追加模式
- **v0.1** (2026-05-01): 基础数据库结构

## 技术支持

如有问题，请查看：
- 项目README.md
- API文档：docs/API_DOCUMENTATION.md
- 认证授权文档：docs/AUTHENTICATION_AUTHORIZATION.md
