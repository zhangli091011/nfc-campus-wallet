"""
Account ORM model for NFC Campus Event Quota System.

Represents participant accounts for specific events.
All amounts stored in 元 (yuan) as DECIMAL(12,2).
"""

from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from decimal import Decimal

from core.database import Base
from core.timezone import CST


class Account(Base):
    """
    Account model for event-specific participant accounts.
    
    账户模型：代表参与者在特定活动下的唯一账户。
    所有金额以"元"为单位，DECIMAL(12,2) 精度。
    股票购买、消费、充值、信贷均从此账户扣款/入账。
    
    Attributes:
        id: Auto-incrementing primary key
        participant_id: Reference to participant
        event_id: Reference to event
        balance: Account balance in yuan (元)
        credit_borrowed: Total loan principal (元)
        credit_fee_paid: Total loan fees paid (元)
        created_at: Creation timestamp
        updated_at: Last update timestamp
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
    balance = Column(
        Numeric(12, 2), nullable=False, default=Decimal('0.00'),
        comment='账户余额（元）'
    )
    credit_borrowed = Column(
        Numeric(12, 2), nullable=False, default=Decimal('0.00'),
        comment='名义借款总额（元）'
    )
    credit_fee_paid = Column(
        Numeric(12, 2), nullable=False, default=Decimal('0.00'),
        comment='已支付借款手续费总额（元）'
    )
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
    )
    
    def __repr__(self):
        return (
            f"<Account(id={self.id}, participant_id={self.participant_id}, "
            f"event_id={self.event_id}, balance={self.balance} 元)>"
        )
    
    @property
    def balance_yuan(self) -> float:
        """Get balance as float (backward compatibility)."""
        return float(self.balance)

    @property
    def credit_borrowed_yuan(self) -> float:
        """Get credit_borrowed as float."""
        return float(self.credit_borrowed)

    @property
    def credit_fee_paid_yuan(self) -> float:
        """Get credit_fee_paid as float."""
        return float(self.credit_fee_paid)
