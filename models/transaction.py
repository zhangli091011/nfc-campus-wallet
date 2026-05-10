"""
Transaction ORM model for NFC Campus E-Wallet System.

Represents all transaction types in ledger append-only mode.
All amounts stored in 元 (yuan) as DECIMAL(12,2).
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from decimal import Decimal
import enum

from core.database import Base


class TransactionType(enum.Enum):
    """Transaction type enumeration for ledger mode."""
    recharge = "recharge"      # 充值
    pay = "pay"                # 支付
    refund = "refund"          # 退款
    adjust = "adjust"          # 调整
    issue = "issue"            # 发卡
    void = "void"              # 作废
    expire = "expire"          # 过期
    loan_issue = "loan_issue"  # 发放垫资（名义本金入账）
    loan_fee = "loan_fee"      # 扣除手续费
    stock_buy = "stock_buy"    # 购买股票


class Transaction(Base):
    """
    Transaction record model (Ledger Append-Only Mode).
    
    账本追加模式：所有交易都是追加记录，不可修改。
    每条记录包含交易前后余额，形成完整的审计链。
    所有金额以"元"为单位。
    
    Attributes:
        id: Auto-incrementing primary key
        uid: Reference to user who performed transaction
        card_uid: Card UID
        type: Transaction type
        amount: Transaction amount in yuan (元, always positive)
        balance_before: Account balance before transaction (元)
        balance_after: Account balance after transaction (元)
        merchant_id: Optional merchant identifier
        related_txn_id: Related transaction ID (for refunds)
        remark: Optional transaction remark
        operator_id: Optional operator ID
        created_at: Transaction timestamp
    """
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # User identification (legacy)
    uid = Column(
        String(32),
        nullable=True,
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
    
    # Transaction details - amounts in 元 (yuan)
    type = Column(String(20), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False, comment='金额（元）')
    balance_before = Column(
        Numeric(12, 2), nullable=False, default=Decimal('0.00'),
        comment='交易前余额（元）'
    )
    balance_after = Column(Numeric(12, 2), nullable=False, comment='交易后余额（元）')
    
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
            "type IN ('recharge', 'pay', 'refund', 'adjust', 'issue', 'void', 'expire', 'loan_issue', 'loan_fee', 'stock_buy')",
            name='chk_transaction_type'
        ),
        CheckConstraint('amount > 0', name='chk_amount_positive'),
        CheckConstraint('balance_before >= 0', name='chk_balance_before_non_negative'),
        CheckConstraint('balance_after >= 0', name='chk_balance_after_non_negative'),
    )
    
    def __repr__(self):
        return (
            f"<Transaction(id={self.id}, uid='{self.uid}', type='{self.type}', "
            f"amount={self.amount}, balance: {self.balance_before} → {self.balance_after})>"
        )
    
    @property
    def amount_yuan(self) -> float:
        """Get amount as float (backward compatibility)."""
        return float(self.amount)
    
    @property
    def balance_before_yuan(self) -> float:
        """Get balance_before as float."""
        return float(self.balance_before)
    
    @property
    def balance_after_yuan(self) -> float:
        """Get balance_after as float."""
        return float(self.balance_after)
