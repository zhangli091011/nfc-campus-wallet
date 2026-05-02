"""
Account schemas for NFC Campus Event Quota System.

Pydantic models for account-related requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AccountResponse(BaseModel):
    """Schema for account response."""
    id: int
    participant_id: int
    event_id: int
    balance: float = Field(..., description="Balance in yuan")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "participant_id": 1,
                "event_id": 1,
                "balance": 100.00,
                "created_at": "2024-02-01T10:00:00Z",
                "updated_at": "2024-02-01T10:00:00Z"
            }
        }


class AccountDetailResponse(BaseModel):
    """Schema for detailed account response."""
    id: int
    participant_id: int
    participant_name: str
    card_uid: str
    event_id: int
    event_name: str
    event_status: str
    balance: float = Field(..., description="Balance in yuan")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "participant_id": 1,
                "participant_name": "张三",
                "card_uid": "A1B2C3D4",
                "event_id": 1,
                "event_name": "2024春季校园美食节",
                "event_status": "active",
                "balance": 100.00,
                "created_at": "2024-02-01T10:00:00Z",
                "updated_at": "2024-02-01T10:00:00Z"
            }
        }
