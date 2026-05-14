-- Migration 015: Allow NULL for participant_id and account_id in transactions
-- 现金收款不关联参与者和账户，需要允许这两个字段为 NULL
-- 使用动态查找外键名称以兼容不同环境

-- 删除 participant_id 外键
SET @fk_name = (
    SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'transactions' 
    AND COLUMN_NAME = 'participant_id' 
    AND REFERENCED_TABLE_NAME = 'participants'
    LIMIT 1
);
SET @sql = IF(@fk_name IS NOT NULL, 
    CONCAT('ALTER TABLE transactions DROP FOREIGN KEY ', @fk_name), 
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 删除 account_id 外键
SET @fk_name2 = (
    SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'transactions' 
    AND COLUMN_NAME = 'account_id' 
    AND REFERENCED_TABLE_NAME = 'accounts'
    LIMIT 1
);
SET @sql2 = IF(@fk_name2 IS NOT NULL, 
    CONCAT('ALTER TABLE transactions DROP FOREIGN KEY ', @fk_name2), 
    'SELECT 1');
PREPARE stmt2 FROM @sql2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

-- 修改列允许 NULL
ALTER TABLE transactions 
    MODIFY COLUMN participant_id INT NULL COMMENT '参与者ID（现金收款时为NULL）',
    MODIFY COLUMN account_id INT NULL COMMENT '账户ID（现金收款时为NULL）';

-- 重新添加外键约束（允许 NULL 值）
ALTER TABLE transactions 
    ADD CONSTRAINT fk_transaction_participant 
        FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE;

ALTER TABLE transactions 
    ADD CONSTRAINT fk_transaction_account 
        FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;
