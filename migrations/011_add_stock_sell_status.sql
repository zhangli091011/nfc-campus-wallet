-- ============================================
-- Add 'sold' status to stock_orders
-- 支持股票抛售功能
-- ============================================

-- 1. 删除旧的状态约束
ALTER TABLE stock_orders DROP CONSTRAINT IF EXISTS chk_order_status;

-- 2. 添加新的状态约束（包含 sold）
ALTER TABLE stock_orders ADD CONSTRAINT chk_order_status 
    CHECK (status IN ('holding', 'settled', 'sold'));

-- 3. 添加索引优化持仓查询
CREATE INDEX IF NOT EXISTS idx_stock_orders_holding 
    ON stock_orders(participant_id, event_id, booth_id, status);
