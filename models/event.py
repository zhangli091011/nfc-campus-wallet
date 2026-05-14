"""
Event ORM model for NFC Campus Event Quota System.

Represents school events with quota management.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from typing import Optional

from core.database import Base
from core.timezone import CST


class Event(Base):
    """
    Event model for school activities.
    
    活动模型：管理学校活动的基本信息和配置。
    每个活动有独立的额度系统，参与者在不同活动下有不同的账户。
    
    Attributes:
        id: Auto-incrementing primary key
        name: Event name
        start_date: Event start date
        end_date: Event end date
        status: Event status (active/inactive/closed)
        allow_recharge: Whether recharge is allowed
        allow_payment: Whether payment is allowed
        created_at: Creation timestamp
        updated_at: Last update timestamp
        accounts: Relationship to Account records
        transactions: Relationship to Transaction records
        booths: Relationship to Booth records
    """
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    start_date = Column(DateTime, nullable=False)  # 注意：数据库中是 DATE 类型
    end_date = Column(DateTime, nullable=False)    # 注意：数据库中是 DATE 类型
    status = Column(String(20), nullable=False, default='active', index=True)
    allow_recharge = Column(Boolean, nullable=False, default=True)
    allow_payment = Column(Boolean, nullable=False, default=True)
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
            "status IN ('active', 'inactive', 'closed')",
            name='chk_event_status'
        ),
    )
    
    def __repr__(self):
        return f"<Event(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    def is_active(self) -> bool:
        """Check if event is currently active."""
        now = datetime.now(CST).date()
        
        # Convert to date objects for comparison
        start_date = self.start_date
        end_date = self.end_date
        
        # Handle both date and datetime objects
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime):
            end_date = end_date.date()
        
        return (
            self.status == 'active' and
            start_date <= now <= end_date
        )
    
    def can_recharge(self) -> bool:
        """Check if recharge is allowed."""
        return self.is_active() and self.allow_recharge
    
    def can_consume(self) -> bool:
        """Check if consumption/payment is allowed."""
        return self.is_active() and self.allow_payment
    
    def is_within_time_range(self) -> bool:
        """Check if current time is within event time range."""
        now = datetime.now(CST).date()
        
        # Convert to date objects for comparison
        start_date = self.start_date
        end_date = self.end_date
        
        # Handle both date and datetime objects
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime):
            end_date = end_date.date()
        
        return start_date <= now <= end_date
