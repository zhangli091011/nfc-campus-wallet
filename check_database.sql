-- ============================================================================
-- Database Integrity Check Script
-- 数据库完整性检查脚本
-- ============================================================================

USE nfc_wallet;

-- ============================================================================
-- 1. 数据库基本信息
-- ============================================================================

SELECT '========================================' AS divider;
SELECT 'DATABASE INFORMATION' AS section;
SELECT '========================================' AS divider;

SELECT 
    DATABASE() AS current_database,
    VERSION() AS mysql_version,
    NOW() AS check_time;

-- ============================================================================
-- 2. 表结构检查
-- ============================================================================

SELECT '========================================' AS divider;
SELECT 'TABLE STRUCTURE CHECK' AS section;
SELECT '========================================' AS divider;

-- 检查所有表是否存在
SELECT 'Checking required tables...' AS info;

SELECT 
    TABLE_NAME,
    ENGINE,
    TABLE_COLLATION,
    TABLE_ROWS,
    ROUND(DATA_LENGTH / 1024 / 1024, 2) AS data_size_mb,
    ROUND(INDEX_LENGTH / 1024 / 1024, 2) AS index_size_mb,
    CREATE_TIME,
    UPDATE_TIME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'nfc_wallet'
ORDER BY TABLE_NAME;

-- ============================================================================
-- 3. 必需字段检查
-- ============================================================================

SELECT '========================================' AS divider;
SELECT 'REQUIRED COLUMNS CHECK' AS section;
SELECT '========================================' AS divider;

-- 检查 participants 表的 participant_type 字段
SELECT 'Checking participants.participant_type...' AS info;
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN '✓ EXISTS'
        ELSE '✗ MISSING'
    END AS status,
    COLUMN_NAME,
    COLUMN_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'nfc_wallet'
    AND TABLE_NAME = 'participants'
    AND COLUMN_NAME = 'participant_type';

-- 检查 booths 表的 collection_participant_id 字段
SELECT 'Checking booths.collection_participant_id...' AS info;
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN '✓ EXISTS'
        ELSE '✗ MISSING'
    END AS status,
    COLUMN_NAME,
    COLUMN_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'nfc_wallet'
    AND TABLE_NAME = 'booths'
    AND COLUMN_NAME = 'collection_participant_id';

-- 检查 transactions 表的摊位相关字段
SELECT 'Checking transactions booth-related columns...' AS info;
SELECT 
    COLUMN_NAME,
    COLUMN_TYPE,
    IS_NULLABLE,
    CASE 
        WHEN COLUMN_NAME IN ('booth_id', 'product_id', 'operator_id') THEN '✓ EXISTS'
        ELSE '? UNKNOWN'
    END AS status
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'nfc_wallet'
    AND TABLE_NAME = 'transactions'
    AND COLUMN_NAME IN ('booth_id', 'product_id', 'operator_id')
ORDER BY COLUMN_NAME;

-- ============================================================================
-- 4. 外键约束检查
-- ============================================================================

SELECT '========================================' AS divider;
SELECT 'FOREIGN KEY CONSTRAINTS CHECK' AS section;
SELECT '========================================' AS divider;

SELECT 
    CONSTRAINT_NAME,
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME,
    '✓ OK' AS status
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'nfc_wallet'
    AND REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY TABLE_NAME, CONSTRAINT_NAME;

-- 检查关键外键是否存在
SELECT 'Checking critical foreign keys...' AS info;

SELECT 
    'fk_booth_collection_participant' AS constraint_name,
    CASE 
        WHEN COUNT(*) > 0 THEN '✓ EXISTS'
        ELSE '✗ MISSING'
    END AS status
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'nfc_wallet'
    AND CONSTRAINT_NAME = 'fk_booth_collection_participant'
UNION ALL
SELECT 
    'fk_transaction_booth' AS constraint_name,
    CASE 
        WHEN COUNT(*) > 0 THEN '✓ EXISTS'
        ELSE '✗ MISSING'
    END AS status
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'nfc_wallet'
    AND CONSTRAINT_NAME = 'fk_transaction_booth'
UNION ALL
SELECT 
    'fk_transaction_product' AS constraint_name,
    CASE 
        WHEN COUNT(*) > 0 THEN '✓ EXISTS'
        ELSE '✗ MISSING'
    END AS status
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'nfc_wallet'
    AND CONSTRAINT_NAME = 'fk_transaction_product'
UNION ALL
SELECT 
    'fk_transaction_operator' AS constraint_name,
    CASE 
        WHEN COUNT(*) > 0 THEN '✓ EXISTS'
        ELSE '✗ MISSING'
    END AS status
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'nfc_wallet'
    AND CONSTRAINT_NAME = 'fk_transaction_operator';

