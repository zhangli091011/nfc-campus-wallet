-- Migration 011: Add staff_name column to users table
-- 工作人员首次登录时需要输入姓名

ALTER TABLE users ADD COLUMN staff_name VARCHAR(50) NULL DEFAULT NULL;

-- Add comment
-- staff_name: 工作人员真实姓名，首次登录安卓端时设置
