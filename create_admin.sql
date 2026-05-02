-- Create Admin User SQL Script
-- 
-- This script creates a super_admin user directly in the database.
-- Username: admin
-- Password: admin123
--
-- Usage on server:
--   mysql -u your_user -p nfc_wallet < create_admin.sql
--

-- Insert admin user
INSERT INTO users (username, hashed_password, role, is_active, created_at)
VALUES (
    'admin',
    '$2b$12$1k1YoueJ786gm.O139qqmuhSI.QsMPl.evIZycDYJYnV2afo7MGvK',
    'super_admin',
    1,
    NOW()
)
ON DUPLICATE KEY UPDATE
    hashed_password = VALUES(hashed_password),
    role = VALUES(role),
    is_active = VALUES(is_active);

-- Verify the user was created
SELECT id, username, role, is_active, created_at 
FROM users 
WHERE username = 'admin';
