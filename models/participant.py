"""
Participant ORM model for NFC Campus Event Quota System.

Represents event participants with NFC card binding.
"""

from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from typing import Optional

from core.database import Base
from core.timezone import CST


class Participant(Base):
    """
    Participant model for event attendees.
    
    参与者模型：代表活动参与者，每个参与者绑定一张 NFC 卡。
    参与者可以参加多个活动，在每个活动下有独立的账户。
    
    Attributes:
        id: Auto-incrementing primary key
        name: Participant name
        class_name: Class name (optional)
        student_no: Student number (optional)
        card_uid: NFC card UID (unique)
        status: Participant status (active/inactive/blocked)
        created_at: Creation timestamp
        updated_at: Last update timestamp
        accounts: Relationship to Account records
        transactions: Relationship to Transaction records
    """
    __tablename__ = 'participants'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    class_name = Column(String(100), nullable=True)
    student_no = Column(String(50), nullable=True, index=True)
    card_uid = Column(String(32), unique=True, nullable=False, index=True)
    participant_type = Column(String(20), nullable=False, default='person', index=True)
    status = Column(String(20), nullable=False, default='active', index=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(CST)
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(CST),
        onupdate=lambda: datetime.now(CST)
    )
    
    # Relationships
    accounts = relationship(
        "Account",
        back_populates="participant",
        cascade="all, delete-orphan"
    )
    transactions = relationship(
        "Transaction",
        back_populates="participant"
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'blocked')",
            name='chk_participant_status'
        ),
        CheckConstraint(
            "participant_type IN ('person', 'booth_collection')",
            name='chk_participant_type'
        ),
    )
    
    @property
    def is_verified(self) -> bool:
        """
        判断参与者是否已实名认证。
        实名条件：name 非空 且 (class_name 或 student_no 至少填写一项)
        """
        if not self.name or not self.name.strip():
            return False
        has_class = self.class_name and self.class_name.strip()
        has_student_no = self.student_no and self.student_no.strip()
        return bool(has_class or has_student_no)

    @property
    def display_name(self) -> str:
        """
        获取显示名称。
        已实名：返回真实姓名
        未实名：返回卡号（card_uid）
        """
        if self.is_verified:
            return self.name
        return self.card_uid

    def __repr__(self):
        return (
            f"<Participant(id={self.id}, name='{self.name}', "
            f"card_uid='{self.card_uid}', status='{self.status}')>"
        )
    
    def is_active(self) -> bool:
        """Check if participant is active."""
        return self.status == 'active'
    
    def is_blocked(self) -> bool:
        """Check if participant is blocked."""
        return self.status == 'blocked'
    
    def is_booth_collection_account(self) -> bool:
        """Check if this is a booth collection account."""
        return self.participant_type == 'booth_collection'
    
    def can_recharge(self) -> bool:
        """Check if this participant can receive recharge."""
        return self.participant_type == 'person' and self.is_active()
