-- ============================================
-- Migration 011: 合并投资币账户 + 金额单位改为元
-- 
-- 核心变更：
-- 1. 去除独立的 stock_accounts 表，股票购买直接从 accounts.balance 扣款
-- 2. 所有金额字段从 INT（分）改为 DECIMAL(12,2)（元）
-- 3. 去除 account_transfers 表（不再需要双账户互转）
-- 4. stock_orders 表去除 stock_account_id 外键
-- ============================================

-- ── 1. 转换 accounts 表金额为元 ──
ALTER TABLE accounts
    MODIFY COLUMN balance DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '账户余额（元）',
    MODIFY COLUMN credit_borrowed DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '名义借款总额（元）',
    MODIFY COLUMN credit_fee_paid DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '已支付手续费总额（元）';

-- 将现有数据从分转换为元
UPDATE accounts SET 
    balance = balance / 100,
    credit_borrowed = credit_borrowed / 100,
    credit_fee_paid = credit_fee_paid / 100;

-- ── 2. 转换 transactions 表金额为元 ──
ALTER TABLE transactions
    MODIFY COLUMN amount DECIMAL(12,2) NOT NULL COMMENT '金额（元）',
    MODIFY COLUMN balance_before DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '交易前余额（元）',
    MODIFY COLUMN balance_after DECIMAL(12,2) NOT NULL COMMENT '交易后余额（元）';

UPDATE transactions SET
    amount = amount / 100,
    balance_before = balance_before / 100,
    balance_after = balance_after / 100;

-- ── 3. 转换 stocks 表金额为元 ──
ALTER TABLE stocks
    MODIFY COLUMN initial_price DECIMAL(12,2) NOT NULL DEFAULT 10.00 COMMENT '初始发行价（元）';

UPDATE stocks SET initial_price = initial_price / 100;

-- ── 4. 转换 stock_orders 表 ──
-- 先去除 stock_account_id 外键约束
ALTER TABLE stock_orders
    DROP FOREIGN KEY stock_orders_ibfk_3;

ALTER TABLE stock_orders
    DROP COLUMN stock_account_id,
    MODIFY COLUMN buy_price DECIMAL(12,2) NOT NULL COMMENT '购买单价（元）',
    MODIFY COLUMN total_amount DECIMAL(12,2) NOT NULL COMMENT '购买总金额（元）',
    MODIFY COLUMN settlement_price DECIMAL(12,2) NULL COMMENT '结算单价（元）',
    MODIFY COLUMN settlement_amount DECIMAL(12,2) NULL COMMENT '结算总金额（元）',
    ADD COLUMN account_id INT NULL COMMENT '关联的活动账户ID' AFTER participant_id;

UPDATE stock_orders SET
    buy_price = buy_price / 100,
    total_amount = total_amount / 100,
    settlement_price = settlement_price / 100,
    settlement_amount = settlement_amount / 100;

-- 回填 account_id
UPDATE stock_orders so
    JOIN accounts a ON a.participant_id = so.participant_id AND a.event_id = so.event_id
    SET so.account_id = a.id;

-- ── 5. 转换 stock_purchases 表（如果存在）──
ALTER TABLE stock_purchases
    MODIFY COLUMN purchase_price DECIMAL(12,2) NOT NULL COMMENT '购买单价（元）',
    MODIFY COLUMN total_amount DECIMAL(12,2) NOT NULL COMMENT '购买总金额（元）',
    MODIFY COLUMN settlement_price DECIMAL(12,2) NULL COMMENT '结算单价（元）',
    MODIFY COLUMN settlement_amount DECIMAL(12,2) NULL COMMENT '结算总金额（元）';

UPDATE stock_purchases SET
    purchase_price = purchase_price / 100,
    total_amount = total_amount / 100,
    settlement_price = CASE WHEN settlement_price IS NOT NULL THEN settlement_price / 100 ELSE NULL END,
    settlement_amount = CASE WHEN settlement_amount IS NOT NULL THEN settlement_amount / 100 ELSE NULL END;

-- ── 6. 转换 bank_loans 表金额为元 ──
ALTER TABLE bank_loans
    MODIFY COLUMN principal_amount DECIMAL(12,2) NOT NULL COMMENT '名义本金（元）',
    MODIFY COLUMN fee_amount DECIMAL(12,2) NOT NULL COMMENT '手续费（元）',
    MODIFY COLUMN disbursed_amount DECIMAL(12,2) NOT NULL COMMENT '实际发放（元）';

UPDATE bank_loans SET
    principal_amount = principal_amount / 100,
    fee_amount = fee_amount / 100,
    disbursed_amount = disbursed_amount / 100;

-- ── 7. 转换 bank_credit_config 表 ──
ALTER TABLE bank_credit_config
    MODIFY COLUMN max_total_credit DECIMAL(12,2) NOT NULL DEFAULT 10000.00 COMMENT '全场信贷总额上限（元）',
    MODIFY COLUMN max_per_person DECIMAL(12,2) NOT NULL DEFAULT 200.00 COMMENT '个人借款上限（元）';

UPDATE bank_credit_config SET
    max_total_credit = max_total_credit / 100,
    max_per_person = max_per_person / 100;

-- ── 8. 转换 products 表金额为元 ──
ALTER TABLE products
    MODIFY COLUMN price DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '售价（元）',
    MODIFY COLUMN cost_price DECIMAL(12,2) NULL COMMENT '成本价（元）';

UPDATE products SET
    price = price / 100,
    cost_price = CASE WHEN cost_price IS NOT NULL THEN cost_price / 100 ELSE NULL END;

-- ── 9. 转换 booth_settlements 表（如果存在）──
-- 安全检查：仅在表存在时执行
SET @table_exists = (SELECT COUNT(*) FROM information_schema.tables 
    WHERE table_schema = DATABASE() AND table_name = 'booth_settlements');

-- ── 10. 删除不再需要的表 ──
DROP TABLE IF EXISTS account_transfers;
DROP TABLE IF EXISTS stock_accounts;

-- ── 11. 移除旧的检查约束（分为单位的约束）──
-- MySQL 8.0+ 支持 DROP CONSTRAINT
-- 如果约束不存在会报错，可忽略
-- ALTER TABLE accounts DROP CONSTRAINT chk_account_balance;
-- ALTER TABLE transactions DROP CONSTRAINT chk_amount_positive;
-- ALTER TABLE transactions DROP CONSTRAINT chk_balance_before_non_negative;
-- ALTER TABLE transactions DROP CONSTRAINT chk_balance_after_non_negative;

-- ── 完成 ──
-- 注意：执行此迁移后需要重启后端服务
