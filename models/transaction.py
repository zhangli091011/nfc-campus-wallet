"""
Transaction ORM model for NFC Campus E-Wallet System.

Represents all transaction types in ledger append-only mode.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from core.database import Base


class TransactionType(enum.Enum):
    """Transaction type enumeration for ledger mode."""
    recharge = "recharge"  # 充值
    pay = "pay"            # 支付
    refund = "refund"      # 退款
    adjust = "adjust"      # 调整
    issue = "issue"        # 发卡
    void = "void"          # 作废
    expire = "expire"      # 过期


class Transaction(Base):
    """
    Transaction record model (Ledger Append-Only Mode).
    
    账本追加模式：所有交易都是追加记录，不可修改。
    每条记录包含交易前后余额，形成完整的审计链。
    
    Attributes:
        id: Auto-incrementing primary key
        uid: Reference to user who performed transaction
        card_uid: Card UID (compatible with uid field)
        type: Transaction type (recharge/pay/refund/adjust/issue/void/expire)
        amount: Transaction amount in cents (always positive, 单位：分)
        balance_before: Account balance before transaction (单位：分)
        balance_after: Account balance after transaction (单位：分)
        merchant_id: Optional merchant identifier for payment transactions
        related_txn_id: Related transaction ID (for refunds, adjustments)
        remark: Optional transaction remark
        operator_id: Optional operator ID (for admin operations)
        created_at: Transaction timestamp
        user: Relationship to User record
        related_transaction: Relationship to related transaction
    """
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # User identification (legacy)
    uid = Column(
        String(32),
        nullable=True,  # 改为可选，兼容旧数据
        index=True
    )
    card_uid = Column(String(32), nullable=True, index=True)
    
    # Event system identification
    event_id = Column(
        Integer,
        ForeignKey('events.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    participant_id = Column(
        Integer,
        ForeignKey('participants.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    account_id = Column(
        Integer,
        ForeignKey('accounts.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Transaction details
    type = Column(String(20), nullable=False)
    amount = Column(Integer, nullable=False, comment='金额（分）')
    balance_before = Column(Integer, nullable=False, default=0, comment='交易前余额（分）')
    balance_after = Column(Integer, nullable=False, comment='交易后余额（分）')
    
    # Optional fields
    merchant_id = Column(String(64), nullable=True, index=True)
    related_txn_id = Column(
        Integer,
        ForeignKey('transactions.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    remark = Column(String(255), nullable=True)
    operator_id = Column(String(64), nullable=True, index=True)
    
    # Booth management system fields
    booth_id = Column(
        Integer,
        ForeignKey('booths.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    product_id = Column(
        Integer,
        ForeignKey('products.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    booth_operator_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment='Booth system operator (User.id)'
    )
    
    # Timestamp
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    
    # Relationships
    # Legacy user relationship removed - incompatible with booth management User model
    # user = relationship("User", back_populates="transactions", primaryjoin="foreign(Transaction.uid) == User.uid")
    event = relationship("Event", back_populates="transactions")
    participant = relationship("Participant", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    related_transaction = relationship(
        "Transaction",
        remote_side=[id],
        foreign_keys=[related_txn_id]
    )
    booth = relationship(
        "Booth",
        back_populates="transactions",
        foreign_keys=[booth_id]
    )
    product = relationship(
        "Product",
        back_populates="transactions",
        foreign_keys=[product_id]
    )
    booth_operator = relationship(
        "User",
        back_populates="operated_transactions",
        foreign_keys=[booth_operator_id]
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "type IN ('recharge', 'pay', 'refund', 'adjust', 'issue', 'void', 'expire')",
            name='chk_transaction_type'
        ),
        CheckConstraint('amount > 0', name='chk_amount_positive'),
        CheckConstraint('balance_before >= 0', name='chk_balance_before_non_negative'),
        CheckConstraint('balance_after >= 0', name='chk_balance_after_non_negative'),
    )
    
    def __repr__(self):
        return (
            f"<Transaction(id={self.id}, uid='{self.uid}', type='{self.type}', "
            f"amount={self.amount}, balance_before={self.balance_before}, "
            f"balance_after={self.balance_after})>"
        )
    
    @property
    def amount_yuan(self) -> float:
        """Get amount in yuan (元)."""
        return self.amount / 100.0
    
    @property
    def balance_before_yuan(self) -> float:
        """Get balance_before in yuan (元)."""
        return self.balance_before / 100.0
    
    @property
    def balance_after_yuan(self) -> float:
        """Get balance_after in yuan (元)."""
        return self.balance_after / 100.0
