"""
User ORM model for Booth Management System.

Represents system users with roles and permissions.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from core.database import Base


class User(Base):
    """
    User model for booth management system.
    
    用户模型：管理系统用户账户，支持多种角色和基于角色的访问控制。
    
    Attributes:
        id: Auto-incrementing primary key
        username: Unique username for login
        password_hash: bcrypt hashed password
        role: User role (super_admin, event_admin, booth_cashier, issuer, reviewer)
        booth_id: Associated booth ID (required for booth_cashier role)
        status: User status (active, inactive, blocked)
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        booth: Relationship to Booth record (for booth_cashier)
        operated_transactions: Relationship to Transaction records operated by this user
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, index=True)
    booth_id = Column(Integer, ForeignKey('booths.id', ondelete='SET NULL'), nullable=True, index=True)
    staff_name = Column(String(50), nullable=True, default=None)
    status = Column(String(20), nullable=False, default='active')
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
    booth = relationship(
        "Booth",
        back_populates="cashiers",
        foreign_keys=[booth_id]
    )
    operated_transactions = relationship(
        "Transaction",
        back_populates="booth_operator",
        foreign_keys="Transaction.booth_operator_id"
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "role IN ('super_admin', 'event_admin', 'booth_cashier', 'issuer', 'reviewer', 'bank_clerk', 'merchant', 'school_inspector')",
            name='chk_user_role'
        ),
        CheckConstraint(
            "status IN ('active', 'inactive', 'blocked')",
            name='chk_user_status'
        ),
        CheckConstraint(
            "(role = 'booth_cashier' AND booth_id IS NOT NULL) OR (role != 'booth_cashier')",
            name='chk_booth_cashier_has_booth'
        ),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
    
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == 'active'
    
    def is_booth_cashier(self) -> bool:
        """Check if user is a booth cashier."""
        return self.role == 'booth_cashier'
    
    def is_bank_clerk(self) -> bool:
        """Check if user is a bank clerk (investment counter operator)."""
        return self.role == 'bank_clerk'
    
    def is_merchant(self) -> bool:
        """Check if user is a merchant (self-registered booth owner)."""
        return self.role == 'merchant'
    
    def is_admin(self) -> bool:
        """Check if user is an admin (super_admin or event_admin)."""
        return self.role in ('super_admin', 'event_admin')
    
    def can_access_booth(self, booth_id: int) -> bool:
        """
        Check if user can access a specific booth.
        
        Args:
            booth_id: The booth ID to check access for
            
        Returns:
            True if user can access the booth, False otherwise
        """
        # Admins can access all booths
        if self.is_admin():
            return True
        
        # Booth cashiers can only access their assigned booth
        if self.is_booth_cashier():
            return self.booth_id == booth_id
        
        # Other roles (issuer, reviewer) cannot access booth-specific data
        return False
