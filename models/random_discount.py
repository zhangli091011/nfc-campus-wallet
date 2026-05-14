"""
Random Discount ORM models for NFC Campus E-Wallet System.

随机立减系统模型：配置表和记录表。
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from core.database import Base


class RandomDiscountSetting(Base):
    """
    随机立减配置模型。
    
    每个活动可以有一个随机立减配置，管理员可以设置：
    - 立减金额范围（最小/最大）
    - 触发概率
    - 总奖池和剩余奖池
    - 单笔最大立减
    - 最低消费金额门槛
    - 每人每日限制次数
    """
    __tablename__ = 'random_discount_settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('events.id', ondelete='CASCADE'), nullable=False, unique=True)
    enabled = Column(Boolean, nullable=False, default=False)
    min_discount_amount = Column(Numeric(12, 2), nullable=False, default=0.01)
    max_discount_amount = Column(Numeric(12, 2), nullable=False, default=5.00)
    probability = Column(Integer, nullable=False, default=100)  # 1-100
    total_pool = Column(Numeric(12, 2), nullable=False, default=1000.00)
    remaining_pool = Column(Numeric(12, 2), nullable=False, default=1000.00)
    max_discount_per_transaction = Column(Numeric(12, 2), nullable=True)
    min_payment_amount = Column(Numeric(12, 2), nullable=False, default=1.00)
    daily_limit_per_user = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    event = relationship("Event", backref="random_discount_setting")
    records = relationship("RandomDiscountRecord", back_populates="setting",
                          foreign_keys="RandomDiscountRecord.event_id",
                          primaryjoin="RandomDiscountSetting.event_id==RandomDiscountRecord.event_id",
                          overlaps="event,random_discount_setting",
                          viewonly=True)


class RandomDiscountRecord(Base):
    """
    随机立减记录模型。
    
    记录每次随机立减的详细信息，用于审计和统计。
    """
    __tablename__ = 'random_discount_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('events.id', ondelete='CASCADE'), nullable=False)
    participant_id = Column(Integer, ForeignKey('participants.id', ondelete='CASCADE'), nullable=False)
    transaction_id = Column(Integer, ForeignKey('transactions.id', ondelete='CASCADE'), nullable=False)
    booth_id = Column(Integer, ForeignKey('booths.id', ondelete='SET NULL'), nullable=True)
    original_amount = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), nullable=False)
    actual_amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    event = relationship("Event", overlaps="random_discount_setting,records")
    participant = relationship("Participant")
    transaction = relationship("Transaction")
    booth = relationship("Booth")
    setting = relationship("RandomDiscountSetting",
                          foreign_keys=[event_id],
                          primaryjoin="RandomDiscountRecord.event_id==RandomDiscountSetting.event_id",
                          viewonly=True,
                          overlaps="event,records,random_discount_setting")
