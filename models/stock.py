"""
Stock ORM model for Campus Stock Market Simulation.

模拟股市模块 - 股票模型
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from decimal import Decimal

from core.database import Base


class Stock(Base):
    """
    Stock model for booth stock issuance.
    
    股票模型：每个摊位可以发行股票，参与者可以购买并锁仓至期末结算。
    
    Attributes:
        id: Auto-incrementing primary key
        booth_id: 关联的摊位ID
        event_id: 关联的活动ID
        initial_price: 初始发行价（分）- 统一为 1000 分（10元）
        total_shares: 总发行股数
        sold_shares: 已售出股数
        status: 股票状态 (active/suspended/settled)
        created_at: 创建时间
        updated_at: 更新时间
    """
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    booth_id = Column(
        Integer,
        ForeignKey('booths.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,  # 每个摊位只能发行一只股票
        index=True
    )
    event_id = Column(
        Integer,
        ForeignKey('events.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    initial_price = Column(
        Integer,
        nullable=False,
        default=1000,
        comment='初始发行价（分），默认1000分=10元'
    )
    total_shares = Column(
        Integer,
        nullable=False,
        comment='总发行股数'
    )
    sold_shares = Column(
        Integer,
        nullable=False,
        default=0,
        comment='已售出股数'
    )
    status = Column(
        String(20),
        nullable=False,
        default='active',
        index=True
    )
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
    booth = relationship("Booth", backref="stock")
    event = relationship("Event", backref="stocks")
    purchases = relationship(
        "StockPurchase",
        back_populates="stock",
        cascade="all, delete-orphan"
    )
    settlement = relationship(
        "BoothSettlement",
        back_populates="stock",
        uselist=False
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'suspended', 'settled')",
            name='chk_stock_status'
        ),
        CheckConstraint('initial_price > 0', name='chk_initial_price_positive'),
        CheckConstraint('total_shares > 0', name='chk_total_shares_positive'),
        CheckConstraint('sold_shares >= 0', name='chk_sold_shares_non_negative'),
        CheckConstraint('sold_shares <= total_shares', name='chk_sold_not_exceed_total'),
    )
    
    def __repr__(self):
        return (
            f"<Stock(id={self.id}, booth_id={self.booth_id}, "
            f"sold={self.sold_shares}/{self.total_shares}, status='{self.status}')>"
        )
    
    @property
    def initial_price_yuan(self) -> float:
        """获取初始发行价（元）"""
        return self.initial_price / 100.0
    
    @property
    def available_shares(self) -> int:
        """获取剩余可购买股数"""
        return self.total_shares - self.sold_shares
    
    def is_available(self) -> bool:
        """检查股票是否可购买"""
        return self.status == 'active' and self.available_shares > 0
    
    def can_purchase(self, quantity: int) -> bool:
        """检查是否可以购买指定数量"""
        return self.is_available() and quantity <= self.available_shares


class StockPurchase(Base):
    """
    Stock purchase record model.
    
    股票购买记录：记录参与者购买股票的详细信息。
    股票不可二次交易，只能锁仓至期末结算。
    
    Attributes:
        id: Auto-incrementing primary key
        stock_id: 股票ID
        participant_id: 购买者ID
        event_id: 活动ID
        quantity: 购买股数
        purchase_price: 购买单价（分）
        total_amount: 购买总金额（分）
        transaction_id: 关联的交易记录ID
        status: 状态 (holding/settled)
        settlement_price: 结算单价（分，结算后填充）
        settlement_amount: 结算总金额（分，结算后填充）
        created_at: 购买时间
        settled_at: 结算时间
    """
    __tablename__ = 'stock_purchases'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(
        Integer,
        ForeignKey('stocks.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
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
    quantity = Column(
        Integer,
        nullable=False,
        comment='购买股数'
    )
    purchase_price = Column(
        Integer,
        nullable=False,
        comment='购买单价（分）'
    )
    total_amount = Column(
        Integer,
        nullable=False,
        comment='购买总金额（分）'
    )
    transaction_id = Column(
        Integer,
        ForeignKey('transactions.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    status = Column(
        String(20),
        nullable=False,
        default='holding',
        index=True
    )
    settlement_price = Column(
        Integer,
        nullable=True,
        comment='结算单价（分）'
    )
    settlement_amount = Column(
        Integer,
        nullable=True,
        comment='结算总金额（分）'
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    settled_at = Column(
        DateTime,
        nullable=True
    )
    
    # Relationships
    stock = relationship("Stock", back_populates="purchases")
    participant = relationship("Participant", backref="stock_purchases")
    event = relationship("Event", backref="stock_purchases")
    transaction = relationship("Transaction", backref="stock_purchase")
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('holding', 'settled')",
            name='chk_purchase_status'
        ),
        CheckConstraint('quantity > 0', name='chk_quantity_positive'),
        CheckConstraint('purchase_price > 0', name='chk_purchase_price_positive'),
        CheckConstraint('total_amount > 0', name='chk_total_amount_positive'),
        CheckConstraint(
            'settlement_price IS NULL OR settlement_price >= 0',
            name='chk_settlement_price_non_negative'
        ),
        CheckConstraint(
            'settlement_amount IS NULL OR settlement_amount >= 0',
            name='chk_settlement_amount_non_negative'
        ),
    )
    
    def __repr__(self):
        return (
            f"<StockPurchase(id={self.id}, stock_id={self.stock_id}, "
            f"participant_id={self.participant_id}, quantity={self.quantity}, "
            f"status='{self.status}')>"
        )
    
    @property
    def purchase_price_yuan(self) -> float:
        """获取购买单价（元）"""
        return self.purchase_price / 100.0
    
    @property
    def total_amount_yuan(self) -> float:
        """获取购买总金额（元）"""
        return self.total_amount / 100.0
    
    @property
    def settlement_price_yuan(self) -> float | None:
        """获取结算单价（元）"""
        return self.settlement_price / 100.0 if self.settlement_price else None
    
    @property
    def settlement_amount_yuan(self) -> float | None:
        """获取结算总金额（元）"""
        return self.settlement_amount / 100.0 if self.settlement_amount else None
    
    @property
    def profit_loss(self) -> int | None:
        """获取盈亏金额（分）"""
        if self.settlement_amount is None:
            return None
        return self.settlement_amount - self.total_amount
    
    @property
    def profit_loss_yuan(self) -> float | None:
        """获取盈亏金额（元）"""
        profit_loss = self.profit_loss
        return profit_loss / 100.0 if profit_loss is not None else None


class BoothSettlement(Base):
    """
    Booth settlement record for stock market.
    
    摊位期末结算记录：记录每个摊位的经营数据和最终股价。
    
    Attributes:
        id: Auto-incrementing primary key
        booth_id: 摊位ID
        stock_id: 股票ID
        event_id: 活动ID
        revenue: 营业额（分）
        profit: 净利润（分）
        order_count: 订单总数
        score: 摊位经营分
        global_pool: 全局奖金池总额（分）
        total_score: 全场摊位总分
        ratio: 分红占比（0-1之间的小数）
        final_price: 最终每股价格（分）
        settled_at: 结算时间
    """
    __tablename__ = 'booth_settlements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    booth_id = Column(
        Integer,
        ForeignKey('booths.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
        index=True
    )
    stock_id = Column(
        Integer,
        ForeignKey('stocks.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
        index=True
    )
    event_id = Column(
        Integer,
        ForeignKey('events.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # 经营数据
    revenue = Column(
        Integer,
        nullable=False,
        default=0,
        comment='营业额（分）'
    )
    profit = Column(
        Integer,
        nullable=False,
        default=0,
        comment='净利润（分）'
    )
    order_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment='订单总数'
    )
    
    # 计算结果
    score = Column(
        Numeric(20, 6),
        nullable=False,
        comment='摊位经营分 = 0.2*营业额 + 0.6*净利润 + 0.2*订单数'
    )
    global_pool = Column(
        Integer,
        nullable=False,
        comment='全局奖金池（分）'
    )
    total_score = Column(
        Numeric(20, 6),
        nullable=False,
        comment='全场摊位总分'
    )
    ratio = Column(
        Numeric(10, 8),
        nullable=False,
        comment='分红占比（0-1）'
    )
    final_price = Column(
        Integer,
        nullable=False,
        comment='最终每股价格（分）'
    )
    
    settled_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    booth = relationship("Booth", backref="settlement")
    stock = relationship("Stock", back_populates="settlement")
    event = relationship("Event", backref="settlements")
    
    # Table constraints
    __table_args__ = (
        CheckConstraint('revenue >= 0', name='chk_revenue_non_negative'),
        CheckConstraint('order_count >= 0', name='chk_order_count_non_negative'),
        CheckConstraint('score >= 0', name='chk_score_non_negative'),
        CheckConstraint('global_pool >= 0', name='chk_global_pool_non_negative'),
        CheckConstraint('total_score > 0', name='chk_total_score_positive'),
        CheckConstraint('ratio >= 0 AND ratio <= 1', name='chk_ratio_range'),
        CheckConstraint('final_price >= 0', name='chk_final_price_non_negative'),
    )
    
    def __repr__(self):
        return (
            f"<BoothSettlement(id={self.id}, booth_id={self.booth_id}, "
            f"score={self.score}, final_price={self.final_price})>"
        )
    
    @property
    def revenue_yuan(self) -> float:
        """获取营业额（元）"""
        return self.revenue / 100.0
    
    @property
    def profit_yuan(self) -> float:
        """获取净利润（元）"""
        return self.profit / 100.0
    
    @property
    def final_price_yuan(self) -> float:
        """获取最终每股价格（元）"""
        return self.final_price / 100.0
    
    @property
    def global_pool_yuan(self) -> float:
        """获取全局奖金池（元）"""
        return self.global_pool / 100.0
