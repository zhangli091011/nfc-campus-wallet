-- ============================================================================
-- Migration: Booth Management System (摊位经营系统)
-- Description: 升级为支持多摊位经营的完整商业管理系统
-- Date: 2026-05-01
-- ============================================================================

-- 1. 创建 booths 表（摊位表）
CREATE TABLE IF NOT EXISTS booths (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '摊位ID',
    event_id INT NOT NULL COMMENT '活动ID',
    name VARCHAR(100) NOT NULL COMMENT '摊位名称',
    class_name VARCHAR(100) NOT NULL COMMENT '班级名称',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '摊位状态: active/inactive/closed',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    -- 外键约束
    CONSTRAINT fk_booth_event 
        FOREIGN KEY (event_id) 
        REFERENCES events(id) 
        ON DELETE CASCADE,
    
    -- 约束
    CONSTRAINT chk_booth_status 
        CHECK (status IN ('active', 'inactive', 'closed'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='摊位表';

-- 创建索引
CREATE INDEX idx_booths_event_id ON booths(event_id);

-- 2. 创建 products 表（商品表）
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '商品ID',
    booth_id INT NOT NULL COMMENT '摊位ID',
    name VARCHAR(100) NOT NULL COMMENT '商品名称',
    price INT NOT NULL COMMENT '售价（分）',
    cost_price INT DEFAULT NULL COMMENT '成本价（分）',
    stock INT DEFAULT NULL COMMENT '库存数量（NULL表示无限）',
    enabled BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    -- 外键约束
    CONSTRAINT fk_product_booth 
        FOREIGN KEY (booth_id) 
        REFERENCES booths(id) 
        ON DELETE CASCADE,
    
    -- 约束
    CONSTRAINT chk_price_non_negative 
        CHECK (price >= 0),
    CONSTRAINT chk_cost_price_non_negative 
        CHECK (cost_price IS NULL OR cost_price >= 0),
    CONSTRAINT chk_stock_non_negative 
        CHECK (stock IS NULL OR stock >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品表';

-- 创建索引
CREATE INDEX idx_products_booth_id ON products(booth_id);

-- 3. 创建 users 表（用户表）
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名（唯一）',
    password_hash VARCHAR(255) NOT NULL COMMENT 'bcrypt哈希密码',
    role VARCHAR(20) NOT NULL COMMENT '用户角色: super_admin/event_admin/booth_cashier/issuer/reviewer',
    booth_id INT DEFAULT NULL COMMENT '关联摊位ID（仅booth_cashier需要）',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '用户状态: active/inactive/blocked',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 外键约束
    CONSTRAINT fk_user_booth 
        FOREIGN KEY (booth_id) 
        REFERENCES booths(id) 
        ON DELETE SET NULL,
    
    -- 约束
    CONSTRAINT chk_user_role 
        CHECK (role IN ('super_admin', 'event_admin', 'booth_cashier', 'issuer', 'reviewer')),
    CONSTRAINT chk_user_status 
        CHECK (status IN ('active', 'inactive', 'blocked')),
    CONSTRAINT chk_booth_cashier_has_booth 
        CHECK ((role = 'booth_cashier' AND booth_id IS NOT NULL) OR (role != 'booth_cashier'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 创建索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_booth_id ON users(booth_id);

-- 4. 增强 transactions 表，添加摊位和商品关联
ALTER TABLE transactions
    ADD COLUMN booth_id INT DEFAULT NULL COMMENT '摊位ID' AFTER account_id,
    ADD COLUMN product_id INT DEFAULT NULL COMMENT '商品ID' AFTER booth_id,
    ADD COLUMN operator_id INT DEFAULT NULL COMMENT '操作员用户ID' AFTER product_id;

-- 添加外键约束
ALTER TABLE transactions
    ADD CONSTRAINT fk_transaction_booth 
        FOREIGN KEY (booth_id) 
        REFERENCES booths(id) 
        ON DELETE SET NULL,
    ADD CONSTRAINT fk_transaction_product 
        FOREIGN KEY (product_id) 
        REFERENCES products(id) 
        ON DELETE SET NULL,
    ADD CONSTRAINT fk_transaction_operator 
        FOREIGN KEY (operator_id) 
        REFERENCES users(id) 
        ON DELETE SET NULL;

-- 创建索引
CREATE INDEX idx_transactions_booth_id ON transactions(booth_id);
CREATE INDEX idx_transactions_product_id ON transactions(product_id);
CREATE INDEX idx_transactions_operator_id ON transactions(operator_id);

-- 5. 插入默认超级管理员账户
-- 用户名: admin
-- 密码: admin123
-- 密码哈希使用 bcrypt，cost factor = 12
INSERT INTO users (username, password_hash, role, status)
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEiUM2', 'super_admin', 'active')
ON DUPLICATE KEY UPDATE username = username;  -- 如果已存在则不更新

-- ============================================================================
-- 创建视图：摊位交易统计
-- ============================================================================

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

-- ============================================================================
-- 创建视图：商品销售统计
-- ============================================================================

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

-- ============================================================================
-- 创建触发器：验证商品属于摊位
-- ============================================================================

DELIMITER $

CREATE TRIGGER trg_validate_product_booth
BEFORE INSERT ON transactions
FOR EACH ROW
BEGIN
    DECLARE v_product_booth_id INT;
    
    -- 如果交易包含商品ID和摊位ID，验证商品属于该摊位
    IF NEW.product_id IS NOT NULL AND NEW.booth_id IS NOT NULL THEN
        SELECT booth_id INTO v_product_booth_id
        FROM products
        WHERE id = NEW.product_id;
        
        IF v_product_booth_id IS NULL THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Product not found';
        END IF;
        
        IF v_product_booth_id != NEW.booth_id THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Product does not belong to the specified booth';
        END IF;
    END IF;
END$

DELIMITER ;

-- ============================================================================
-- 创建存储过程：获取摊位收入统计
-- ============================================================================

DELIMITER $

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
-- 数据完整性检查
-- ============================================================================

-- 检查摊位数量
SELECT COUNT(*) AS booth_count FROM booths;

-- 检查商品数量
SELECT COUNT(*) AS product_count FROM products;

-- 检查用户数量
SELECT COUNT(*) AS user_count FROM users;

-- 检查超级管理员是否创建成功
SELECT id, username, role, status, created_at 
FROM users 
WHERE role = 'super_admin';

-- ============================================================================
-- 索引优化建议
-- ============================================================================

-- 复合索引：优化常见查询
CREATE INDEX idx_transactions_booth_created ON transactions(booth_id, created_at);
CREATE INDEX idx_transactions_product_created ON transactions(product_id, created_at);
CREATE INDEX idx_products_booth_enabled ON products(booth_id, enabled);
CREATE INDEX idx_users_role_status ON users(role, status);

-- ============================================================================
-- 完成迁移
-- ============================================================================

SELECT 'Booth Management System migration completed successfully' AS status;
SELECT 'Default super admin created - Username: admin, Password: admin123' AS notice;
SELECT 'IMPORTANT: Please change the default admin password immediately!' AS warning;
