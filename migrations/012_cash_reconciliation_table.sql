-- ============================================================================
-- Migration: Create booth_cash_reconciliations table
-- Description: 创建现金对账记录表
-- Date: 2026-05-12
-- ============================================================================

CREATE TABLE IF NOT EXISTS booth_cash_reconciliations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booth_id INT NOT NULL,
    event_id INT NOT NULL,
    expected_cash INT NOT NULL DEFAULT 0 COMMENT '预期现金金额（分）',
    actual_cash INT NOT NULL DEFAULT 0 COMMENT '实际现金金额（分）',
    diff_amount INT NOT NULL DEFAULT 0 COMMENT '差额（分）= actual_cash - expected_cash',
    reason TEXT NULL COMMENT '差额原因说明',
    reviewer_id INT NULL COMMENT '审核人ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_booth_id (booth_id),
    INDEX idx_event_id (event_id),
    INDEX idx_reviewer_id (reviewer_id),
    INDEX idx_created_at (created_at),
    
    CONSTRAINT fk_reconciliation_booth FOREIGN KEY (booth_id) REFERENCES booths(id) ON DELETE CASCADE,
    CONSTRAINT fk_reconciliation_event FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    CONSTRAINT fk_reconciliation_reviewer FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
