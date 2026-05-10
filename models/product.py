"""
Product ORM model for Booth Management System.

Represents products sold by booths in events.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from core.database import Base


class Product(Base):
    """
    Product model for booth product management.
    
    商品模型：代表摊位销售的商品，支持价格、成本和库存管理。
    每个商品属于一个摊位，可以在多个交易中出现。
    
    Attributes:
        id: Auto-incrementing primary key
        booth_id: Associated booth ID (foreign key to booths table)
        name: Product name (e.g., "奶茶", "汉堡")
        price: Selling price in cents (单位：分)
        cost_price: Cost price in cents (optional, 单位：分)
        stock: Stock quantity (null means unlimited stock)
        enabled: Whether product is enabled for sale
        created_at: Creation timestamp
        booth: Relationship to Booth record
        transactions: Relationship to Transaction records
    """
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    booth_id = Column(
        Integer,
        ForeignKey('booths.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    name = Column(String(100), nullable=False)
    price = Column(Integer, nullable=False, comment='售价（分）')
    cost_price = Column(Integer, nullable=True, comment='成本价（分）')
    stock = Column(Integer, nullable=True, comment='库存数量（null表示无限）')
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    booth = relationship(
        "Booth",
        back_populates="products"
    )
    transactions = relationship(
        "Transaction",
        back_populates="product",
        foreign_keys="Transaction.product_id"
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint('price >= 0', name='chk_price_non_negative'),
        CheckConstraint(
            'cost_price IS NULL OR cost_price >= 0',
            name='chk_cost_price_non_negative'
        ),
        CheckConstraint(
            'stock IS NULL OR stock >= 0',
            name='chk_stock_non_negative'
        ),
    )
    
    def __repr__(self):
        return (
            f"<Product(id={self.id}, booth_id={self.booth_id}, name='{self.name}', "
            f"price={self.price}, stock={self.stock}, enabled={self.enabled})>"
        )
    
    @property
    def price_yuan(self) -> float:
        """Get price in yuan (元) - 值已为元."""
        return float(self.price)
    
    @property
    def cost_price_yuan(self) -> float | None:
        """Get cost price in yuan (元) - 值已为元."""
        return float(self.cost_price) if self.cost_price is not None else None
    
    def is_available(self) -> bool:
        """
        Check if product is available for sale.
        
        Returns:
            True if product is enabled and has stock (or unlimited stock), False otherwise
        """
        if not self.enabled:
            return False
        
        # If stock is None, it means unlimited stock
        if self.stock is None:
            return True
        
        # Otherwise, check if stock is greater than 0
        return self.stock > 0
    
    def has_sufficient_stock(self, quantity: int = 1) -> bool:
        """
        Check if product has sufficient stock for a given quantity.
        
        Args:
            quantity: The quantity to check (default: 1)
            
        Returns:
            True if stock is sufficient or unlimited, False otherwise
        """
        # If stock is None, it means unlimited stock
        if self.stock is None:
            return True
        
        # Otherwise, check if stock is sufficient
        return self.stock >= quantity
    
    def calculate_profit(self) -> float | None:
        """
        Calculate profit per unit in yuan.
        
        Returns:
            Profit in yuan, or None if cost_price is not set
        """
        if self.cost_price is None:
            return None
        
        return float(self.price - self.cost_price)
    
    def calculate_profit_margin(self) -> float | None:
        """
        Calculate profit margin as a percentage.
        
        Returns:
            Profit margin percentage, or None if cost_price is not set or price is 0
        """
        if self.cost_price is None or self.price == 0:
            return None
        
        return ((self.price - self.cost_price) / self.price) * 100.0
