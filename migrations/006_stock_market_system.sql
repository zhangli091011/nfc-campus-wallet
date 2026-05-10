-- ============================================
-- Stock Market System Migration
-- 模拟股市与期末结算系统
-- ============================================

-- 1. 股票表 (stocks)
CREATE TABLE IF NOT EXISTS stocks (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '股票ID',
    booth_id INT NOT NULL UNIQUE COMMENT '摊位ID（每个摊位只能发行一只股票）',
    event_id INT NOT NULL COMMENT '活动ID',
    initial_price INT NOT NULL DEFAULT 1000 COMMENT '初始发行价（分），默认1000分=10元',
    total_shares INT NOT NULL COMMENT '总发行股数',
    sold_shares INT NOT NULL DEFAULT 0 COMMENT '已售出股数',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '股票状态: active/suspended/settled',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 外键约束
    FOREIGN KEY (booth_id) REFERENCES booths(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    
    -- 检查约束
    CONSTRAINT chk_stock_status CHECK (status IN ('active', 'suspended', 'settled')),
    CONSTRAINT chk_initial_price_positive CHECK (initial_price > 0),
    CONSTRAINT chk_total_shares_positive CHECK (total_shares > 0),
    CONSTRAINT chk_sold_shares_non_negative CHECK (sold_shares >= 0),
    CONSTRAINT chk_sold_not_exceed_total CHECK (sold_shares <= total_shares),
    
    -- 索引
    INDEX idx_event_id (event_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票表';


-- 2. 股票购买记录表 (stock_purchases)
CREATE TABLE IF NOT EXISTS stock_purchases (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '购买记录ID',
    stock_id INT NOT NULL COMMENT '股票ID',
    participant_id INT NOT NULL COMMENT '购买者ID',
    event_id INT NOT NULL COMMENT '活动ID',
    quantity INT NOT NULL COMMENT '购买股数',
    purchase_price INT NOT NULL COMMENT '购买单价（分）',
    total_amount INT NOT NULL COMMENT '购买总金额（分）',
    transaction_id INT NULL COMMENT '关联的交易记录ID',
    status VARCHAR(20) NOT NULL DEFAULT 'holding' COMMENT '状态: holding/settled',
    settlement_price INT NULL COMMENT '结算单价（分，结算后填充）',
    settlement_amount INT NULL COMMENT '结算总金额（分，结算后填充）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '购买时间',
    settled_at DATETIME NULL COMMENT '结算时间',
    
    -- 外键约束
    FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE,
    FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE SET NULL,
    
    -- 检查约束
    CONSTRAINT chk_purchase_status CHECK (status IN ('holding', 'settled')),
    CONSTRAINT chk_quantity_positive CHECK (quantity > 0),
    CONSTRAINT chk_purchase_price_positive CHECK (purchase_price > 0),
    CONSTRAINT chk_total_amount_positive CHECK (total_amount > 0),
    CONSTRAINT chk_settlement_price_non_negative CHECK (settlement_price IS NULL OR settlement_price >= 0),
    CONSTRAINT chk_settlement_amount_non_negative CHECK (settlement_amount IS NULL OR settlement_amount >= 0),
    
    -- 索引
    INDEX idx_stock_id (stock_id),
    INDEX idx_participant_id (participant_id),
    INDEX idx_event_id (event_id),
    INDEX idx_transaction_id (transaction_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票购买记录表';


-- 3. 摊位期末结算表 (booth_settlements)
CREATE TABLE IF NOT EXISTS booth_settlements (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '结算记录ID',
    booth_id INT NOT NULL UNIQUE COMMENT '摊位ID',
    stock_id INT NOT NULL UNIQUE COMMENT '股票ID',
    event_id INT NOT NULL COMMENT '活动ID',
    
    -- 经营数据
    revenue INT NOT NULL DEFAULT 0 COMMENT '营业额（分）',
    profit INT NOT NULL DEFAULT 0 COMMENT '净利润（分）',
    order_count INT NOT NULL DEFAULT 0 COMMENT '订单总数',
    
    -- 计算结果
    score DECIMAL(20, 6) NOT NULL COMMENT '摊位经营分 = 0.2*营业额 + 0.6*净利润 + 0.2*订单数',
    global_pool INT NOT NULL COMMENT '全局奖金池（分）',
    total_score DECIMAL(20, 6) NOT NULL COMMENT '全场摊位总分',
    ratio DECIMAL(10, 8) NOT NULL COMMENT '分红占比（0-1）',
    final_price INT NOT NULL COMMENT '最终每股价格（分）',
    
    settled_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '结算时间',
    
    -- 外键约束
    FOREIGN KEY (booth_id) REFERENCES booths(id) ON DELETE CASCADE,
    FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    
    -- 检查约束
    CONSTRAINT chk_revenue_non_negative CHECK (revenue >= 0),
    CONSTRAINT chk_order_count_non_negative CHECK (order_count >= 0),
    CONSTRAINT chk_score_non_negative CHECK (score >= 0),
    CONSTRAINT chk_global_pool_non_negative CHECK (global_pool >= 0),
    CONSTRAINT chk_total_score_positive CHECK (total_score > 0),
    CONSTRAINT chk_ratio_range CHECK (ratio >= 0 AND ratio <= 1),
    CONSTRAINT chk_final_price_non_negative CHECK (final_price >= 0),
    
    -- 索引
    INDEX idx_event_id (event_id),
    INDEX idx_score (score DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='摊位期末结算表';


-- ============================================
-- 数据完整性说明
-- ============================================

-- 1. 股票发行规则：
--    - 每个摊位只能发行一只股票（booth_id UNIQUE）
--    - 初始发行价统一为 1000 分（10元）
--    - 总发行股数由管理员设定
--    - 已售出股数不能超过总发行股数

-- 2. 股票购买规则：
--    - 参与者使用账户余额购买股票
--    - 购买价格为初始发行价（不随市场变化）
--    - 股票不可二次交易，只能锁仓至期末结算
--    - 每次购买创建一条交易记录（扣除余额）

-- 3. 期末结算规则：
--    - 全局奖金池 = (全场买股总金额) * (1 - 0.05 手续费)
--    - 摊位经营分 = 0.2 * 营业额 + 0.6 * 净利润 + 0.2 * 订单总数
--    - 摊位分红占比 = 该摊位分 / 全场摊位总分
--    - 摊位最终每股价格 = (奖金池 * 占比) / 该摊位售出总股数

-- 4. 事务一致性：
--    - 购买股票时同时扣除账户余额和增加已售股数
--    - 结算时批量更新所有股票状态和购买记录
--    - 使用数据库事务保证原子性

-- ============================================
-- 示例数据（可选）
-- ============================================

-- 示例：为活动1的3个摊位发行股票
-- INSERT INTO stocks (booth_id, event_id, initial_price, total_shares, status)
-- VALUES 
--     (1, 1, 1000, 100, 'active'),  -- 摊位1发行100股
--     (2, 1, 1000, 150, 'active'),  -- 摊位2发行150股
--     (3, 1, 1000, 120, 'active');  -- 摊位3发行120股

-- ============================================
-- 迁移完成
-- ============================================
