-- 检查和创建测试数据
-- 用于排查"活动信息加载失败"问题

-- 1. 检查活动表
SELECT 'Checking events table...' AS status;
SELECT * FROM events;

-- 2. 检查摊位表
SELECT 'Checking booths table...' AS status;
SELECT * FROM booths;

-- 3. 如果没有活动，创建一个测试活动
INSERT INTO events (name, start_time, end_time, status, recharge_enabled, consume_enabled, expire_rule, created_at, updated_at)
SELECT 
    '测试活动',
    NOW(),
    DATE_ADD(NOW(), INTERVAL 7 DAY),
    'active',
    TRUE,
    TRUE,
    'event_end',
    NOW(),
    NOW()
WHERE NOT EXISTS (SELECT 1 FROM events WHERE status = 'active');

-- 4. 获取活动ID
SET @event_id = (SELECT id FROM events WHERE status = 'active' LIMIT 1);

-- 5. 如果没有摊位，创建一个测试摊位
INSERT INTO booths (event_id, name, description, status, created_at, updated_at)
SELECT 
    @event_id,
    '测试摊位',
    '用于测试的摊位',
    'active',
    NOW(),
    NOW()
WHERE NOT EXISTS (SELECT 1 FROM booths WHERE event_id = @event_id);

-- 6. 显示创建的数据
SELECT 'Created/Existing data:' AS status;
SELECT 
    e.id AS event_id,
    e.name AS event_name,
    e.status AS event_status,
    b.id AS booth_id,
    b.name AS booth_name,
    b.status AS booth_status
FROM events e
LEFT JOIN booths b ON e.id = b.event_id
WHERE e.status = 'active';

-- 7. 检查用户表（确保有可以登录的用户）
SELECT 'Checking users table...' AS status;
SELECT id, username, role, is_active FROM users;
