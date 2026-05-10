"""
用户相关 DTO 模型 for NFC Campus E-Wallet System.

定义用户相关的请求/响应模型。
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""
    super_admin = "super_admin"
    event_admin = "event_admin"
    booth_cashier = "booth_cashier"
    issuer = "issuer"
    reviewer = "reviewer"
    bank_clerk = "bank_clerk"  # 投资办理员（官方中央银行）
    merchant = "merchant"  # 商户（自主注册管理商铺）


class UserStatus(str, Enum):
    """User status enumeration."""
    active = "active"
    inactive = "inactive"
    blocked = "blocked"


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    username: str = Field(..., min_length=1, max_length=50, description="Username for login")
    password: str = Field(..., min_length=6, max_length=100, description="User password")
    role: UserRole = Field(..., description="User role")
    booth_id: Optional[int] = Field(None, description="Associated booth ID (required for booth_cashier)")
    
    @model_validator(mode='after')
    def validate_booth_id_for_cashier(self):
        """Validate booth_id is provided for booth_cashier role."""
        if self.role == UserRole.booth_cashier and self.booth_id is None:
            raise ValueError("booth_id is required for booth_cashier role")
        if self.role != UserRole.booth_cashier and self.booth_id is not None:
            raise ValueError("booth_id should only be set for booth_cashier role")
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "cashier01",
                "password": "password123",
                "role": "booth_cashier",
                "booth_id": 1
            }
        }


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    username: str
    role: str
    booth_id: Optional[int]
    staff_name: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "cashier01",
                "role": "booth_cashier",
                "booth_id": 1,
                "staff_name": "张三",
                "status": "active",
                "created_at": "2024-02-01T10:00:00Z"
            }
        }


class UserLogin(BaseModel):
    """Schema for user login request."""
    username: str = Field(..., min_length=1, max_length=50, description="Username")
    password: str = Field(..., min_length=1, max_length=100, description="Password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "password123"
            }
        }


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "username": "admin",
                    "role": "super_admin",
                    "booth_id": None,
                    "status": "active",
                    "created_at": "2024-02-01T10:00:00Z"
                }
            }
        }


class BalanceResponse(BaseModel):
    """余额查询响应"""
    balance: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "balance": 100.50
            }
        }


class SetStaffNameRequest(BaseModel):
    """Schema for setting staff name on first login."""
    staff_name: str = Field(..., min_length=1, max_length=50, description="工作人员真实姓名")
    
    class Config:
        json_schema_extra = {
            "example": {
                "staff_name": "张三"
            }
        }


class SetStaffNameResponse(BaseModel):
    """Schema for set staff name response."""
    message: str
    staff_name: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Staff name set successfully",
                "staff_name": "张三"
            }
        }