-- ============================================================================
-- 5. 索引检查
-- ============================================================================

SELECT '========================================' AS divider;
SELECT 'INDEX CHECK' AS section;
SELECT '========================================' AS divider;

SELECT 
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    NON_UNIQUE,
    SEQ_IN_INDEX,
    INDEX_TYPE
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = 'nfc_wallet'
ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;

-- 检查关键索引
SELECT 'Checking critical indexes...' AS info;

SELECT 
    'idx_participants_type' AS index_name,
    CASE 
        WHEN COUNT(*) > 0 THEN '✓ EXISTS'
        ELSE '✗ MISSING'
    END AS status
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = 'nfc_wallet'
    AND INDEX_NAME = 'idx_participants_type'
UNION ALL
SELECT 
    'idx_booths_collection_participant' AS index_name,
    CASE 
        WHEN COUNT(*) > 0 THEN '✓ EXISTS'
        ELSE '✗ MISSING'
    END AS status
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = 'nfc_wallet'
    AND INDEX_NAME = 'idx_booths_collection_participant';

-- ============================================================================
-- 6. 数据统计
-- ============================================================================

SELECT '========================================' AS divider;
SELECT 'DATA STATISTICS' AS section;
SELECT '========================================' AS divider;

-- 表记录数统计
SELECT 'Table record counts:' AS info;

SELECT 'events' AS table_name, COUNT(*) AS record_count FROM events
UNION ALL
SELECT 'participants', COUNT(*) FROM participants
UNION ALL
SELECT 'accounts', COUNT(*) FROM accounts
UNION ALL
SELECT 'booths', COUNT(*) FROM booths
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions;

-- 参与者类型分布
SELECT 'Participant type distribution:' AS info;
SELECT 
    participant_type,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM participants), 2) AS percentage
FROM participants
GROUP BY participant_type;

-- 摊位状态分布
SELECT 'Booth status distribution:' AS info;
SELECT 
    status,
    COUNT(*) AS count
FROM booths
GROUP BY status;

-- 用户角色分布
SELECT 'User role distribution:' AS info;
SELECT 
    role,
    COUNT(*) AS count
FROM users
GROUP BY role;

-- 交易类型分布
SELECT 'Transaction type distribution:' AS info;
SELECT 
    type,
    COUNT(*) AS count,
    SUM(amount) / 100.0 AS total_amount_yuan
FROM transactions
GROUP BY type;

-- ============================================================================
-- 7. 数据完整性检查
-- ============================================================================

SELECT '========================================' AS divider;
SELECT 'DATA INTEGRITY CHECK' AS section;
SELECT '========================================' AS divider;

-- 检查孤立的账户（没有对应参与者）
SELECT 'Checking orphaned accounts...' AS info;
SELECT 
    COUNT(*) AS orphaned_accounts,
    CASE 
        WHEN COUNT(*) = 0 THEN '✓ OK'
        ELSE '✗ FOUND ORPHANS'
    END AS status
FROM accounts a
LEFT JOIN participants p ON a.participant_id = p.id
WHERE p.id IS NULL;

-- 检查孤立的交易（没有对应账户）
SELECT 'Checking orphaned transactions...' AS info;
SELECT 
    COUNT(*) AS orphaned_transactions,
    CASE 
        WHEN COUNT(*) = 0 THEN '✓ OK'
        ELSE '✗ FOUND ORPHANS'
    END AS status
FROM transactions t
LEFT JOIN accounts a ON t.account_id = a.id
WHERE a.id IS NULL;

-- 检查摊位收款账户关联
SELECT 'Checking booth collection accounts...' AS info;
SELECT 
    COUNT(*) AS total_booths,
    SUM(CASE WHEN collection_participant_id IS NOT NULL THEN 1 ELSE 0 END) AS with_collection_account,
    SUM(CASE WHEN collection_participant_id IS NULL THEN 1 ELSE 0 END) AS without_collection_account,
    CASE 
        WHEN SUM(CASE WHEN collection_participant_id IS NULL THEN 1 ELSE 0 END) = 0 THEN '✓ ALL BOOTHS HAVE COLLECTION ACCOUNTS'
        ELSE '⚠ SOME BOOTHS MISSING COLLECTION ACCOUNTS'
    END AS status
FROM booths;

-- 检查负余额账户
SELECT 'Checking negative balance accounts...' AS info;
SELECT 
    COUNT(*) AS negative_balance_count,
    CASE 
        WHEN COUNT(*) = 0 THEN '✓ OK'
        ELSE '✗ FOUND NEGATIVE BALANCES'
    END AS status
