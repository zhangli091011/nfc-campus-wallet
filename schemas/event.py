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
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    status: EventStatus = Field(default=EventStatus.draft, description="Event status")
    recharge_enabled: bool = Field(default=True, description="Whether recharge is allowed")
    consume_enabled: bool = Field(default=True, description="Whether consumption is allowed")
    expire_rule: ExpireRule = Field(default=ExpireRule.event_end, description="Quota expiration rule")
    
    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v, info):
        """Validate end_time is after start_time."""
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError("end_time must be after start_time")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "2024春季校园美食节",
                "start_time": "2024-03-01T08:00:00Z",
                "end_time": "2024-03-03T20:00:00Z",
                "status": "draft",
                "recharge_enabled": True,
                "consume_enabled": True,
                "expire_rule": "event_end"
            }
        }


class EventUpdate(BaseModel):
    """Schema for updating an event."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Event name")
    start_time: Optional[datetime] = Field(None, description="Event start time")
    end_time: Optional[datetime] = Field(None, description="Event end time")
    status: Optional[EventStatus] = Field(None, description="Event status")
    recharge_enabled: Optional[bool] = Field(None, description="Whether recharge is allowed")
    consume_enabled: Optional[bool] = Field(None, description="Whether consumption is allowed")
    expire_rule: Optional[ExpireRule] = Field(None, description="Quota expiration rule")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "active",
                "recharge_enabled": True,
                "consume_enabled": True
            }
        }


class EventResponse(BaseModel):
    """Schema for event response."""
    id: int
    name: str
    start_time: datetime
    end_time: datetime
    status: str
    recharge_enabled: bool
    consume_enabled: bool
    expire_rule: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "2024春季校园美食节",
                "start_time": "2024-03-01T08:00:00Z",
                "end_time": "2024-03-03T20:00:00Z",
                "status": "active",
                "recharge_enabled": True,
                "consume_enabled": True,
                "expire_rule": "event_end",
                "created_at": "2024-02-01T10:00:00Z",
                "updated_at": "2024-02-01T10:00:00Z"
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
                        "start_time": "2024-03-01T08:00:00Z",
                        "end_time": "2024-03-03T20:00:00Z",
                        "status": "active",
                        "recharge_enabled": True,
                        "consume_enabled": True,
                        "expire_rule": "event_end",
                        "created_at": "2024-02-01T10:00:00Z",
                        "updated_at": "2024-02-01T10:00:00Z"
                    }
                ],
                "total_count": 1
            }
        }
