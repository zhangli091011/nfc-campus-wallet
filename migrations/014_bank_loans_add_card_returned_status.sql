-- Migration 014: Add 'card_returned' status to bank_loans
-- 退卡时保留贷款追偿信息，需要新增状态值

ALTER TABLE bank_loans 
    MODIFY COLUMN status ENUM('active', 'repaid', 'written_off', 'card_returned') NOT NULL DEFAULT 'active';
