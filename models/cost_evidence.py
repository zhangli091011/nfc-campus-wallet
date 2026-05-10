"""
Cost Evidence ORM model for Booth Management System.

成本凭据模型：商铺上传的成本凭据（收据、发票等）。
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from core.database import Base


class CostEvidence(Base):
    """
    成本凭据模型。

    Attributes:
        id: 自增主键
        booth_id: 关联商铺ID
        uploader_id: 上传者用户ID
        filename: 原始文件名
        stored_filename: 存储文件名（UUID生成）
        file_path: 文件存储路径
        file_size: 文件大小（字节）
        mime_type: 文件MIME类型
        category: 凭据类别 (material/logistics/labor/rent/other)
        amount: 凭据金额（元）
        description: 凭据描述/备注
        status: 审核状态 (pending/approved/rejected)
        reviewed_by: 审核人用户ID
        reviewed_at: 审核时间
        created_at: 上传时间
    """
    __tablename__ = 'cost_evidences'

    id = Column(Integer, primary_key=True, autoincrement=True)
    booth_id = Column(
        Integer,
        ForeignKey('booths.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    uploader_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False, default='other')
    amount = Column(Numeric(10, 2), nullable=True)
    description = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default='pending')
    reviewed_by = Column(
        Integer,
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    booth = relationship("Booth", backref="cost_evidences")
    uploader = relationship("User", foreign_keys=[uploader_id], backref="uploaded_evidences")
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "category IN ('material', 'logistics', 'labor', 'rent', 'other')",
            name='chk_evidence_category'
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name='chk_evidence_status'
        ),
        CheckConstraint(
            "amount IS NULL OR amount >= 0",
            name='chk_evidence_amount'
        ),
        CheckConstraint(
            "file_size > 0",
            name='chk_evidence_file_size'
        ),
    )

    def __repr__(self):
        return (
            f"<CostEvidence(id={self.id}, booth_id={self.booth_id}, "
            f"filename='{self.filename}', category='{self.category}', "
            f"status='{self.status}')>"
        )
