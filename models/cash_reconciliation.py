"""
Cash Reconciliation ORM model for NFC Campus Event System.

现金对账模型：用于记录摊位现金对账信息。
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from core.database import Base


class CashReconciliation(Base):
    """
    现金对账记录模型。
    
    用于记录摊位的现金对账信息，包括预期现金、实际现金、差额等。
    
    Attributes:
        id: Auto-incrementing primary key
        booth_id: 摊位ID
        event_id: 活动ID
        expected_cash: 预期现金金额（分）
        actual_cash: 实际现金金额（分）
        diff_amount: 差额（分）= actual_cash - expected_cash
        reason: 差额原因说明
        reviewer_id: 审核人ID
        created_at: 创建时间
        booth: Relationship to Booth
        event: Relationship to Event
        reviewer: Relationship to User (reviewer)
    """
    __tablename__ = 'booth_cash_reconciliations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    booth_id = Column(
        Integer,
        ForeignKey('booths.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    event_id = Column(
        Integer,
        ForeignKey('events.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    expected_cash = Column(
        Integer,
        nullable=False,
        default=0,
        comment='预期现金金额（分）'
    )
    actual_cash = Column(
        Integer,
        nullable=False,
        default=0,
        comment='实际现金金额（分）'
    )
    diff_amount = Column(
        Integer,
        nullable=False,
        default=0,
        comment='差额（分）= actual_cash - expected_cash'
    )
    reason = Column(Text, nullable=True, comment='差额原因说明')
    reviewer_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment='审核人ID'
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    
    # Relationships
    booth = relationship("Booth", back_populates="cash_reconciliations")
    event = relationship("Event", back_populates="cash_reconciliations")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    
    def __repr__(self):
        return (
            f"<CashReconciliation(id={self.id}, booth_id={self.booth_id}, "
            f"expected={self.expected_cash}, actual={self.actual_cash}, "
            f"diff={self.diff_amount})>"
        )
    
    @property
    def expected_cash_yuan(self) -> float:
        """预期现金金额（元）"""
        return self.expected_cash / 100.0
    
    @property
    def actual_cash_yuan(self) -> float:
        """实际现金金额（元）"""
        return self.actual_cash / 100.0
    
    @property
    def diff_amount_yuan(self) -> float:
        """差额（元）"""
        return self.diff_amount / 100.0
