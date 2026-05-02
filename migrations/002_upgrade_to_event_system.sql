-- ============================================================================
-- Migration: Upgrade to Event-Based Quota System (活动额度系统)
-- Description: 将基础钱包升级为学校单场活动额度系统
-- Date: 2026-05-01
-- ============================================================================

-- 1. 创建 events 表（活动表）
CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '活动ID',
    name VARCHAR(255) NOT NULL COMMENT '活动名称',
    start_time DATETIME NOT NULL COMMENT '活动开始时间',
    end_time DATETIME NOT NULL COMMENT '活动结束时间',
    status VARCHAR(20) NOT NULL DEFAULT 'draft' COMMENT '活动状态: draft/active/paused/ended',
    recharge_enabled BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否允许充值',
    consume_enabled BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否允许消费',
    expire_rule VARCHAR(50) DEFAULT 'event_end' COMMENT '过期规则: event_end/never/custom',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX idx_status (status),
    INDEX idx_start_time (start_time),
    INDEX idx_end_time (end_time),
    
    -- 约束
    CONSTRAINT chk_event_status CHECK (status IN ('draft', 'active', 'paused', 'ended')),
    CONSTRAINT chk_event_time CHECK (end_time > start_time),
    CONSTRAINT chk_expire_rule CHECK (expire_rule IN ('event_end', 'never', 'custom'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='活动表';

-- 2. 创建 participants 表（参与者表）
CREATE TABLE IF NOT EXISTS participants (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '参与者ID',
    name VARCHAR(100) NOT NULL COMMENT '参与者姓名',
    class_name VARCHAR(100) DEFAULT NULL COMMENT '班级名称',
    student_no VARCHAR(50) DEFAULT NULL COMMENT '学号',
    card_uid VARCHAR(32) UNIQUE NOT NULL COMMENT 'NFC卡片UID（唯一）',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '状态: active/inactive/blocked',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX idx_card_uid (card_uid),
    INDEX idx_student_no (student_no),
    INDEX idx_status (status),
    INDEX idx_name (name),
    
    -- 约束
    CONSTRAINT chk_participant_status CHECK (status IN ('active', 'inactive', 'blocked'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='参与者表';

-- 3. 创建 accounts 表（活动账户表）
CREATE TABLE IF NOT EXISTS accounts (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '账户ID',
    participant_id INT NOT NULL COMMENT '参与者ID',
    event_id INT NOT NULL COMMENT '活动ID',
    balance INT NOT NULL DEFAULT 0 COMMENT '账户余额（分）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 外键
    CONSTRAINT fk_account_participant FOREIGN KEY (participant_id) 
        REFERENCES participants(id) ON DELETE CASCADE,
    CONSTRAINT fk_account_event FOREIGN KEY (event_id) 
        REFERENCES events(id) ON DELETE CASCADE,
    
    -- 唯一约束：一个参与者在一个活动下只能有一个账户
    CONSTRAINT uk_participant_event UNIQUE (participant_id, event_id),
    
    -- 索引
    INDEX idx_participant_id (participant_id),
    INDEX idx_event_id (event_id),
    INDEX idx_balance (balance),
    
    -- 约束
    CONSTRAINT chk_account_balance CHECK (balance >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='活动账户表';

-- 4. 修改 transactions 表，添加活动关联
ALTER TABLE transactions
    -- 添加活动和参与者关联
    ADD COLUMN event_id INT DEFAULT NULL COMMENT '活动ID' AFTER uid,
    ADD COLUMN participant_id INT DEFAULT NULL COMMENT '参与者ID' AFTER event_id,
    ADD COLUMN account_id INT DEFAULT NULL COMMENT '账户ID' AFTER participant_id,
    
    -- 添加外键约束
    ADD CONSTRAINT fk_transaction_event 
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE SET NULL,
    ADD CONSTRAINT fk_transaction_participant 
        FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE SET NULL,
    ADD CONSTRAINT fk_transaction_account 
        FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL,
    
    -- 添加索引
    ADD INDEX idx_event_id (event_id),
    ADD INDEX idx_participant_id (participant_id),
    ADD INDEX idx_account_id (account_id);

-- 5. 创建视图：兼容旧版 users 表查询
CREATE OR REPLACE VIEW users_legacy_view AS
SELECT 
    p.id,
    p.card_uid AS uid,
    COALESCE(SUM(a.balance), 0) AS balance,
    p.created_at
FROM participants p
LEFT JOIN accounts a ON p.id = a.participant_id
GROUP BY p.id, p.card_uid, p.created_at;

-- 6. 创建视图：活动账户详情
CREATE OR REPLACE VIEW account_details_view AS
SELECT 
    a.id AS account_id,
    a.balance / 100.0 AS balance_yuan,
    p.id AS participant_id,
    p.name AS participant_name,
    p.card_uid,
    p.student_no,
    p.class_name,
    e.id AS event_id,
    e.name AS event_name,
    e.status AS event_status,
    e.start_time,
    e.end_time,
    a.created_at,
    a.updated_at
FROM accounts a
INNER JOIN participants p ON a.participant_id = p.id
INNER JOIN events e ON a.event_id = e.id;

-- 7. 创建触发器：验证活动时间有效性
DELIMITER $$

CREATE TRIGGER trg_validate_event_time
BEFORE INSERT ON events
FOR EACH ROW
BEGIN
    IF NEW.end_time <= NEW.start_time THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Event end_time must be after start_time';
    END IF;
END$$

CREATE TRIGGER trg_validate_event_time_update
BEFORE UPDATE ON events
FOR EACH ROW
BEGIN
    IF NEW.end_time <= NEW.start_time THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Event end_time must be after start_time';
    END IF;
END$$

DELIMITER ;

-- 8. 创建存储过程：自动创建账户
DELIMITER $$

CREATE PROCEDURE sp_get_or_create_account(
    IN p_participant_id INT,
    IN p_event_id INT,
    OUT p_account_id INT,
    OUT p_balance INT
)
BEGIN
    DECLARE v_account_id INT;
    DECLARE v_balance INT;
    
    -- 尝试获取现有账户
    SELECT id, balance INTO v_account_id, v_balance
    FROM accounts
    WHERE participant_id = p_participant_id AND event_id = p_event_id
    LIMIT 1;
    
    -- 如果账户不存在，创建新账户
    IF v_account_id IS NULL THEN
        INSERT INTO accounts (participant_id, event_id, balance)
        VALUES (p_participant_id, p_event_id, 0);
        
        SET v_account_id = LAST_INSERT_ID();
        SET v_balance = 0;
    END IF;
    
    -- 返回结果
    SET p_account_id = v_account_id;
    SET p_balance = v_balance;
END$$

DELIMITER ;

-- 9. 数据迁移：将现有 users 迁移到 participants
-- 注意：这会将现有用户转换为参与者，但不会自动创建活动和账户
-- 需要手动创建活动后，再为参与者创建账户

INSERT INTO participants (name, card_uid, status, created_at)
SELECT 
    CONCAT('User_', uid) AS name,  -- 默认名称
    uid AS card_uid,
    'active' AS status,
    created_at
FROM users
WHERE NOT EXISTS (
    SELECT 1 FROM participants WHERE card_uid = users.uid
);

-- 10. 创建默认活动（可选）
-- 如果需要为现有数据创建默认活动，取消注释以下代码

/*
INSERT INTO events (name, start_time, end_time, status, recharge_enabled, consume_enabled)
VALUES (
    '默认活动',
    NOW(),
    DATE_ADD(NOW(), INTERVAL 1 YEAR),
    'active',
    TRUE,
    TRUE
);

-- 为所有参与者在默认活动下创建账户
INSERT INTO accounts (participant_id, event_id, balance)
SELECT 
    p.id,
    (SELECT id FROM events WHERE name = '默认活动' LIMIT 1),
    u.balance
FROM participants p
INNER JOIN users u ON p.card_uid = u.uid
WHERE NOT EXISTS (
    SELECT 1 FROM accounts 
    WHERE participant_id = p.id 
    AND event_id = (SELECT id FROM events WHERE name = '默认活动' LIMIT 1)
);
*/

-- ============================================================================
-- 索引优化建议
-- ============================================================================

-- 复合索引：优化常见查询
CREATE INDEX idx_accounts_participant_event ON accounts(participant_id, event_id);
CREATE INDEX idx_transactions_event_participant ON transactions(event_id, participant_id);
CREATE INDEX idx_transactions_account_created ON transactions(account_id, created_at);

-- 覆盖索引：优化余额查询
CREATE INDEX idx_accounts_event_balance ON accounts(event_id, balance);

-- ============================================================================
-- 数据完整性检查
-- ============================================================================

-- 检查参与者数量
SELECT COUNT(*) AS participant_count FROM participants;

-- 检查活动数量
SELECT COUNT(*) AS event_count FROM events;

-- 检查账户数量
SELECT COUNT(*) AS account_count FROM accounts;

-- 检查孤立的交易记录（没有关联活动的）
SELECT COUNT(*) AS orphan_transaction_count 
FROM transactions 
WHERE event_id IS NULL;

-- ============================================================================
-- 完成迁移
-- ============================================================================

SELECT 'Event system migration completed successfully' AS status;
