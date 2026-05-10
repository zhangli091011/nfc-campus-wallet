-- ============================================================================
-- Migration: Bank Credit (Official Loan) System
-- Description: 官方银行信用垫资模块 - 前端扣息模型
-- Business Rules:
--   1. 学生名义借款 N 元（线下签署纸质借条）
--   2. 系统收取固定 5% 手续费
--   3. 实际发放到 NFC 账户 = N * 0.95
--   4. 账本精确记录：本金、手续费、实际到账
-- Date: 2026-05-09
-- ============================================================================

-- 信贷记录表
CREATE TABLE IF NOT EXISTS bank_loans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    participant_id INT NOT NULL,
    operator_id INT NOT NULL COMMENT '放贷操作员 (bank_clerk)',
    
    -- 核心账本字段
    principal_amount INT NOT NULL COMMENT '名义借款本金（分）',
    fee_rate DECIMAL(5,4) NOT NULL DEFAULT 0.0500 COMMENT '手续费率',
    fee_amount INT NOT NULL COMMENT '扣除的手续费（分）',
    disbursed_amount INT NOT NULL COMMENT '实际发放到账金额（分）',
    
    -- 状态
    status ENUM('active', 'repaid', 'written_off') NOT NULL DEFAULT 'active',
    remark VARCHAR(255) DEFAULT NULL COMMENT '备注（如借条编号）',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    repaid_at TIMESTAMP NULL DEFAULT NULL,
    
    -- 外键
    CONSTRAINT fk_loan_event FOREIGN KEY (event_id) REFERENCES events(id),
    CONSTRAINT fk_loan_participant FOREIGN KEY (participant_id) REFERENCES participants(id),
    CONSTRAINT fk_loan_operator FOREIGN KEY (operator_id) REFERENCES users(id),
    
    -- 索引
    INDEX idx_loan_event (event_id),
    INDEX idx_loan_participant (participant_id),
    INDEX idx_loan_status (status),
    INDEX idx_loan_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='官方银行信贷记录表';

-- 信贷系统配置表
CREATE TABLE IF NOT EXISTS bank_credit_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL UNIQUE,
    max_total_credit INT NOT NULL DEFAULT 1000000 COMMENT '全场信贷总额上限（分），默认10000元',
    max_per_person INT NOT NULL DEFAULT 50000 COMMENT '单人借款上限（分），默认500元',
    fee_rate DECIMAL(5,4) NOT NULL DEFAULT 0.0500 COMMENT '手续费率，默认5%',
    is_enabled TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_credit_config_event FOREIGN KEY (event_id) REFERENCES events(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='信贷系统配置';

-- 验证
SELECT 'Bank credit system tables created successfully' AS status;
