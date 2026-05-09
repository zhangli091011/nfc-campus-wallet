-- ============================================================================
-- Create Test Data for NFC Campus Wallet
-- 创建测试数据
-- ============================================================================

USE nfc_wallet;

-- ============================================================================
-- 1. 创建测试活动
-- ============================================================================

INSERT INTO events (name, start_date, end_date, status, allow_recharge, allow_payment)
VALUES 
    ('2026春季校园美食节', '2026-05-01', '2026-05-31', 'active', 1, 1),
    ('2026秋季运动会', '2026-09-01', '2026-09-30', 'inactive', 1, 1);

-- 获取活动ID
SET @event_id = (SELECT id FROM events WHERE name = '2026春季校园美食节' LIMIT 1);

SELECT CONCAT('✓ 创建活动成功，活动ID: ', @event_id) AS status;

-- ============================================================================
-- 2. 创建测试参与者（学生）
-- ============================================================================

INSERT INTO participants (name, card_uid, class_name, student_no, participant_type, status)
VALUES 
    ('张三', 'A1B2C3D4', '高一(1)班', '2024001', 'person', 'active'),
    ('李四', 'E5F6G7H8', '高一(2)班', '2024002', 'person', 'active'),
    ('王五', 'I9J0K1L2', '高二(1)班', '2023001', 'person', 'active'),
    ('赵六', 'M3N4O5P6', '高二(2)班', '2023002', 'person', 'active'),
    ('钱七', 'Q7R8S9T0', '高三(1)班', '2022001', 'person', 'active');

SELECT '✓ 创建5个测试参与者成功' AS status;

-- ============================================================================
-- 3. 为参与者创建账户并充值
-- ============================================================================

-- 为每个参与者创建账户
INSERT INTO accounts (participant_id, event_id, balance)
SELECT id, @event_id, 10000  -- 初始余额100元（10000分）
FROM participants 
WHERE participant_type = 'person';

SELECT '✓ 为参与者创建账户成功，初始余额: ¥100' AS status;

-- ============================================================================
-- 4. 创建测试摊位
-- ============================================================================

INSERT INTO booths (event_id, name, class_name, status)
VALUES 
    (@event_id, '美味奶茶铺', '高一(1)班', 'active'),
    (@event_id, '特色小吃摊', '高一(2)班', 'active'),
    (@event_id, '创意甜品站', '高二(1)班', 'active'),
    (@event_id, '健康果汁吧', '高二(2)班', 'active'),
    (@event_id, '传统糕点屋', '高三(1)班', 'active');

SELECT '✓ 创建5个测试摊位成功' AS status;

-- ============================================================================
-- 5. 为每个摊位创建收款账户
-- ============================================================================

-- 为每个摊位创建收款参与者
INSERT INTO participants (name, card_uid, participant_type, status)
SELECT 
    CONCAT('【收款】', name),
    CONCAT('BOOTH_', id),
    'booth_collection',
    'active'
FROM booths
WHERE event_id = @event_id;

-- 为收款参与者创建账户
INSERT INTO accounts (participant_id, event_id, balance)
SELECT p.id, @event_id, 0
FROM participants p
WHERE p.participant_type = 'booth_collection'
AND p.card_uid LIKE 'BOOTH_%';

-- 关联摊位和收款账户
UPDATE booths b
INNER JOIN participants p ON p.card_uid = CONCAT('BOOTH_', b.id)
SET b.collection_participant_id = p.id
WHERE b.event_id = @event_id;

SELECT '✓ 为摊位创建收款账户成功' AS status;

-- ============================================================================
-- 6. 创建测试商品
-- ============================================================================

-- 美味奶茶铺的商品
SET @booth1_id = (SELECT id FROM booths WHERE name = '美味奶茶铺' LIMIT 1);
INSERT INTO products (booth_id, name, price, cost_price, stock, enabled)
VALUES 
    (@booth1_id, '珍珠奶茶', 1200, 600, 50, 1),
    (@booth1_id, '芝士奶盖', 1500, 700, 30, 1),
    (@booth1_id, '水果茶', 1000, 500, 40, 1);