FROM accounts
WHERE balance < 0;

-- 如果有负余额，显示详情
SELECT 'Negative balance accounts (if any):' AS info;
SELECT 
    a.id AS account_id,
    p.name AS participant_name,
    p.card_uid,
    a.balance / 100.0 AS balance_yuan,
    a.event_id
FROM accounts a
JOIN participants p ON a.participant_id = p.id
WHERE a.balance < 0
LIMIT 10;

-- 检查booth_cashier用户是否都有关联摊位
SELECT 'Checking booth_cashier users...' AS info;
SELECT 
    COUNT(*) AS total_cashiers,
    SUM(CASE WHEN booth_id IS NOT NULL THEN 1 ELSE 0 END) AS with_booth,
    SUM(CASE WHEN booth_id IS NULL THEN 1 ELSE 0 END) AS without_booth,
    CASE 
        WHEN SUM(CASE WHEN booth_id IS NULL THEN 1 ELSE 0 END) = 0 THEN '✓ ALL CASHIERS HAVE BOOTHS'
        ELSE '✗ SOME CASHIERS MISSING BOOTHS'
    END AS status
FROM users
WHERE role = 'booth_cashier';

-- ============================================================================
-- 8. 视图检查
-- ============================================================================

SELECT '========================================' AS divider;
SELECT 'VIEWS CHECK' AS section;
SELECT '========================================' AS divider;

SELECT 
    TABLE_NAME AS view_name,
    '✓ EXISTS' AS status
FROM INFORMATION_SCHEMA.VIEWS
WHERE TABLE_SCHEMA = 'nfc_wallet'
ORDER BY TABLE_NAME;

-- 检查关键视图
SELECT 'Checking critical views...' AS info;

SELECT 
    'booth_transaction_stats' AS view_name,
    CASE 
        WHEN COUNT(*) > 0 THEN '✓ EXISTS'
        ELSE '✗ MISSING'
    END AS status
FROM INFORMATION_SCHEMA.VIEWS
WHERE TABLE_SCHEMA = 'nfc_wallet'
    AND TABLE_NAME = 'booth_transaction_stats'
UNION ALL
SELECT 
    'product_sales_stats' AS view_name,
    CASE 
        WHEN COUNT(*) > 0 THEN '✓ EXISTS'
        ELSE '✗ MISSING'
    END AS status
FROM INFORMATION_SCHEMA.VIEWS
WHERE TABLE_SCHEMA = 'nfc_wallet'
    AND TABLE_NAME = 'product_sales_stats';

-- ============================================================================
-- 9. 管理员账户检查
-- ============================================================================

SELECT '========================================' AS divider;
SELECT 'ADMIN ACCOUNTS CHECK' AS section;
SELECT '========================================' AS divider;

SELECT 
    id,
    username,
    role,
    status,
    created_at,
    CASE 
        WHEN status = 'active' THEN '✓ ACTIVE'
        ELSE '⚠ NOT ACTIVE'
    END AS account_status
FROM users
WHERE role IN ('super_admin', 'event_admin')
ORDER BY role, username;

-- ============================================================================
-- 10. 活动状态检查
-- ============================================================================

SELECT '========================================' AS divider;
SELECT 'EVENTS STATUS CHECK' AS section;
SELECT '========================================' AS divider;

SELECT 
    id,
    name,
    start_date,
    end_date,
    status,
    allow_recharge,
    allow_payment,
    CASE 
        WHEN status = 'active' THEN '✓ ACTIVE'
        WHEN status = 'inactive' THEN '⚠ INACTIVE'
        ELSE '✗ CLOSED'
    END AS event_status,
    DATEDIFF(end_date, start_date) AS duration_days
FROM events
ORDER BY start_date DESC;

-- 检查是否有活动的活动
SELECT 'Active events check:' AS info;
SELECT 
    COUNT(*) AS active_event_count,
    CASE 
        WHEN COUNT(*) > 0 THEN '✓ HAS ACTIVE EVENTS'
        ELSE '⚠ NO ACTIVE EVENTS'
    END AS status
FROM events
WHERE status = 'active';

-- ============================================================================
-- 11. 总结
-- ============================================================================

SELECT '========================================' AS divider;
SELECT 'CHECK SUMMARY' AS section;
SELECT '========================================' AS divider;

SELECT 
    'Database Check Completed' AS summary,
    NOW() AS check_completed_at;

SELECT 'Review the results above for any issues marked with ✗ or ⚠' AS note;
SELECT 'All items marked with ✓ are OK' AS note;

SELECT '========================================' AS divider;
