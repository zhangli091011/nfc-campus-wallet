"""
交易相关 DTO 模型 for NFC Campus Event Quota System (Event Mode).

定义交易相关的请求/响应模型，支持活动额度系统。
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum


class TransactionTypeEnum(str, Enum):
    """交易类型枚举"""
    recharge = "recharge"  # 充值
    pay = "pay"            # 支付
    refund = "refund"      # 退款
    adjust = "adjust"      # 调整
    issue = "issue"        # 发卡
    void = "void"          # 作废
    expire = "expire"      # 过期


class PaymentRequest(BaseModel):
    """支付请求模型（支持活动模式和传统模式）"""
    # Event mode fields (optional)
    event_id: Optional[int] = Field(None, description="Event ID (for event mode)")
    card_uid: Optional[str] = Field(None, description="NFC card UID (for event mode)")
    
    # Legacy mode field (optional)
    uid: Optional[str] = Field(None, description="User UID (for legacy mode)")
    
    # Common fields
    amount: float = Field(..., description="Payment amount in yuan", gt=0)
    timestamp: int = Field(..., description="Request timestamp in Unix seconds")
    signature: str = Field(..., description="Request signature for authentication")
    merchant_id: Optional[str] = Field(None, description="Optional merchant identifier")
    remark: Optional[str] = Field(None, max_length=255, description="Optional transaction remark")
    
    # Booth management fields (optional)
    booth_id: Optional[int] = Field(None, description="Booth ID (for booth management)")
    product_id: Optional[int] = Field(None, description="Product ID (optional, for booth management)")
    
    @field_validator("card_uid")
    @classmethod
    def validate_card_uid_format(cls, v):
        """Validate card_uid is hexadecimal format."""
        if v is None:
            return v
        if not v:
            raise ValueError("card_uid cannot be empty")
        if not all(c in "0123456789ABCDEFabcdef" for c in v):
            raise ValueError("card_uid must be a hexadecimal string")
        return v.upper()
    
    def model_post_init(self, __context):
        """Validate that either event mode or legacy mode fields are provided, but not both."""
        event_mode = self.event_id is not None or self.card_uid is not None
        legacy_mode = self.uid is not None
        
        if event_mode and legacy_mode:
            raise ValueError("Cannot specify both event mode (event_id, card_uid) and legacy mode (uid) fields")
        
        if not event_mode and not legacy_mode:
            raise ValueError("Must specify either event mode (event_id, card_uid) or legacy mode (uid) fields")
        
        # If event mode, both event_id and card_uid must be present
        if event_mode:
            if self.event_id is None or self.card_uid is None:
                raise ValueError("event_id and card_uid must both be present for event mode")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "event_id": 1,
                    "card_uid": "A1B2C3D4",
                    "amount": 25.00,
                    "timestamp": 1234567890,
                    "signature": "abc123...",
                    "merchant_id": "MERCHANT001",
                    "remark": "购买商品",
                    "booth_id": 1,
                    "product_id": 5
                },
                {
                    "uid": "A1B2C3D4",
                    "amount": 25.00,
                    "timestamp": 1234567890,
                    "signature": "abc123...",
                    "merchant_id": "MERCHANT001",
                    "remark": "购买商品"
                }
            ]
        }


class RechargeRequest(BaseModel):
    """充值请求模型（支持活动模式和传统模式）"""
    # Event mode fields (optional)
    event_id: Optional[int] = Field(None, description="Event ID (for event mode)")
    card_uid: Optional[str] = Field(None, description="NFC card UID (for event mode)")
    
    # Legacy mode field (optional)
    uid: Optional[str] = Field(None, description="User UID (for legacy mode)")
    
    # Common fields
    amount: float = Field(..., description="Recharge amount in yuan", gt=0)
    timestamp: Optional[int] = Field(None, description="Request timestamp in Unix seconds (legacy mode)")
    signature: Optional[str] = Field(None, description="Request signature for authentication (legacy mode)")
    operator_id: Optional[str] = Field(None, max_length=64, description="Optional operator ID")
    remark: Optional[str] = Field(None, max_length=255, description="Optional transaction remark")
    
    @field_validator("card_uid")
    @classmethod
    def validate_card_uid_format(cls, v):
        """Validate card_uid is hexadecimal format."""
        if v is None:
            return v
        if not v:
            raise ValueError("card_uid cannot be empty")
        if not all(c in "0123456789ABCDEFabcdef" for c in v):
            raise ValueError("card_uid must be a hexadecimal string")
        return v.upper()
    
    def model_post_init(self, __context):
        """Validate that either event mode or legacy mode fields are provided, but not both."""
        event_mode = self.event_id is not None or self.card_uid is not None
        legacy_mode = self.uid is not None
        
        if event_mode and legacy_mode:
            raise ValueError("Cannot specify both event mode (event_id, card_uid) and legacy mode (uid) fields")
        
        if not event_mode and not legacy_mode:
            raise ValueError("Must specify either event mode (event_id, card_uid) or legacy mode (uid) fields")
        
        # If event mode, both event_id and card_uid must be present
        if event_mode:
            if self.event_id is None or self.card_uid is None:
                raise ValueError("event_id and card_uid must both be present for event mode")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "event_id": 1,
                    "card_uid": "A1B2C3D4",
                    "amount": 50.00,
                    "timestamp": 1234567890,
                    "signature": "abc123...",
                    "operator_id": "ADMIN001",
                    "remark": "现金充值"
                },
                {
                    "uid": "A1B2C3D4",
                    "amount": 50.00,
                    "timestamp": 1234567890,
                    "signature": "abc123...",
                    "operator_id": "ADMIN001",
                    "remark": "现金充值"
                }
            ]
        }


class BalanceQueryRequest(BaseModel):
    """余额查询请求模型（支持活动模式和传统模式）"""
    # Event mode fields (optional)
    event_id: Optional[int] = Field(None, description="Event ID (for event mode)")
    card_uid: Optional[str] = Field(None, description="NFC card UID (for event mode)")
    
    # Legacy mode field (optional)
    uid: Optional[str] = Field(None, description="User UID (for legacy mode)")
    
    @field_validator("card_uid")
    @classmethod
    def validate_card_uid_format(cls, v):
        """Validate card_uid is hexadecimal format."""
        if v is None:
            return v
        if not v:
            raise ValueError("card_uid cannot be empty")
        if not all(c in "0123456789ABCDEFabcdef" for c in v):
            raise ValueError("card_uid must be a hexadecimal string")
        return v.upper()
    
    def model_post_init(self, __context):
        """Validate that either event mode or legacy mode fields are provided, but not both."""
        event_mode = self.event_id is not None or self.card_uid is not None
        legacy_mode = self.uid is not None
        
        if event_mode and legacy_mode:
            raise ValueError("Cannot specify both event mode (event_id, card_uid) and legacy mode (uid) fields")
        
        if not event_mode and not legacy_mode:
            raise ValueError("Must specify either event mode (event_id, card_uid) or legacy mode (uid) fields")
        
        # If event mode, both event_id and card_uid must be present
        if event_mode:
            if self.event_id is None or self.card_uid is None:
                raise ValueError("event_id and card_uid must both be present for event mode")


class TransactionResponse(BaseModel):
    """交易响应模型（兼容旧版）"""
    success: bool
    new_balance: float = Field(..., description="New balance in yuan")
    transaction_id: int
    balance_before: Optional[float] = Field(None, description="Balance before transaction in yuan")
    event_id: Optional[int] = Field(None, description="Event ID")
    participant_id: Optional[int] = Field(None, description="Participant ID")
    booth_id: Optional[int] = Field(None, description="Booth ID")
    product_id: Optional[int] = Field(None, description="Product ID")
    operator_id: Optional[int] = Field(None, description="Operator User ID")
    # 随机立减字段
    discount_applied: bool = Field(False, description="Whether random discount was applied")
    discount_amount: Optional[float] = Field(None, description="Discount amount in yuan")
    original_amount: Optional[float] = Field(None, description="Original payment amount before discount in yuan")
    actual_amount: Optional[float] = Field(None, description="Actual charged amount after discount in yuan")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "new_balance": 75.50,
                "transaction_id": 12345,
                "balance_before": 100.50,
                "event_id": 1,
                "participant_id": 1,
                "booth_id": 1,
                "product_id": 5,
                "operator_id": 3,
                "discount_applied": True,
                "discount_amount": 2.50,
                "original_amount": 25.00,
                "actual_amount": 22.50
            }
        }


class BalanceResponse(BaseModel):
    """余额响应模型（活动模式）"""
    balance: float = Field(..., description="Balance in yuan")
    event_id: int
    event_name: str
    participant_id: int
    participant_name: str
    card_uid: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "balance": 100.50,
                "event_id": 1,
                "event_name": "2024春季校园美食节",
                "participant_id": 1,
                "participant_name": "张三",
                "card_uid": "A1B2C3D4"
            }
        }


class TransactionItem(BaseModel):
    """交易记录项模型（账本模式）"""
    id: int
    type: str
    amount: float = Field(..., description="Amount in yuan")
    balance_before: float = Field(..., description="Balance before transaction in yuan")
    balance_after: float = Field(..., description="Balance after transaction in yuan")
    event_id: Optional[int] = None
    participant_id: Optional[int] = None
    merchant_id: Optional[str] = None
    related_txn_id: Optional[int] = None
    remark: Optional[str] = None
    operator_id: Optional[str] = None
    booth_id: Optional[int] = None
    product_id: Optional[int] = None
    booth_operator_id: Optional[int] = None
    created_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 12345,
                "type": "pay",
                "amount": 25.00,
                "balance_before": 100.50,
                "balance_after": 75.50,
                "event_id": 1,
                "participant_id": 1,
                "merchant_id": "MERCHANT001",
                "related_txn_id": None,
                "remark": "购买商品",
                "operator_id": None,
                "booth_id": 1,
                "product_id": 5,
                "booth_operator_id": 3,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


class TransactionHistoryResponse(BaseModel):
    """交易历史响应模型"""
    transactions: List[TransactionItem]
    total_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "transactions": [
                    {
                        "id": 12345,
                        "type": "pay",
                        "amount": 25.00,
                        "balance_before": 100.50,
                        "balance_after": 75.50,
                        "event_id": 1,
                        "participant_id": 1,
                        "merchant_id": "MERCHANT001",
                        "related_txn_id": None,
                        "remark": "购买商品",
                        "operator_id": None,
                        "created_at": "2024-01-15T10:30:00Z"
                    }
                ],
                "total_count": 1
            }
        }


class RefundRequest(BaseModel):
    """退款请求模型（预留）"""
    event_id: int = Field(..., description="Event ID")
    card_uid: str = Field(..., description="NFC card UID")
    original_txn_id: int = Field(..., description="Original transaction ID to refund")
    amount: Optional[float] = Field(None, description="Refund amount (if partial refund)", gt=0)
    timestamp: int = Field(..., description="Request timestamp in Unix seconds")
    signature: str = Field(..., description="Request signature for authentication")
    operator_id: Optional[str] = Field(None, max_length=64, description="Operator ID")
    remark: Optional[str] = Field(None, max_length=255, description="Refund reason")
    
    @field_validator("card_uid")
    @classmethod
    def validate_card_uid_format(cls, v):
        """Validate card_uid is hexadecimal format."""
        if not v:
            raise ValueError("card_uid cannot be empty")
        if not all(c in "0123456789ABCDEFabcdef" for c in v):
            raise ValueError("card_uid must be a hexadecimal string")
        return v.upper()
