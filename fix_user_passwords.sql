-- ============================================================================
-- 修复用户密码哈希
-- Fix User Password Hashes
-- ============================================================================
-- 
-- 问题: create_test_data.sql 中的密码哈希不正确，无法验证
-- 解决: 使用正确生成的 bcrypt 哈希更新所有用户密码
--
-- 密码说明:
--   - admin 用户: admin123
--   - 其他用户 (收银员、充值员): cashier123
-- ============================================================================

USE nfc_wallet;

-- 更新 admin 用户密码 (密码: admin123)
UPDATE users 
SET password_hash = '$2b$12$14BtTTqR5hA8SiGciAp89uvy.09EtoZnz7zt8cGTZDyezaYfMSPrq'
WHERE username = 'admin';

-- 更新所有收银员和充值员密码 (密码: cashier123)
UPDATE users 
SET password_hash = '$2b$12$8Juz3NGP7Emas/knJW6gxuZMAJKjdQ925q3toBZkcU1vxgb9i7Q3O'
WHERE role IN ('booth_cashier', 'issuer', 'reviewer');

-- 验证更新结果
SELECT 
    '✓ 密码哈希已更新' AS status,
    COUNT(*) AS updated_users
FROM users;

SELECT 
    username,
    role,
    LEFT(password_hash, 20) AS password_hash_prefix,
    CASE 
        WHEN username = 'admin' THEN 'admin123'
        ELSE 'cashier123'
    END AS password
FROM users
ORDER BY role, username;

