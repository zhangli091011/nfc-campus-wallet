"""
Stock Order ORM model for Campus Stock Market Simulation.

股票订单模型 - 股票购买直接从主账户（accounts）扣款，不再有独立投资币账户。
所有金额以"元"为单位。
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from decimal import Decimal

from core.database import Base


class StockOrder(Base):
    """
    Stock order model for stock purchases.
    
    股票订单模型：记录股票购买订单。
    购买金额直接从 accounts.balance 扣除。
    
    Attributes:
        id: Auto-incrementing primary key
        event_id: 活动ID
        participant_id: 参与者ID
        account_id: 关联的活动账户ID
        card_uid: NFC卡UID
        booth_id: 摊位ID
        shares: 购买股数
        buy_price: 购买单价（元）
        total_amount: 购买总金额（元）
        status: 订单状态 (holding/settled)
        settlement_price: 结算单价（元）
        settlement_amount: 结算总金额（元）
    """
    __tablename__ = 'stock_orders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(
        Integer,
        ForeignKey('events.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    participant_id = Column(
        Integer,
        ForeignKey('participants.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    account_id = Column(
        Integer,
        ForeignKey('accounts.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    card_uid = Column(String(32), nullable=False, index=True)
    booth_id = Column(
        Integer,
        ForeignKey('booths.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    shares = Column(Integer, nullable=False, comment='购买股数')
    buy_price = Column(
        Numeric(12, 2), nullable=False,
        comment='购买单价（元）'
    )
    total_amount = Column(
        Numeric(12, 2), nullable=False,
        comment='购买总金额（元）'
    )
    status = Column(
        String(20), nullable=False, default='holding',
        comment='订单状态: holding/settled'
    )
    settlement_price = Column(
        Numeric(12, 2), nullable=True,
        comment='结算单价（元）'
    )
    settlement_amount = Column(
        Numeric(12, 2), nullable=True,
        comment='结算总金额（元）'
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    settled_at = Column(DateTime, nullable=True)
    
    # Relationships
    event = relationship("Event")
    participant = relationship("Participant")
    account = relationship("Account")
    booth = relationship("Booth")
    
    def __repr__(self):
        return (
            f"<StockOrder(id={self.id}, booth_id={self.booth_id}, "
            f"shares={self.shares}, total={self.total_amount}元)>"
        )
    
    @property
    def buy_price_yuan(self) -> float:
        return float(self.buy_price)
    
    @property
    def total_amount_yuan(self) -> float:
        return float(self.total_amount)
    
    @property
    def settlement_price_yuan(self) -> float:
        return float(self.settlement_price) if self.settlement_price else 0.0
    
    @property
    def settlement_amount_yuan(self) -> float:
        return float(self.settlement_amount) if self.settlement_amount else 0.0
    
    @property
    def amount_yuan(self) -> float:
        """Alias for total_amount_yuan (backward compat)."""
        return float(self.total_amount)
