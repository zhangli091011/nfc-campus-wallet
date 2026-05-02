"""
Merchant ORM model for NFC Campus E-Wallet System.

Represents merchants authorized to receive payments.
"""

from sqlalchemy import Column, String, Boolean

from core.database import Base


class Merchant(Base):
    """
    Merchant record model.
    
    Attributes:
        merchant_id: Primary key - unique merchant identifier
        name: Merchant name
        is_active: Whether the merchant is currently active and can receive payments
    """
    __tablename__ = 'merchants'
    
    merchant_id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    
    def __repr__(self):
        return f"<Merchant(merchant_id='{self.merchant_id}', name='{self.name}', is_active={self.is_active})>"
