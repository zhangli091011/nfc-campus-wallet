-- ============================================================================
-- Migration: Add school_inspector role (校方巡查)
-- Description: 添加"校方巡查"角色，仅有只读查看权限，无法修改任何数据
-- Date: 2026-05-13
-- ============================================================================

-- 更新 users 表的 role 约束，添加 school_inspector 角色
ALTER TABLE users
    DROP CONSTRAINT IF EXISTS chk_user_role;

ALTER TABLE users
    ADD CONSTRAINT chk_user_role
        CHECK (role IN (
            'super_admin',
            'event_admin',
            'booth_cashier',
            'issuer',
            'reviewer',
            'bank_clerk',
            'merchant',
            'school_inspector'
        ));

-- 说明：
-- school_inspector 角色仅拥有 GET/HEAD/OPTIONS 类型请求的访问权限，
-- 可以查看所有后台数据（报表、交易流水、参与者余额、班级搜索等），
-- 但无法执行任何修改操作（POST/PUT/DELETE 会被拒绝）。
-- 权限控制在 core/security.py 的 RoleChecker 类中实现。