-- 特色小吃摊的商品
SET @booth2_id = (SELECT id FROM booths WHERE name = '特色小吃摊' LIMIT 1);
INSERT INTO products (booth_id, name, price, cost_price, stock, enabled)
VALUES 
    (@booth2_id, '章鱼小丸子', 800, 400, 100, 1),
    (@booth2_id, '臭豆腐', 1000, 500, 50, 1),
    (@booth2_id, '烤串拼盘', 1500, 800, 30, 1);

-- 创意甜品站的商品
SET @booth3_id = (SELECT id FROM booths WHERE name = '创意甜品站' LIMIT 1);
INSERT INTO products (booth_id, name, price, cost_price, stock, enabled)
VALUES 
    (@booth3_id, '芒果班戟', 1800, 900, 20, 1),
    (@booth3_id, '提拉米苏', 2000, 1000, 15, 1),
    (@booth3_id, '抹茶蛋糕', 1600, 800, 25, 1);

-- 健康果汁吧的商品
SET @booth4_id = (SELECT id FROM booths WHERE name = '健康果汁吧' LIMIT 1);
INSERT INTO products (booth_id, name, price, cost_price, stock, enabled)
VALUES 
    (@booth4_id, '鲜榨橙汁', 1200, 600, 50, 1),
    (@booth4_id, '西瓜汁', 1000, 500, 40, 1),
    (@booth4_id, '混合果汁', 1500, 700, 30, 1);

-- 传统糕点屋的商品
SET @booth5_id = (SELECT id FROM booths WHERE name = '传统糕点屋' LIMIT 1);
INSERT INTO products (booth_id, name, price, cost_price, stock, enabled)
VALUES 
    (@booth5_id, '绿豆糕', 600, 300, 100, 1),
    (@booth5_id, '桂花糕', 800, 400, 80, 1),
    (@booth5_id, '凤梨酥', 1000, 500, 60, 1);

SELECT '✓ 创建18个测试商品成功' AS status;

-- ============================================================================
-- 7. 创建测试用户（收银员）
-- ============================================================================

-- 为每个摊位创建一个收银员账户
-- 密码都是: cashier123
-- 密码哈希: $2b$12$8Juz3NGP7Emas/knJW6gxuZMAJKjdQ925q3toBZkcU1vxgb9i7Q3O

INSERT INTO users (username, password_hash, role, booth_id, status)
VALUES 
    ('booth1_cashier', '$2b$12$8Juz3NGP7Emas/knJW6gxuZMAJKjdQ925q3toBZkcU1vxgb9i7Q3O', 'booth_cashier', @booth1_id, 'active'),
    ('booth2_cashier', '$2b$12$8Juz3NGP7Emas/knJW6gxuZMAJKjdQ925q3toBZkcU1vxgb9i7Q3O', 'booth_cashier', @booth2_id, 'active'),
    ('booth3_cashier', '$2b$12$8Juz3NGP7Emas/knJW6gxuZMAJKjdQ925q3toBZkcU1vxgb9i7Q3O', 'booth_cashier', @booth3_id, 'active'),
    ('booth4_cashier', '$2b$12$8Juz3NGP7Emas/knJW6gxuZMAJKjdQ925q3toBZkcU1vxgb9i7Q3O', 'booth_cashier', @booth4_id, 'active'),
    ('booth5_cashier', '$2b$12$8Juz3NGP7Emas/knJW6gxuZMAJKjdQ925q3toBZkcU1vxgb9i7Q3O', 'booth_cashier', @booth5_id, 'active');

-- 创建一个充值员账户
INSERT INTO users (username, password_hash, role, booth_id, status)
VALUES 
    ('issuer1', '$2b$12$8Juz3NGP7Emas/knJW6gxuZMAJKjdQ925q3toBZkcU1vxgb9i7Q3O', 'issuer', NULL, 'active');

SELECT '✓ 创建6个测试用户成功（5个收银员 + 1个充值员）' AS status;

-- ============================================================================
-- 8. 创建一些测试交易记录
-- ============================================================================

-- 张三在美味奶茶铺买了珍珠奶茶
SET @participant1_id = (SELECT id FROM participants WHERE name = '张三' LIMIT 1);
SET @account1_id = (SELECT id FROM accounts WHERE participant_id = @participant1_id AND event_id = @event_id LIMIT 1);
SET @product1_id = (SELECT id FROM products WHERE name = '珍珠奶茶' LIMIT 1);
SET @operator1_id = (SELECT id FROM users WHERE username = 'booth1_cashier' LIMIT 1);

