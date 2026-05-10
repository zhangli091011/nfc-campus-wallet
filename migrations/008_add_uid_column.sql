-- Migration 008: Add uid column to transactions table
-- Date: 2026-05-09
-- Description: Add missing uid column for legacy compatibility

USE nfc_wallet;

-- Check if uid column exists, if not add it
SET @col_exists = 0;
SELECT COUNT(*) INTO @col_exists 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'nfc_wallet' 
  AND TABLE_NAME = 'transactions' 
  AND COLUMN_NAME = 'uid';

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE transactions ADD COLUMN uid VARCHAR(32) NULL AFTER id, ADD INDEX idx_transactions_uid (uid)',
    'SELECT "Column uid already exists" AS message');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Verify the change
DESCRIBE transactions;

SELECT 'Migration 008 completed successfully' AS status;
