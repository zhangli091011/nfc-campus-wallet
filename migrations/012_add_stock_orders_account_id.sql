-- ============================================
-- Migration 012: 为 stock_orders 表添加 account_id 列
-- 
-- 修复：ORM 模型中定义了 account_id 但数据库表中缺失
-- ============================================

-- 添加 account_id 列（如果不存在）
SET @col_exists = (
    SELECT COUNT(*) FROM information_schema.columns 
    WHERE table_schema = DATABASE() 
    AND table_name = 'stock_orders' 
    AND column_name = 'account_id'
);

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE stock_orders ADD COLUMN account_id INT NULL COMMENT ''关联的活动账户ID'' AFTER participant_id',
    'SELECT ''account_id column already exists''');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 回填 account_id（将已有订单关联到对应账户）
UPDATE stock_orders so
    JOIN accounts a ON a.participant_id = so.participant_id AND a.event_id = so.event_id
    SET so.account_id = a.id
    WHERE so.account_id IS NULL;
