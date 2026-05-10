-- ============================================================================
-- Migration: Merchant Self-Registration System (商户自主注册系统)
-- Description: 添加 merchant 角色支持，允许商户自主注册、管理商铺和查看收入
-- Date: 2026-05-10
-- ============================================================================

-- 1. 更新 users 表的 role 约束，添加 merchant 角色
ALTER TABLE users
    DROP CONSTRAINT IF EXISTS chk_user_role;

ALTER TABLE users
    ADD CONSTRAINT chk_user_role
        CHECK (role IN ('super_admin', 'event_admin', 'booth_cashier', 'issuer', 'reviewer', 'bank_clerk', 'merchant'));

-- 2. 更新 booth_cashier 约束，merchant 角色也需要关联 booth_id
ALTER TABLE users
    DROP CONSTRAINT IF EXISTS chk_booth_cashier_has_booth;

ALTER TABLE users
    ADD CONSTRAINT chk_booth_cashier_has_booth
        CHECK (
            (role = 'booth_cashier' AND booth_id IS NOT NULL) OR
            (role = 'merchant' AND booth_id IS NOT NULL) OR
            (role NOT IN ('booth_cashier', 'merchant'))
        );

-- ============================================================================
-- 说明：
-- 
-- merchant 角色的用户通过 /merchant/register 端点自主注册，
-- 注册时会自动创建关联的 booth 记录。
-- 
-- 商户可以：
--   - 注册并登录 (POST /merchant/register, POST /merchant/login)
--   - 查看和更新商铺信息 (GET/PUT /merchant/booth)
--   - 管理商品 (POST/PUT/DELETE /merchant/products)
--   - 查看收入统计 (GET /merchant/income)
--   - 查看交易记录 (GET /merchant/transactions)
-- ============================================================================
