-- Migration 004: Booth Collection Accounts
-- 为摊位添加收款账号功能
-- 
-- 功能：
-- 1. 为Participant表添加participant_type字段，区分普通参与者和收款账号
-- 2. 为Booth表添加collection_participant_id字段，关联收款账号
-- 3. 为现有摊位创建收款账号

-- ============================================================================
-- Step 1: 修改Participant表
-- ============================================================================

-- 添加participant_type字段
ALTER TABLE participants 
ADD COLUMN participant_type VARCHAR(20) DEFAULT 'person' NOT NULL;

-- 添加约束
ALTER TABLE participants
ADD CONSTRAINT chk_participant_type 
CHECK (participant_type IN ('person', 'booth_collection'));

-- 添加索引
CREATE INDEX idx_participants_type ON participants(participant_type);

-- 添加注释
COMMENT ON COLUMN participants.participant_type IS '参与者类型：person=普通参与者, booth_collection=摊位收款账号';

-- ============================================================================
-- Step 2: 修改Booth表
-- ============================================================================

-- 添加collection_participant_id字段
ALTER TABLE booths
ADD COLUMN collection_participant_id INTEGER;

-- 添加外键约束
ALTER TABLE booths
ADD CONSTRAINT fk_booth_collection_participant
FOREIGN KEY (collection_participant_id) 
REFERENCES participants(id) ON DELETE SET NULL;

-- 添加索引
CREATE INDEX idx_booths_collection_participant ON booths(collection_participant_id);

-- 添加注释
COMMENT ON COLUMN booths.collection_participant_id IS '收款账号的参与者ID';

-- ============================================================================
-- Step 3: 为现有摊位创建收款账号
-- ============================================================================

-- 注意：这个步骤需要在应用层执行，因为需要为每个摊位创建账户
-- 提供SQL模板供参考：

/*
-- 为单个摊位创建收款账号的SQL模板
DO $$
DECLARE
    booth_record RECORD;
    new_participant_id INTEGER;
    new_account_id INTEGER;
BEGIN
    -- 遍历所有摊位
    FOR booth_record IN 
        SELECT id, event_id, name, class_name 
        FROM booths 
        WHERE collection_participant_id IS NULL
    LOOP
        -- 创建收款参与者
        INSERT INTO participants (
            name, 
            card_uid, 
            participant_type, 
            status,
            created_at,
            updated_at
        ) VALUES (
            '【收款】' || booth_record.name,
            'BOOTH_' || booth_record.id,
            'booth_collection',
            'active',
            NOW(),
            NOW()
        ) RETURNING id INTO new_participant_id;
        
        -- 创建账户
        INSERT INTO accounts (
            participant_id,
            event_id,
            balance,
            created_at,
            updated_at
        ) VALUES (
            new_participant_id,
            booth_record.event_id,
            0,
            NOW(),
            NOW()
        ) RETURNING id INTO new_account_id;
        
        -- 更新摊位
        UPDATE booths 
        SET collection_participant_id = new_participant_id
        WHERE id = booth_record.id;
        
        RAISE NOTICE '为摊位 % (ID: %) 创建收款账号 (Participant ID: %, Account ID: %)', 
            booth_record.name, booth_record.id, new_participant_id, new_account_id;
    END LOOP;
END $$;
*/

-- ============================================================================
-- Step 4: 验证数据
-- ============================================================================

-- 查看参与者类型分布
SELECT 
    participant_type,
    COUNT(*) as count
FROM participants
GROUP BY participant_type;

-- 查看摊位收款账号关联情况
SELECT 
    b.id as booth_id,
    b.name as booth_name,
    b.collection_participant_id,
    p.name as collection_account_name,
    p.card_uid as collection_card_uid,
    a.balance as collection_balance
FROM booths b
LEFT JOIN participants p ON b.collection_participant_id = p.id
LEFT JOIN accounts a ON a.participant_id = p.id AND a.event_id = b.event_id
ORDER BY b.id;

-- ============================================================================
-- Rollback Script (如果需要回滚)
-- ============================================================================

/*
-- 删除收款账号相关的账户
DELETE FROM accounts 
WHERE participant_id IN (
    SELECT id FROM participants WHERE participant_type = 'booth_collection'
);

-- 删除收款账号参与者
DELETE FROM participants WHERE participant_type = 'booth_collection';

-- 删除Booth表的外键和字段
ALTER TABLE booths DROP CONSTRAINT IF EXISTS fk_booth_collection_participant;
ALTER TABLE booths DROP COLUMN IF EXISTS collection_participant_id;

-- 删除Participant表的约束和字段
DROP INDEX IF EXISTS idx_participants_type;
ALTER TABLE participants DROP CONSTRAINT IF EXISTS chk_participant_type;
ALTER TABLE participants DROP COLUMN IF EXISTS participant_type;
*/

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- 记录迁移
INSERT INTO schema_migrations (version, description, applied_at)
VALUES (
    '004',
    'Add booth collection accounts support',
    NOW()
) ON CONFLICT (version) DO NOTHING;
