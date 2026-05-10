-- ============================================================================
-- Migration: Cost Evidence Upload System (成本凭据上传系统)
-- Description: 为商铺管理处添加成本凭据上传功能
-- Date: 2026-05-10
-- ============================================================================

-- 创建 cost_evidences 表（成本凭据表）
CREATE TABLE IF NOT EXISTS cost_evidences (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '凭据ID',
    booth_id INT NOT NULL COMMENT '商铺ID',
    uploader_id INT NOT NULL COMMENT '上传者用户ID',
    filename VARCHAR(255) NOT NULL COMMENT '原始文件名',
    stored_filename VARCHAR(255) NOT NULL COMMENT '存储文件名（UUID）',
    file_path VARCHAR(500) NOT NULL COMMENT '文件存储路径',
    file_size INT NOT NULL COMMENT '文件大小（字节）',
    mime_type VARCHAR(100) NOT NULL COMMENT '文件MIME类型',
    category VARCHAR(50) NOT NULL DEFAULT 'other' COMMENT '凭据类别: material/logistics/labor/rent/other',
    amount DECIMAL(10, 2) DEFAULT NULL COMMENT '凭据金额（元）',
    description VARCHAR(500) DEFAULT NULL COMMENT '凭据描述/备注',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '审核状态: pending/approved/rejected',
    reviewed_by INT DEFAULT NULL COMMENT '审核人用户ID',
    reviewed_at DATETIME DEFAULT NULL COMMENT '审核时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',

    -- 外键约束
    CONSTRAINT fk_cost_evidence_booth
        FOREIGN KEY (booth_id)
        REFERENCES booths(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_cost_evidence_uploader
        FOREIGN KEY (uploader_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_cost_evidence_reviewer
        FOREIGN KEY (reviewed_by)
        REFERENCES users(id)
        ON DELETE SET NULL,

    -- 约束
    CONSTRAINT chk_evidence_category
        CHECK (category IN ('material', 'logistics', 'labor', 'rent', 'other')),
    CONSTRAINT chk_evidence_status
        CHECK (status IN ('pending', 'approved', 'rejected')),
    CONSTRAINT chk_evidence_amount
        CHECK (amount IS NULL OR amount >= 0),
    CONSTRAINT chk_evidence_file_size
        CHECK (file_size > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='成本凭据表';

-- 创建索引
CREATE INDEX idx_cost_evidences_booth_id ON cost_evidences(booth_id);
CREATE INDEX idx_cost_evidences_uploader_id ON cost_evidences(uploader_id);
CREATE INDEX idx_cost_evidences_status ON cost_evidences(status);
CREATE INDEX idx_cost_evidences_category ON cost_evidences(category);
CREATE INDEX idx_cost_evidences_created_at ON cost_evidences(created_at);
