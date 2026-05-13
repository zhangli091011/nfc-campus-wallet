-- ============================================================================
-- Migration 013: Random Discount System (随机立减系统)
-- ============================================================================
-- 
-- 功能说明：
-- 1. 随机立减配置表：管理员可配置立减力度范围、总奖池等
-- 2. 随机立减记录表：记录每次立减的详细信息
-- ============================================================================

USE nfc;

-- ============================================================================
-- 1. 随机立减配置表
-- ============================================================================

CREATE TABLE IF NOT EXISTS random_discount_settings (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '配置ID',
    event_id INT NOT NULL COMMENT '活动ID',
    enabled BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否启用随机立减',
    min_discount_amount DECIMAL(12,2) NOT NULL DEFAULT 0.01 COMMENT '最小立减金额（元）',
    max_discount_amount DECIMAL(12,2) NOT NULL DEFAULT 5.00 COMMENT '最大立减金额（元）',
    probability INT NOT NULL DEFAULT 100 COMMENT '触发概率（百分比，1-100）',
    total_pool DECIMAL(12,2) NOT NULL DEFAULT 1000.00 COMMENT '总奖池金额（元）',
    remaining_pool DECIMAL(12,2) NOT NULL DEFAULT 1000.00 COMMENT '剩余奖池金额（元）',
    max_discount_per_transaction DECIMAL(12,2) DEFAULT NULL COMMENT '单笔最大立减金额（元），NULL表示不限',
    min_payment_amount DECIMAL(12,2) NOT NULL DEFAULT 1.00 COMMENT '触发立减的最低消费金额（元）',
    daily_limit_per_user INT DEFAULT NULL COMMENT '每人每日最多享受次数，NULL表示不限',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    CONSTRAINT fk_discount_setting_event 
        FOREIGN KEY (event_id) 
        REFERENCES events(id) 
        ON DELETE CASCADE,
    CONSTRAINT chk_discount_amount_range 
        CHECK (max_discount_amount >= min_discount_amount),
    CONSTRAINT chk_discount_min_positive 
        CHECK (min_discount_amount >= 0),
    CONSTRAINT chk_probability_range 
        CHECK (probability >= 1 AND probability <= 100),
    CONSTRAINT chk_pool_non_negative 
        CHECK (remaining_pool >= 0),
    CONSTRAINT chk_total_pool_positive 
        CHECK (total_pool > 0),
    
    UNIQUE KEY uk_discount_event (event_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='随机立减配置表';

-- ============================================================================
-- 2. 随机立减记录表
-- ============================================================================

CREATE TABLE IF NOT EXISTS random_discount_records (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    event_id INT NOT NULL COMMENT '活动ID',
    participant_id INT NOT NULL COMMENT '参与者ID',
    transaction_id INT NOT NULL COMMENT '关联交易ID',
    booth_id INT DEFAULT NULL COMMENT '摊位ID',
    original_amount DECIMAL(12,2) NOT NULL COMMENT '原始支付金额（元）',
    discount_amount DECIMAL(12,2) NOT NULL COMMENT '立减金额（元）',
    actual_amount DECIMAL(12,2) NOT NULL COMMENT '实际支付金额（元）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    CONSTRAINT fk_discount_record_event 
        FOREIGN KEY (event_id) 
        REFERENCES events(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_discount_record_participant 
        FOREIGN KEY (participant_id) 
        REFERENCES participants(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_discount_record_transaction 
        FOREIGN KEY (transaction_id) 
        REFERENCES transactions(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_discount_record_booth 
        FOREIGN KEY (booth_id) 
        REFERENCES booths(id) 
        ON DELETE SET NULL,
    CONSTRAINT chk_discount_amount_positive 
        CHECK (discount_amount > 0),
    CONSTRAINT chk_actual_amount 
        CHECK (actual_amount = original_amount - discount_amount)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='随机立减记录表';

CREATE INDEX idx_discount_records_event ON random_discount_records(event_id);
CREATE INDEX idx_discount_records_participant ON random_discount_records(participant_id);
CREATE INDEX idx_discount_records_transaction ON random_discount_records(transaction_id);
CREATE INDEX idx_discount_records_created_at ON random_discount_records(created_at);
CREATE INDEX idx_discount_records_participant_date ON random_discount_records(participant_id, created_at);
