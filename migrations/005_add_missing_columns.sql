-- ============================================================================
-- Migration 005: Add Missing Columns to Existing Database
-- 为现有数据库添加缺失的字段
-- ============================================================================

USE nfc_wallet;

-- ============================================================================
-- Step 1: 检查并添加 participant_type 字段到 participants 表
-- ============================================================================

-- 检查字段是否存在
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'nfc_wallet' 
    AND TABLE_NAME = 'participants' 
    AND COLUMN_NAME = 'participant_type'
);

-- 如果字段不存在，则添加
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE participants ADD COLUMN participant_type VARCHAR(20) NOT NULL DEFAULT ''person'' COMMENT ''参与者类型: person=普通参与者, booth_collection=摊位收款账号''',
    'SELECT ''Column participant_type already exists'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加约束（如果不存在）
SET @constraint_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
    WHERE TABLE_SCHEMA = 'nfc_wallet' 
    AND TABLE_NAME = 'participants' 
    AND CONSTRAINT_NAME = 'chk_participant_type'
);

SET @sql = IF(@constraint_exists = 0,
    'ALTER TABLE participants ADD CONSTRAINT chk_participant_type CHECK (participant_type IN (''person'', ''booth_collection''))',
    'SELECT ''Constraint chk_participant_type already exists'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加索引（如果不存在）
SET @idx_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = 'nfc_wallet' 
    AND TABLE_NAME = 'participants' 
    AND INDEX_NAME = 'idx_participants_type'
);

SET @sql = IF(@idx_exists = 0,
    'CREATE INDEX idx_participants_type ON participants(participant_type)',
    'SELECT ''Index idx_participants_type already exists'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ============================================================================
-- Step 2: 检查并添加 collection_participant_id 字段到 booths 表
-- ============================================================================

-- 检查字段是否存在
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'nfc_wallet' 
    AND TABLE_NAME = 'booths' 
    AND COLUMN_NAME = 'collection_participant_id'
);

-- 如果字段不存在，则添加
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE booths ADD COLUMN collection_participant_id INT DEFAULT NULL COMMENT ''收款参与者ID（用于摊位收款账户）''',
    'SELECT ''Column collection_participant_id already exists'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加外键约束（如果不存在）
SET @fk_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
    WHERE TABLE_SCHEMA = 'nfc_wallet' 
    AND TABLE_NAME = 'booths' 
    AND CONSTRAINT_NAME = 'fk_booth_collection_participant'
);

SET @sql = IF(@fk_exists = 0,
    'ALTER TABLE booths ADD CONSTRAINT fk_booth_collection_participant FOREIGN KEY (collection_participant_id) REFERENCES participants(id) ON DELETE SET NULL',
    'SELECT ''Foreign key fk_booth_collection_participant already exists'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加索引（如果不存在）
SET @idx_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = 'nfc_wallet' 
    AND TABLE_NAME = 'booths' 
    AND INDEX_NAME = 'idx_booths_collection_participant'
);

SET @sql = IF(@idx_exists = 0,
    'CREATE INDEX idx_booths_collection_participant ON booths(collection_participant_id)',
    'SELECT ''Index idx_booths_collection_participant already exists'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ============================================================================
-- Step 3: 验证修改
-- ============================================================================

SELECT '========================================' AS divider;
SELECT 'Migration 005 completed successfully!' AS status;
SELECT '========================================' AS divider;

-- 显示 participants 表结构
SELECT 'Participants table structure:' AS info;
DESCRIBE participants;

SELECT '========================================' AS divider;

-- 显示 booths 表结构
SELECT 'Booths table structure:' AS info;
DESCRIBE booths;

SELECT '========================================' AS divider;

-- 显示参与者类型分布
SELECT 'Participant type distribution:' AS info;
SELECT 
    participant_type,
    COUNT(*) as count
FROM participants
GROUP BY participant_type;

SELECT '========================================' AS divider;

-- 显示摊位收款账号关联情况
SELECT 'Booth collection account status:' AS info;
SELECT 
    COUNT(*) as total_booths,
    SUM(CASE WHEN collection_participant_id IS NOT NULL THEN 1 ELSE 0 END) as booths_with_collection_account,
    SUM(CASE WHEN collection_participant_id IS NULL THEN 1 ELSE 0 END) as booths_without_collection_account
FROM booths;

SELECT '========================================' AS divider;
SELECT 'Migration completed!' AS status;
