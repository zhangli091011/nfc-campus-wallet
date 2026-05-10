-- ============================================================================
-- Migration: Add credit columns to accounts table
-- Description: 添加信用借款相关字段（官方银行垫资功能）
-- Date: 2026-05-09
-- ============================================================================

ALTER TABLE accounts
    ADD COLUMN credit_borrowed INT NOT NULL DEFAULT 0 COMMENT '名义借款总额/欠款本金（分）',
    ADD COLUMN credit_fee_paid INT NOT NULL DEFAULT 0 COMMENT '已支付借款手续费总额（分）';

SELECT 'Added credit_borrowed and credit_fee_paid columns to accounts table' AS status;
