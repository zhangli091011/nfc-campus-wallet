-- ============================================
-- Stock Account System Migration
-- 投资币账户系统（双账户体系）
-- ============================================

-- 1. 投资币账户表 (stock_accounts)
CREATE TABLE IF NOT EXISTS stock_accounts (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '投资币账户ID',
    participant_id INT NOT NULL COMMENT '参与者ID',
    event_id INT NOT NULL COMMENT '活动ID',
    balance INT NOT NULL DEFAULT 0 COMMENT '投资币余额（分）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 外键约束
    FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    
    -- 唯一约束：每个参与者在每个活动下只能有一个投资币账户
    UNIQUE KEY uk_stock_participant_event (participant_id, event_id),
    
    -- 检查约束
    CONSTRAINT chk_stock_balance_non_negative CHECK (balance >= 0),
    
    -- 索引
    INDEX idx_participant_id (participant_id),
    INDEX idx_event_id (event_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='投资币账户表';


-- 2. 股票订单表 (stock_orders)
CREATE TABLE IF NOT EXISTS stock_orders (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '订单ID',
    event_id INT NOT NULL COMMENT '活动ID',
    participant_id INT NOT NULL COMMENT '参与者ID',
    stock_account_id INT NOT NULL COMMENT '投资币账户ID',
    card_uid VARCHAR(32) NOT NULL COMMENT 'NFC卡UID',
    booth_id INT NOT NULL COMMENT '摊位ID',
    shares INT NOT NULL COMMENT '购买股数',
    buy_price INT NOT NULL COMMENT '购买单价（分）',
    total_amount INT NOT NULL COMMENT '购买总金额（分）',
    status VARCHAR(20) NOT NULL DEFAULT 'holding' COMMENT '订单状态: holding/settled',
    settlement_price INT NULL COMMENT '结算单价（分）',
    settlement_amount INT NULL COMMENT '结算总金额（分）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '购买时间',
    settled_at DATETIME NULL COMMENT '结算时间',
    
    -- 外键约束
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE,
    FOREIGN KEY (stock_account_id) REFERENCES stock_accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (booth_id) REFERENCES booths(id) ON DELETE CASCADE,
    
    -- 检查约束
    CONSTRAINT chk_order_status CHECK (status IN ('holding', 'settled')),
    CONSTRAINT chk_shares_positive CHECK (shares > 0),
    CONSTRAINT chk_buy_price_positive CHECK (buy_price > 0),
    CONSTRAINT chk_order_total_amount_positive CHECK (total_amount > 0),
    CONSTRAINT chk_order_settlement_price_non_negative CHECK (settlement_price IS NULL OR settlement_price >= 0),
    CONSTRAINT chk_order_settlement_amount_non_negative CHECK (settlement_amount IS NULL OR settlement_amount >= 0),
    
    -- 索引
    INDEX idx_event_id (event_id),
    INDEX idx_participant_id (participant_id),
    INDEX idx_stock_account_id (stock_account_id),
    INDEX idx_card_uid (card_uid),
    INDEX idx_booth_id (booth_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票订单表';


-- 3. 账户互转记录表 (account_transfers)
CREATE TABLE IF NOT EXISTS account_transfers (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '转账记录ID',
    event_id INT NOT NULL COMMENT '活动ID',
    participant_id INT NOT NULL COMMENT '参与者ID',
    card_uid VARCHAR(32) NOT NULL COMMENT 'NFC卡UID',
    transfer_type VARCHAR(20) NOT NULL COMMENT '转账类型: to_stock(余额→投资币), from_stock(投资币→余额)',
    amount INT NOT NULL COMMENT '转账金额（分）',
    account_balance_before INT NOT NULL COMMENT '活动账户转账前余额（分）',
    account_balance_after INT NOT NULL COMMENT '活动账户转账后余额（分）',
    stock_balance_before INT NOT NULL COMMENT '投资币账户转账前余额（分）',
    stock_balance_after INT NOT NULL COMMENT '投资币账户转账后余额（分）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '转账时间',
    
    -- 外键约束
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE,
    
    -- 检查约束
    CONSTRAINT chk_transfer_type CHECK (transfer_type IN ('to_stock', 'from_stock')),
    CONSTRAINT chk_transfer_amount_positive CHECK (amount > 0),
    CONSTRAINT chk_account_before_non_negative CHECK (account_balance_before >= 0),
    CONSTRAINT chk_account_after_non_negative CHECK (account_balance_after >= 0),
    CONSTRAINT chk_stock_before_non_negative CHECK (stock_balance_before >= 0),
    CONSTRAINT chk_stock_after_non_negative CHECK (stock_balance_after >= 0),
    
    -- 索引
    INDEX idx_event_id (event_id),
    INDEX idx_participant_id (participant_id),
    INDEX idx_card_uid (card_uid),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='账户互转记录表';


-- ============================================
-- 系统说明
-- ============================================

-- 1. 双账户体系：
--    - accounts: 活动账户，用于日常消费（充值、支付、退款）
--    - stock_accounts: 投资币账户，用于股票投资

-- 2. 账户互转：
--    - to_stock: 活动账户余额 → 投资币账户
--    - from_stock: 投资币账户 → 活动账户余额
--    - 互转比例 1:1，无手续费

-- 3. 股票购买流程：
--    - 参与者使用投资币账户余额购买股票
--    - 扣除投资币余额，创建股票订单
--    - 股票不可二次交易，只能锁仓至期末结算

-- 4. 期末结算流程：
--    - 计算全局奖金池 = (全场买股总金额) * 0.95
--    - 计算摊位经营分 = 0.2*营业额 + 0.6*净利润 + 0.2*订单数
--    - 计算摊位分红占比 = 该摊位分 / 全场总分
--    - 计算最终股价 = (奖金池 * 占比) / 该摊位售出总股数
--    - 更新所有订单的结算价格和结算金额

-- 5. 并发安全：
--    - 使用悲观锁 (SELECT ... FOR UPDATE) 防止并发问题
--    - 购买股票时锁定投资币账户
--    - 账户互转时同时锁定两个账户

-- ============================================
-- 迁移完成
-- ============================================
