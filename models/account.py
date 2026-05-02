"""
Account ORM model for NFC Campus Event Quota System.

Represents participant accounts for specific events.
"""

from sqlalchemy import Column, Integer, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from core.database import Base


class Account(Base):
    """
    Account model for event-specific participant accounts.
    
    账户模型：代表参与者在特定活动下的账户。
    一个参与者在一个活动下只能有一个账户。
    账户余额仅在该活动内有效。
    
    Attributes:
        id: Auto-incrementing primary key
        participant_id: Reference to participant
        event_id: Reference to event
        balance: Account balance in cents (单位：分)
        created_at: Creation timestamp
        updated_at: Last update timestamp
        participant: Relationship to Participant record
        event: Relationship to Event record
        transactions: Relationship to Transaction records
    """
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    participant_id = Column(
        Integer,
        ForeignKey('participants.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    event_id = Column(
        Integer,
        ForeignKey('events.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    balance = Column(Integer, nullable=False, default=0, comment='账户余额（分）')
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
    participant = relationship("Participant", back_populates="accounts")
    event = relationship("Event", back_populates="accounts")
    transactions = relationship(
        "Transaction",
        back_populates="account",
        order_by="Transaction.created_at.desc()"
    )
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('participant_id', 'event_id', name='uk_participant_event'),
        CheckConstraint('balance >= 0', name='chk_account_balance'),
    )
    
    def __repr__(self):
        return (
            f"<Account(id={self.id}, participant_id={self.participant_id}, "
            f"event_id={self.event_id}, balance={self.balance} cents)>"
        )
    
    @property
    def balance_yuan(self) -> float:
        """Get balance in yuan (元)."""
        return self.balance / 100.0
