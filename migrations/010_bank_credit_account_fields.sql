-- ============================================================================
-- Migration: Add credit tracking fields to accounts table
-- Description: 为 accounts 表新增信贷追踪字段，支持官方银行信用垫资模块
-- Business Rules:
--   credit_borrowed: 记录名义借款总额（欠款本金）
--   credit_fee_paid: 记录已支付的借款手续费总额
-- Also updates transaction type CHECK constraint to include loan_issue, loan_fee
-- Date: 2026-05-09
-- ============================================================================

-- 1. 为 accounts 表新增信贷字段
ALTER TABLE accounts
    ADD COLUMN credit_borrowed INT NOT NULL DEFAULT 0 COMMENT '名义借款总额/欠款本金（分）',
    ADD COLUMN credit_fee_paid INT NOT NULL DEFAULT 0 COMMENT '已支付借款手续费总额（分）';

-- 2. 更新 transactions 表的 type CHECK 约束，新增 loan_issue 和 loan_fee
ALTER TABLE transactions DROP CHECK chk_transaction_type;

ALTER TABLE transactions ADD CONSTRAINT chk_transaction_type
    CHECK (type IN ('recharge', 'pay', 'refund', 'adjust', 'issue', 'void', 'expire', 'loan_issue', 'loan_fee'));

-- 3. 创建审计日志表（如果不存在）
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT DEFAULT NULL,
    operator_id INT NOT NULL,
    action VARCHAR(100) NOT NULL COMMENT '操作类型',
    detail TEXT COMMENT '操作详情',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_audit_event (event_id),
    INDEX idx_audit_operator (operator_id),
    INDEX idx_audit_action (action),
    INDEX idx_audit_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统审计日志表';

-- 4. 验证
SELECT 'Migration 010 completed: credit_borrowed, credit_fee_paid added to accounts; loan_issue/loan_fee types added' AS status;
