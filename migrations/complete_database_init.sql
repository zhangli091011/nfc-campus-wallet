-- ============================================================================
-- NFC Campus Wallet - Complete Database Initialization Script
-- 完整数据库初始化脚本（合并所有迁移）
-- ============================================================================
-- 
-- 说明：
-- 本脚本整合了所有数据库迁移，可用于全新安装
-- 包含以下功能：
-- - 基础表结构（活动、参与者、账户）
-- - 摊位管理系统（摊位、商品）
-- - 用户权限系统（用户、角色）
-- - 交易记录系统（完整账本模式）
-- - 摊位收款账户功能
-- - 统计视图和存储过程
-- 
-- 版本：v1.0
-- 日期：2026-05-09
-- ============================================================================

-- 使用数据库
USE nfc;

-- ============================================================================
-- 1. 基础表：Events（活动表）
-- ============================================================================

CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '活动ID',
    name VARCHAR(100) NOT NULL COMMENT '活动名称',
    start_date DATE NOT NULL COMMENT '开始日期',
    end_date DATE NOT NULL COMMENT '结束日期',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '活动状态: active/inactive/closed',
    allow_recharge BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否允许充值',
    allow_payment BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否允许支付',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    CONSTRAINT chk_event_status 
        CHECK (status IN ('active', 'inactive', 'closed')),
    CONSTRAINT chk_event_dates 
        CHECK (end_date >= start_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='活动表';

CREATE INDEX idx_events_status ON events(status);
CREATE INDEX idx_events_dates ON events(start_date, end_date);

-- ============================================================================
-- 2. 基础表：Participants（参与者表）
-- ============================================================================

CREATE TABLE IF NOT EXISTS participants (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '参与者ID',
    name VARCHAR(100) NOT NULL COMMENT '参与者姓名',
    card_uid VARCHAR(32) UNIQUE NOT NULL COMMENT 'NFC卡片UID（唯一）',
    class_name VARCHAR(100) DEFAULT NULL COMMENT '班级名称',
    student_no VARCHAR(50) DEFAULT NULL COMMENT '学号',
    participant_type VARCHAR(20) NOT NULL DEFAULT 'person' COMMENT '参与者类型: person/booth_collection',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '参与者状态: active/inactive/blocked',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    CONSTRAINT chk_participant_type 
        CHECK (participant_type IN ('person', 'booth_collection')),
    CONSTRAINT chk_participant_status 
        CHECK (status IN ('active', 'inactive', 'blocked'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='参与者表';

CREATE INDEX idx_participants_card_uid ON participants(card_uid);
CREATE INDEX idx_participants_type ON participants(participant_type);
CREATE INDEX idx_participants_status ON participants(status);

-- ============================================================================
-- 3. 基础表：Accounts（账户表）
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounts (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '账户ID',
    participant_id INT NOT NULL COMMENT '参与者ID',
    event_id INT NOT NULL COMMENT '活动ID',
    balance INT NOT NULL DEFAULT 0 COMMENT '账户余额（分）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    CONSTRAINT fk_account_participant 
        FOREIGN KEY (participant_id) 
        REFERENCES participants(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_account_event 
        FOREIGN KEY (event_id) 
        REFERENCES events(id) 
        ON DELETE CASCADE,
    CONSTRAINT chk_balance_non_negative 
        CHECK (balance >= 0),
    
    UNIQUE KEY uk_participant_event (participant_id, event_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='账户表';

CREATE INDEX idx_accounts_participant ON accounts(participant_id);
CREATE INDEX idx_accounts_event ON accounts(event_id);
CREATE INDEX idx_accounts_participant_event ON accounts(participant_id, event_id);
CREATE INDEX idx_accounts_event_balance ON accounts(event_id, balance);

-- ============================================================================
-- 4. 摊位表：Booths（摊位表）
-- ============================================================================

CREATE TABLE IF NOT EXISTS booths (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '摊位ID',
    event_id INT NOT NULL COMMENT '活动ID',
    name VARCHAR(100) NOT NULL COMMENT '摊位名称',
    class_name VARCHAR(100) NOT NULL COMMENT '班级名称',
    collection_participant_id INT DEFAULT NULL COMMENT '收款参与者ID（用于摊位收款账户）',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '摊位状态: active/inactive/closed',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    CONSTRAINT fk_booth_event 
        FOREIGN KEY (event_id) 
        REFERENCES events(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_booth_collection_participant 
        FOREIGN KEY (collection_participant_id) 
        REFERENCES participants(id) 
        ON DELETE SET NULL,
    CONSTRAINT chk_booth_status 
        CHECK (status IN ('active', 'inactive', 'closed'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='摊位表';

CREATE INDEX idx_booths_event_id ON booths(event_id);
CREATE INDEX idx_booths_collection_participant ON booths(collection_participant_id);

-- ============================================================================
-- 5. 商品表：Products（商品表）
-- ============================================================================

CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '商品ID',
    booth_id INT NOT NULL COMMENT '摊位ID',
    name VARCHAR(100) NOT NULL COMMENT '商品名称',
    price INT NOT NULL COMMENT '售价（分）',
    cost_price INT DEFAULT NULL COMMENT '成本价（分）',
    stock INT DEFAULT NULL COMMENT '库存数量（NULL表示无限）',
    enabled BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    CONSTRAINT fk_product_booth 
        FOREIGN KEY (booth_id) 
        REFERENCES booths(id) 
        ON DELETE CASCADE,
    CONSTRAINT chk_price_non_negative 
        CHECK (price >= 0),
    CONSTRAINT chk_cost_price_non_negative 
        CHECK (cost_price IS NULL OR cost_price >= 0),
    CONSTRAINT chk_stock_non_negative 
        CHECK (stock IS NULL OR stock >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品表';

CREATE INDEX idx_products_booth_id ON products(booth_id);
CREATE INDEX idx_products_booth_enabled ON products(booth_id, enabled);

-- ============================================================================
-- 6. 用户表：Users（用户表）
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名（唯一）',
    password_hash VARCHAR(255) NOT NULL COMMENT 'bcrypt哈希密码',
    role VARCHAR(20) NOT NULL COMMENT '用户角色: super_admin/event_admin/booth_cashier/issuer/reviewer',
    booth_id INT DEFAULT NULL COMMENT '关联摊位ID（仅booth_cashier需要）',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '用户状态: active/inactive/blocked',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    CONSTRAINT fk_user_booth 
        FOREIGN KEY (booth_id) 
        REFERENCES booths(id) 
        ON DELETE SET NULL,
    CONSTRAINT chk_user_role 
        CHECK (role IN ('super_admin', 'event_admin', 'booth_cashier', 'issuer', 'reviewer')),
    CONSTRAINT chk_user_status 
        CHECK (status IN ('active', 'inactive', 'blocked'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_booth_id ON users(booth_id);
CREATE INDEX idx_users_role_status ON users(role, status);

-- ============================================================================
-- 7. 交易表：Transactions（交易表 - 完整账本模式）
-- ============================================================================

CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '交易ID',
    type VARCHAR(20) NOT NULL COMMENT '交易类型: pay/recharge/refund',
    amount INT NOT NULL COMMENT '交易金额（分）',
    balance_before INT NOT NULL COMMENT '交易前余额（分）',
    balance_after INT NOT NULL COMMENT '交易后余额（分）',
    participant_id INT NOT NULL COMMENT '参与者ID',
    event_id INT NOT NULL COMMENT '活动ID',
    account_id INT NOT NULL COMMENT '账户ID',
    booth_id INT DEFAULT NULL COMMENT '摊位ID',
    product_id INT DEFAULT NULL COMMENT '商品ID',
    operator_id INT DEFAULT NULL COMMENT '操作员用户ID',
    remark VARCHAR(255) DEFAULT NULL COMMENT '备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '交易时间',
    
    CONSTRAINT fk_transaction_participant 
        FOREIGN KEY (participant_id) 
        REFERENCES participants(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_transaction_event 
        FOREIGN KEY (event_id) 
        REFERENCES events(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_transaction_account 
        FOREIGN KEY (account_id) 
        REFERENCES accounts(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_transaction_booth 
        FOREIGN KEY (booth_id) 
        REFERENCES booths(id) 
        ON DELETE SET NULL,
    CONSTRAINT fk_transaction_product 
        FOREIGN KEY (product_id) 
        REFERENCES products(id) 
        ON DELETE SET NULL,
    CONSTRAINT fk_transaction_operator 
        FOREIGN KEY (operator_id) 
        REFERENCES users(id) 
        ON DELETE SET NULL,
    CONSTRAINT chk_transaction_type 
        CHECK (type IN ('pay', 'recharge', 'refund')),
    CONSTRAINT chk_amount_positive 
        CHECK (amount > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交易表';

CREATE INDEX idx_transactions_participant ON transactions(participant_id);
CREATE INDEX idx_transactions_event ON transactions(event_id);
CREATE INDEX idx_transactions_account ON transactions(account_id);
CREATE INDEX idx_transactions_booth_id ON transactions(booth_id);
CREATE INDEX idx_transactions_product_id ON transactions(product_id);
CREATE INDEX idx_transactions_operator_id ON transactions(operator_id);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_transactions_booth_created ON transactions(booth_id, created_at);
CREATE INDEX idx_transactions_product_created ON transactions(product_id, created_at);
CREATE INDEX idx_transactions_event_participant ON transactions(event_id, participant_id);
CREATE INDEX idx_transactions_account_created ON transactions(account_id, created_at);

-- ============================================================================
-- 8. 插入默认数据
-- ============================================================================

-- 插入默认超级管理员账户
-- 用户名: admin
-- 密码: admin123
-- 密码哈希使用 bcrypt，cost factor = 12
INSERT INTO users (username, password_hash, role, status)
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEiUM2', 'super_admin', 'active')
ON DUPLICATE KEY UPDATE username = username;

-- ============================================================================
-- 9. 创建视图
-- ============================================================================

-- 摊位交易统计视图
CREATE OR REPLACE VIEW booth_transaction_stats AS
SELECT 
    b.id AS booth_id,
    b.name AS booth_name,
    b.class_name,
    b.event_id,
    COUNT(t.id) AS transaction_count,
    COALESCE(SUM(CASE WHEN t.type = 'pay' THEN t.amount ELSE 0 END), 0) AS total_sales_cents,
    COALESCE(SUM(CASE WHEN t.type = 'pay' THEN t.amount ELSE 0 END), 0) / 100.0 AS total_sales_yuan,
    COALESCE(SUM(CASE WHEN t.type = 'refund' THEN t.amount ELSE 0 END), 0) AS total_refunds_cents,
    COALESCE(SUM(CASE WHEN t.type = 'refund' THEN t.amount ELSE 0 END), 0) / 100.0 AS total_refunds_yuan,
    MIN(t.created_at) AS first_transaction_at,
    MAX(t.created_at) AS last_transaction_at
FROM booths b
LEFT JOIN transactions t ON b.id = t.booth_id
GROUP BY b.id, b.name, b.class_name, b.event_id;

-- 商品销售统计视图
CREATE OR REPLACE VIEW product_sales_stats AS
SELECT 
    p.id AS product_id,
    p.name AS product_name,
    p.booth_id,
    b.name AS booth_name,
    p.price AS price_cents,
    p.price / 100.0 AS price_yuan,
    p.cost_price AS cost_price_cents,
    p.cost_price / 100.0 AS cost_price_yuan,
    p.stock,
    p.enabled,
    COUNT(t.id) AS sales_count,
    COALESCE(SUM(t.amount), 0) AS total_revenue_cents,
    COALESCE(SUM(t.amount), 0) / 100.0 AS total_revenue_yuan,
    CASE 
        WHEN p.cost_price IS NOT NULL THEN 
            (COALESCE(SUM(t.amount), 0) - (COUNT(t.id) * p.cost_price))
        ELSE NULL 
    END AS total_profit_cents,
    CASE 
        WHEN p.cost_price IS NOT NULL THEN 
            (COALESCE(SUM(t.amount), 0) - (COUNT(t.id) * p.cost_price)) / 100.0
        ELSE NULL 
    END AS total_profit_yuan
FROM products p
INNER JOIN booths b ON p.booth_id = b.id
LEFT JOIN transactions t ON p.id = t.product_id AND t.type = 'pay'
GROUP BY p.id, p.name, p.booth_id, b.name, p.price, p.cost_price, p.stock, p.enabled;

-- 账户详情视图
CREATE OR REPLACE VIEW account_details_view AS
SELECT 
    a.id AS account_id,
    a.balance / 100.0 AS balance_yuan,
    p.id AS participant_id,
    p.name AS participant_name,
    p.card_uid,
    p.student_no,
    p.class_name,
    p.participant_type,
    e.id AS event_id,
    e.name AS event_name,
    e.status AS event_status,
    e.start_date,
    e.end_date,
    a.created_at,
    a.updated_at
FROM accounts a
INNER JOIN participants p ON a.participant_id = p.id
INNER JOIN events e ON a.event_id = e.id;

-- ============================================================================
-- 10. 创建存储过程
-- ============================================================================

-- 获取或创建账户
DELIMITER $

DROP PROCEDURE IF EXISTS sp_get_or_create_account$

CREATE PROCEDURE sp_get_or_create_account(
    IN p_participant_id INT,
    IN p_event_id INT,
    OUT p_account_id INT,
    OUT p_balance INT
)
BEGIN
    DECLARE v_account_id INT;
    DECLARE v_balance INT;
    
    -- 尝试获取现有账户
    SELECT id, balance INTO v_account_id, v_balance
    FROM accounts
    WHERE participant_id = p_participant_id AND event_id = p_event_id
    LIMIT 1;
    
    -- 如果账户不存在，创建新账户
    IF v_account_id IS NULL THEN
        INSERT INTO accounts (participant_id, event_id, balance)
        VALUES (p_participant_id, p_event_id, 0);
        
        SET v_account_id = LAST_INSERT_ID();
        SET v_balance = 0;
    END IF;
    
    -- 返回结果
    SET p_account_id = v_account_id;
    SET p_balance = v_balance;
END$

-- 获取摊位收入统计
DROP PROCEDURE IF EXISTS sp_get_booth_revenue$

CREATE PROCEDURE sp_get_booth_revenue(
    IN p_booth_id INT,
    IN p_start_date DATETIME,
    IN p_end_date DATETIME,
    OUT p_total_sales INT,
    OUT p_total_refunds INT,
    OUT p_net_revenue INT,
    OUT p_transaction_count INT
)
BEGIN
    SELECT 
        COALESCE(SUM(CASE WHEN type = 'pay' THEN amount ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN type = 'refund' THEN amount ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN type = 'pay' THEN amount WHEN type = 'refund' THEN -amount ELSE 0 END), 0),
        COUNT(*)
    INTO p_total_sales, p_total_refunds, p_net_revenue, p_transaction_count
    FROM transactions
    WHERE booth_id = p_booth_id
        AND created_at >= p_start_date
        AND created_at <= p_end_date;
END$

DELIMITER ;

-- ============================================================================
-- 11. 数据完整性检查
-- ============================================================================

SELECT '========================================' AS divider;
SELECT 'Database initialization completed successfully!' AS status;
SELECT '========================================' AS divider;
SELECT 'Table Statistics:' AS info;
SELECT COUNT(*) AS event_count FROM events;
SELECT COUNT(*) AS participant_count FROM participants;
SELECT COUNT(*) AS account_count FROM accounts;
SELECT COUNT(*) AS booth_count FROM booths;
SELECT COUNT(*) AS product_count FROM products;
SELECT COUNT(*) AS user_count FROM users;
SELECT COUNT(*) AS transaction_count FROM transactions;
SELECT '========================================' AS divider;
SELECT 'Default Admin Account:' AS info;
SELECT id, username, role, status, created_at FROM users WHERE role = 'super_admin';
SELECT '========================================' AS divider;
SELECT 'IMPORTANT: Default admin password is "admin123"' AS warning;
SELECT 'Please change it immediately after first login!' AS warning;
SELECT '========================================' AS divider;

-- ============================================================================
-- 完成
-- ============================================================================
