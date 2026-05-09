"""
Event schemas for NFC Campus Event Quota System.

Pydantic models for event-related requests and responses.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class EventStatus(str, Enum):
    """Event status enumeration."""
    draft = "draft"
    active = "active"
    paused = "paused"
    ended = "ended"


class ExpireRule(str, Enum):
    """Quota expiration rule enumeration."""
    event_end = "event_end"
    never = "never"
    custom = "custom"


class EventCreate(BaseModel):
    """Schema for creating a new event."""
    name: str = Field(..., min_length=1, max_length=255, description="Event name")
    start_date: datetime = Field(..., description="Event start date")
    end_date: datetime = Field(..., description="Event end date")
    status: str = Field(default="active", description="Event status (active/inactive/closed)")
    allow_recharge: bool = Field(default=True, description="Whether recharge is allowed")
    allow_payment: bool = Field(default=True, description="Whether payment is allowed")
    
    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v, info):
        """Validate end_date is after start_date."""
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError("end_date must be after start_date")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "2026春季校园美食节",
                "start_date": "2026-05-01T00:00:00Z",
                "end_date": "2026-05-31T23:59:59Z",
                "status": "active",
                "allow_recharge": True,
                "allow_payment": True
            }
        }


class EventUpdate(BaseModel):
    """Schema for updating an event."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Event name")
    start_date: Optional[datetime] = Field(None, description="Event start date")
    end_date: Optional[datetime] = Field(None, description="Event end date")
    status: Optional[str] = Field(None, description="Event status (active/inactive/closed)")
    allow_recharge: Optional[bool] = Field(None, description="Whether recharge is allowed")
    allow_payment: Optional[bool] = Field(None, description="Whether payment is allowed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "active",
                "allow_recharge": True,
                "allow_payment": True
            }
        }


class EventResponse(BaseModel):
    """Schema for event response."""
    id: int
    name: str
    start_date: datetime
    end_date: datetime
    status: str
    allow_recharge: bool
    allow_payment: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "2026春季校园美食节",
                "start_date": "2026-05-01T00:00:00Z",
                "end_date": "2026-05-31T23:59:59Z",
                "status": "active",
                "allow_recharge": True,
                "allow_payment": True,
                "created_at": "2026-05-08T10:00:00Z",
                "updated_at": "2026-05-08T10:00:00Z"
            }
        }


class EventListResponse(BaseModel):
    """Schema for event list response."""
    events: List[EventResponse]
    total_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "events": [
                    {
                        "id": 1,
                        "name": "2024春季校园美食节",
                        "start_date": "2024-03-01T00:00:00Z",
                        "end_date": "2024-03-03T23:59:59Z",
                        "status": "active",
                        "allow_recharge": True,
                        "allow_payment": True,
                        "created_at": "2024-02-01T10:00:00Z",
                        "updated_at": "2024-02-01T10:00:00Z"
                    }
                ],
                "total_count": 1
            }
        }
