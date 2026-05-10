-- ============================================================================
-- Migration: Add bank_clerk role (投资办理员角色)
-- Description: 新增专用角色 bank_clerk 用于官方中央银行 - 投资办理终端
-- Date: 2026-05-09
-- ============================================================================

-- MySQL 不支持直接修改 CHECK 约束，需要先删除再添加
ALTER TABLE users DROP CHECK chk_user_role;

ALTER TABLE users ADD CONSTRAINT chk_user_role
    CHECK (role IN ('super_admin', 'event_admin', 'booth_cashier', 'issuer', 'reviewer', 'bank_clerk'));

-- 验证
SELECT 'bank_clerk role added to users.role CHECK constraint' AS status;
