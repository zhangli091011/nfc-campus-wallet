-- ============================================================================
-- Migration: Upgrade to Ledger Mode (账本追加模式)
-- Description: 将简单余额模型升级为完整的账本追加模式
-- Date: 2026-05-01
-- ============================================================================

-- 1. 扩展 transactions 表，添加账本追加模式所需字段
ALTER TABLE transactions
    -- 交易前余额（单位：分）
    ADD COLUMN balance_before INT NOT NULL DEFAULT 0 COMMENT '交易前余额（分）',
    
    -- 关联交易ID（用于退款、调整等关联场景）
    ADD COLUMN related_txn_id INT NULL COMMENT '关联交易ID（退款/调整时使用）',
    
    -- 备注信息
    ADD COLUMN remark VARCHAR(255) NULL COMMENT '交易备注',
    
    -- 操作员ID（预留字段，用于后台操作审计）
    ADD COLUMN operator_id VARCHAR(64) NULL COMMENT '操作员ID（后台操作时使用）',
    
    -- 卡片UID（与uid字段兼容，为未来扩展预留）
    ADD COLUMN card_uid VARCHAR(32) NULL COMMENT '卡片UID（与uid兼容）',
    
    -- 添加外键约束
    ADD CONSTRAINT fk_related_txn 
        FOREIGN KEY (related_txn_id) 
        REFERENCES transactions(id) 
        ON DELETE SET NULL;

-- 2. 修改 type 字段，扩展交易类型
-- 先删除旧的 ENUM 约束
ALTER TABLE transactions 
    MODIFY COLUMN type VARCHAR(20) NOT NULL;

-- 添加新的 CHECK 约束（MySQL 8.0.16+）
ALTER TABLE transactions
    ADD CONSTRAINT chk_transaction_type 
    CHECK (type IN (
        'recharge',  -- 充值
        'pay',       -- 支付
        'refund',    -- 退款
        'adjust',    -- 调整
        'issue',     -- 发卡
        'void',      -- 作废
        'expire'     -- 过期
    ));

-- 3. 修改金额字段：从 DECIMAL(10,2) 改为 INT（单位：分）
-- 注意：这会导致数据丢失，需要先备份或迁移数据
-- 如果有现有数据，请先执行数据迁移脚本

-- 备份现有数据到临时表
CREATE TABLE transactions_backup AS SELECT * FROM transactions;

-- 修改 amount 字段
ALTER TABLE transactions
    MODIFY COLUMN amount INT NOT NULL COMMENT '交易金额（分）';

-- 修改 balance_after 字段
ALTER TABLE transactions
    MODIFY COLUMN balance_after INT NOT NULL COMMENT '交易后余额（分）';

-- 4. 更新现有数据：将 balance_after 复制到 balance_before
-- 这是一个简化处理，实际应该根据历史数据计算
UPDATE transactions t1
LEFT JOIN (
    SELECT 
        id,
        LAG(balance_after) OVER (PARTITION BY uid ORDER BY created_at, id) as prev_balance
    FROM transactions
) t2 ON t1.id = t2.id
SET t1.balance_before = COALESCE(t2.prev_balance, 0);

-- 5. 同步 card_uid 字段（与 uid 保持一致）
UPDATE transactions SET card_uid = uid WHERE card_uid IS NULL;

-- 6. 修改 users 表的 balance 字段为 INT（单位：分）
ALTER TABLE users
    MODIFY COLUMN balance INT NOT NULL DEFAULT 0 COMMENT '账户余额（分）';

-- 7. 添加索引以优化查询性能
CREATE INDEX idx_transactions_card_uid ON transactions(card_uid);
CREATE INDEX idx_transactions_related_txn_id ON transactions(related_txn_id);
CREATE INDEX idx_transactions_operator_id ON transactions(operator_id);
CREATE INDEX idx_transactions_type_created ON transactions(type, created_at);

-- 8. 创建视图：兼容旧版本的查询（金额以元为单位）
CREATE OR REPLACE VIEW transactions_view AS
SELECT 
    id,
    uid,
    card_uid,
    type,
    amount / 100.0 AS amount_yuan,
    balance_before / 100.0 AS balance_before_yuan,
    balance_after / 100.0 AS balance_after_yuan,
    merchant_id,
    related_txn_id,
    remark,
    operator_id,
    created_at
FROM transactions;

-- 9. 创建审计触发器（可选）
DELIMITER $$

CREATE TRIGGER trg_transactions_audit
BEFORE INSERT ON transactions
FOR EACH ROW
BEGIN
    -- 确保 card_uid 与 uid 同步
    IF NEW.card_uid IS NULL THEN
        SET NEW.card_uid = NEW.uid;
    END IF;
    
    -- 验证金额为正数
    IF NEW.amount <= 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Transaction amount must be positive';
    END IF;
    
    -- 验证余额计算正确性
    IF NEW.type IN ('recharge', 'refund', 'adjust') THEN
        IF NEW.balance_after != NEW.balance_before + NEW.amount THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Balance calculation error for credit transaction';
        END IF;
    ELSEIF NEW.type IN ('pay', 'void', 'expire') THEN
        IF NEW.balance_after != NEW.balance_before - NEW.amount THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Balance calculation error for debit transaction';
        END IF;
    END IF;
END$$

DELIMITER ;

-- ============================================================================
-- 数据迁移说明
-- ============================================================================
-- 如果有现有数据需要迁移，请执行以下步骤：
--
-- 1. 备份数据库
--    mysqldump -u root -p nfc_wallet > backup_before_migration.sql
--
-- 2. 将现有金额从元转换为分（乘以100）
--    UPDATE transactions SET amount = amount * 100;
--    UPDATE transactions SET balance_after = balance_after * 100;
--    UPDATE users SET balance = balance * 100;
--
-- 3. 更新交易类型名称
--    UPDATE transactions SET type = 'pay' WHERE type = 'payment';
--
-- 4. 验证数据完整性
--    SELECT COUNT(*) FROM transactions WHERE amount <= 0;
--    SELECT COUNT(*) FROM transactions WHERE balance_after < 0;
--
-- ============================================================================

-- 完成迁移
SELECT 'Migration completed successfully' AS status;
