"""
Event ORM model for NFC Campus Event Quota System.

Represents school events with quota management.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from typing import Optional

from core.database import Base


class Event(Base):
    """
    Event model for school activities.
    
    活动模型：管理学校活动的基本信息和配置。
    每个活动有独立的额度系统，参与者在不同活动下有不同的账户。
    
    Attributes:
        id: Auto-incrementing primary key
        name: Event name
        start_time: Event start time
        end_time: Event end time
        status: Event status (draft/active/paused/ended)
        recharge_enabled: Whether recharge is allowed
        consume_enabled: Whether consumption is allowed
        expire_rule: Quota expiration rule (event_end/never/custom)
        created_at: Creation timestamp
        updated_at: Last update timestamp
        accounts: Relationship to Account records
        transactions: Relationship to Transaction records
    """
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default='draft', index=True)
    recharge_enabled = Column(Boolean, nullable=False, default=True)
    consume_enabled = Column(Boolean, nullable=False, default=True)
    expire_rule = Column(String(50), default='event_end')
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    accounts = relationship(
        "Account",
        back_populates="event",
        cascade="all, delete-orphan"
    )
    transactions = relationship(
        "Transaction",
        back_populates="event"
    )
    booths = relationship(
        "Booth",
        back_populates="event",
        cascade="all, delete-orphan"
    )
    cash_reconciliations = relationship(
        "CashReconciliation",
        back_populates="event",
        cascade="all, delete-orphan"
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'paused', 'ended')",
            name='chk_event_status'
        ),
        CheckConstraint(
            "expire_rule IN ('event_end', 'never', 'custom')",
            name='chk_expire_rule'
        ),
    )
    
    def __repr__(self):
        return f"<Event(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    def is_active(self) -> bool:
        """Check if event is currently active."""
        now = datetime.now(timezone.utc)
        return (
            self.status == 'active' and
            self.start_time <= now <= self.end_time
        )
    
    def can_recharge(self) -> bool:
        """Check if recharge is allowed."""
        return self.is_active() and self.recharge_enabled
    
    def can_consume(self) -> bool:
        """Check if consumption is allowed."""
        return self.is_active() and self.consume_enabled
    
    def is_within_time_range(self) -> bool:
        """Check if current time is within event time range."""
        now = datetime.now(timezone.utc)
        return self.start_time <= now <= self.end_time
