-- ============================================
-- Add stock_enabled flag to booths table
-- 控制商家是否可以参与股票市场
-- ============================================

ALTER TABLE booths ADD COLUMN stock_enabled TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否允许参与股票市场: 1=允许, 0=不允许';
