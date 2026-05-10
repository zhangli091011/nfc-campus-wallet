"""
Participant schemas for NFC Campus Event Quota System.

Pydantic models for participant-related requests and responses.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ParticipantStatus(str, Enum):
    """Participant status enumeration."""
    active = "active"
    inactive = "inactive"
    blocked = "blocked"


class ParticipantCreate(BaseModel):
    """Schema for creating a new participant."""
    name: str = Field(..., min_length=1, max_length=100, description="Participant name")
    class_name: Optional[str] = Field(None, max_length=100, description="Class name")
    student_no: Optional[str] = Field(None, max_length=50, description="Student number")
    card_uid: str = Field(..., min_length=1, max_length=32, description="NFC card UID")
    status: ParticipantStatus = Field(default=ParticipantStatus.active, description="Participant status")
    
    @field_validator("card_uid")
    @classmethod
    def validate_card_uid_format(cls, v):
        """Validate card_uid is hexadecimal format."""
        if not v:
            raise ValueError("card_uid cannot be empty")
        if not all(c in "0123456789ABCDEFabcdef" for c in v):
            raise ValueError("card_uid must be a hexadecimal string")
        return v.upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "张三",
                "class_name": "高一(1)班",
                "student_no": "2024001",
                "card_uid": "A1B2C3D4",
                "status": "active"
            }
        }


class ParticipantUpdate(BaseModel):
    """Schema for updating a participant."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Participant name")
    class_name: Optional[str] = Field(None, max_length=100, description="Class name")
    student_no: Optional[str] = Field(None, max_length=50, description="Student number")
    status: Optional[ParticipantStatus] = Field(None, description="Participant status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "张三",
                "class_name": "高一(2)班",
                "status": "active"
            }
        }


class CardBindRequest(BaseModel):
    """Schema for binding a card to a participant."""
    participant_id: int = Field(..., description="Participant ID")
    card_uid: str = Field(..., min_length=1, max_length=32, description="NFC card UID")
    
    @field_validator("card_uid")
    @classmethod
    def validate_card_uid_format(cls, v):
        """Validate card_uid is hexadecimal format."""
        if not v:
            raise ValueError("card_uid cannot be empty")
        if not all(c in "0123456789ABCDEFabcdef" for c in v):
            raise ValueError("card_uid must be a hexadecimal string")
        return v.upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "participant_id": 1,
                "card_uid": "A1B2C3D4"
            }
        }


class ParticipantResponse(BaseModel):
    """Schema for participant response."""
    id: int
    name: str
    class_name: Optional[str]
    student_no: Optional[str]
    card_uid: str
    status: str
    is_verified: bool = False
    display_name: str = ""
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "张三",
                "class_name": "高一(1)班",
                "student_no": "2024001",
                "card_uid": "A1B2C3D4",
                "status": "active",
                "is_verified": True,
                "display_name": "张三",
                "created_at": "2024-02-01T10:00:00Z",
                "updated_at": "2024-02-01T10:00:00Z"
            }
        }


class ParticipantWithAccountsResponse(BaseModel):
    """Schema for participant response with accounts."""
    id: int
    name: str
    class_name: Optional[str]
    student_no: Optional[str]
    card_uid: str
    status: str
    created_at: datetime
    updated_at: datetime
    accounts: List[dict] = []
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "张三",
                "class_name": "高一(1)班",
                "student_no": "2024001",
                "card_uid": "A1B2C3D4",
                "status": "active",
                "created_at": "2024-02-01T10:00:00Z",
                "updated_at": "2024-02-01T10:00:00Z",
                "accounts": [
                    {
                        "event_id": 1,
                        "event_name": "2024春季校园美食节",
                        "balance": 100.00
                    }
                ]
            }
        }


class ParticipantListResponse(BaseModel):
    """Schema for participant list response."""
    participants: List[ParticipantResponse]
    total_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "participants": [
                    {
                        "id": 1,
                        "name": "张三",
                        "class_name": "高一(1)班",
                        "student_no": "2024001",
                        "card_uid": "A1B2C3D4",
                        "status": "active",
                        "created_at": "2024-02-01T10:00:00Z",
                        "updated_at": "2024-02-01T10:00:00Z"
                    }
                ],
                "total_count": 1
            }
        }
