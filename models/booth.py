"""
Booth ORM model for Booth Management System.

Represents booths/stalls in events, operated by classes or teams.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from core.database import Base
from core.timezone import CST


class Booth(Base):
    """
    Booth model for event booth management.
    
    摊位模型：代表活动中的经营单位，由班级或团队运营。
    每个摊位属于一个活动，可以销售多个商品，有多个收银员，并记录交易。
    
    Attributes:
        id: Auto-incrementing primary key
        event_id: Associated event ID (foreign key to events table)
        name: Booth name (e.g., "美食摊", "饮品站")
        class_name: Class or team name operating the booth (e.g., "高一(1)班")
        status: Booth status (active, inactive, closed)
        created_at: Creation timestamp
        event: Relationship to Event record
        products: Relationship to Product records (one-to-many)
        cashiers: Relationship to User records (booth cashiers)
        transactions: Relationship to Transaction records
    """
    __tablename__ = 'booths'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(
        Integer,
        ForeignKey('events.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    name = Column(String(100), nullable=False)
    class_name = Column(String(100), nullable=False)
    collection_participant_id = Column(
        Integer,
        ForeignKey('participants.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    status = Column(String(20), nullable=False, default='active')
    stock_enabled = Column(
        Integer,
        nullable=False,
        default=1,
        comment='是否允许参与股票市场: 1=允许, 0=不允许'
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(CST)
    )
    
    # Relationships
    event = relationship(
        "Event",
        back_populates="booths"
    )
    collection_participant = relationship(
        "Participant",
        foreign_keys=[collection_participant_id],
        uselist=False
    )
    products = relationship(
        "Product",
        back_populates="booth",
        cascade="all, delete-orphan"
    )
    cashiers = relationship(
        "User",
        back_populates="booth",
        foreign_keys="User.booth_id"
    )
    transactions = relationship(
        "Transaction",
        back_populates="booth",
        foreign_keys="Transaction.booth_id"
    )
    cash_reconciliations = relationship(
        "CashReconciliation",
        back_populates="booth",
        cascade="all, delete-orphan"
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'closed')",
            name='chk_booth_status'
        ),
    )
    
    def __repr__(self):
        return f"<Booth(id={self.id}, name='{self.name}', class_name='{self.class_name}', status='{self.status}')>"
    
    def is_active(self) -> bool:
        """Check if booth is active."""
        return self.status == 'active'
    
    def can_process_transactions(self) -> bool:
        """
        Check if booth can process transactions.
        
        Returns:
            True if booth is active and belongs to an active event, False otherwise
        """
        return self.is_active() and self.event.is_active() if self.event else False
