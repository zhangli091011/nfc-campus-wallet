-- ============================================================================
-- Drop All Tables Script
-- 清空数据库所有表、视图、存储过程
-- ============================================================================
-- 
-- 警告：此脚本会删除所有数据，请谨慎使用！
-- 建议在执行前先备份数据库：
-- mysqldump -u root -p nfc_wallet > backup_$(date +%Y%m%d_%H%M%S).sql
-- 
-- ============================================================================

USE nfc_wallet;

-- 禁用外键检查（允许删除有外键约束的表）
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================================
-- 1. 删除所有视图
-- ============================================================================

DROP VIEW IF EXISTS booth_transaction_stats;
DROP VIEW IF EXISTS product_sales_stats;
DROP VIEW IF EXISTS account_details_view;
DROP VIEW IF EXISTS users_legacy_view;
DROP VIEW IF EXISTS transactions_view;

-- ============================================================================
-- 2. 删除所有存储过程
-- ============================================================================

DROP PROCEDURE IF EXISTS sp_get_or_create_account;
DROP PROCEDURE IF EXISTS sp_get_booth_revenue;

-- ============================================================================
-- 3. 删除所有触发器
-- ============================================================================

DROP TRIGGER IF EXISTS trg_transactions_audit;
DROP TRIGGER IF EXISTS trg_validate_event_time;
DROP TRIGGER IF EXISTS trg_validate_event_time_update;
DROP TRIGGER IF EXISTS trg_validate_product_booth;

-- ============================================================================
-- 4. 删除所有表（按依赖关系倒序删除）
-- ============================================================================

-- 先删除依赖其他表的表
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS booths;
DROP TABLE IF EXISTS participants;
DROP TABLE IF EXISTS events;

-- 删除可能存在的备份表
DROP TABLE IF EXISTS transactions_backup;

-- ============================================================================
-- 5. 重新启用外键检查
-- ============================================================================

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- 6. 验证清空结果
-- ============================================================================

SELECT '========================================' AS divider;
SELECT 'All tables, views, and procedures dropped successfully!' AS status;
SELECT '========================================' AS divider;

-- 显示剩余的表（应该为空）
SELECT 'Remaining tables:' AS info;
SHOW TABLES;

SELECT '========================================' AS divider;
SELECT 'Database is now empty and ready for reinitialization.' AS message;
SELECT '========================================' AS divider;
