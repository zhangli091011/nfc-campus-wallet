-- Create Admin User SQL Script
-- 
-- This script creates a super_admin user directly in the database.
-- Username: admin
-- Password: admin123
--
-- Usage on server:
--   mysql -u your_user -p nfc < create_admin.sql
--   OR
--   mysql -u your_user -p nfc_wallet < create_admin.sql
--

-- Insert admin user
INSERT INTO users (username, password_hash, role, status, created_at, updated_at)
VALUES (
    'admin',
    '$2b$12$1k1YoueJ786gm.O139qqmuhSI.QsMPl.evIZycDYJYnV2afo7MGvK',
    'super_admin',
    'active',
    NOW(),
    NOW()
)
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    role = VALUES(role),
    status = VALUES(status),
    updated_at = NOW();

-- Verify the user was created
SELECT id, username, role, status, created_at 
FROM users 
WHERE username = 'admin';