INSERT INTO transactions (type, amount, balance_before, balance_after, participant_id, event_id, account_id, booth_id, product_id, operator_id, remark)
VALUES 
    ('pay', 1200, 10000, 8800, @participant1_id, @event_id, @account1_id, @booth1_id, @product1_id, @operator1_id, '购买珍珠奶茶');

-- 更新张三的余额
UPDATE accounts SET balance = 8800 WHERE id = @account1_id;

-- 李四在特色小吃摊买了章鱼小丸子
SET @participant2_id = (SELECT id FROM participants WHERE name = '李四' LIMIT 1);
SET @account2_id = (SELECT id FROM accounts WHERE participant_id = @participant2_id AND event_id = @event_id LIMIT 1);
SET @product2_id = (SELECT id FROM products WHERE name = '章鱼小丸子' LIMIT 1);
SET @operator2_id = (SELECT id FROM users WHERE username = 'booth2_cashier' LIMIT 1);

INSERT INTO transactions (type, amount, balance_before, balance_after, participant_id, event_id, account_id, booth_id, product_id, operator_id, remark)
VALUES 
    ('pay', 800, 10000, 9200, @participant2_id, @event_id, @account2_id, @booth2_id, @product2_id, @operator2_id, '购买章鱼小丸子');

-- 更新李四的余额
UPDATE accounts SET balance = 9200 WHERE id = @account2_id;

SELECT '✓ 创建2笔测试交易记录成功' AS status;

-- ============================================================================
-- 9. 显示测试数据摘要
-- ============================================================================

SELECT '========================================' AS divider;
SELECT '测试数据创建完成！' AS summary;
SELECT '========================================' AS divider;

SELECT '活动信息:' AS info;
SELECT id, name, start_date, end_date, status FROM events WHERE status = 'active';

SELECT '========================================' AS divider;
SELECT '摊位信息:' AS info;
SELECT id, name, class_name, status FROM booths WHERE event_id = @event_id;

SELECT '========================================' AS divider;
SELECT '参与者信息:' AS info;
SELECT id, name, card_uid, class_name, participant_type FROM participants WHERE participant_type = 'person';

SELECT '========================================' AS divider;
SELECT '账户余额:' AS info;
SELECT 
    p.name AS participant_name,
    p.card_uid,
    a.balance / 100.0 AS balance_yuan
FROM accounts a
JOIN participants p ON a.participant_id = p.id
WHERE p.participant_type = 'person'
ORDER BY p.name;

SELECT '========================================' AS divider;
SELECT '商品信息（前10个）:' AS info;
SELECT 
    b.name AS booth_name,
    p.name AS product_name,
    p.price / 100.0 AS price_yuan,
    p.stock,
    p.enabled
FROM products p
JOIN booths b ON p.booth_id = b.id
LIMIT 10;

SELECT '========================================' AS divider;
SELECT '用户账户:' AS info;
SELECT username, role, booth_id, status FROM users ORDER BY role, username;

SELECT '========================================' AS divider;
SELECT '登录凭据:' AS credentials;
SELECT '管理员账户:' AS account_type;
SELECT '  用户名: admin' AS info;
SELECT '  密码: admin123' AS info;
SELECT '' AS blank;
SELECT '收银员账户（任选一个）:' AS account_type;
SELECT '  用户名: booth1_cashier ~ booth5_cashier' AS info;
SELECT '  密码: cashier123' AS info;
SELECT '' AS blank;
SELECT '充值员账户:' AS account_type;
SELECT '  用户名: issuer1' AS info;
SELECT '  密码: cashier123' AS info;
SELECT '' AS blank;
SELECT '测试卡片（用于NFC刷卡）:' AS card_info;
SELECT '  张三: A1B2C3D4' AS info;
SELECT '  李四: E5F6G7H8' AS info;
SELECT '  王五: I9J0K1L2' AS info;
SELECT '  赵六: M3N4O5P6' AS info;
SELECT '  钱七: Q7R8S9T0' AS info;

SELECT '========================================' AS divider;
SELECT '✓ 测试数据创建完成！' AS final_status;
SELECT '现在可以使用安卓应用进行测试了' AS next_step;
