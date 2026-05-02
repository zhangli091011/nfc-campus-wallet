"""
Booth schemas for Booth Management System.

Pydantic models for booth-related requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class BoothStatus(str, Enum):
    """Booth status enumeration."""
    active = "active"
    inactive = "inactive"
    closed = "closed"


class BoothCreate(BaseModel):
    """Schema for creating a new booth."""
    event_id: int = Field(..., description="Event ID the booth belongs to")
    name: str = Field(..., min_length=1, max_length=100, description="Booth name")
    class_name: str = Field(..., min_length=1, max_length=100, description="Class or team name operating the booth")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": 1,
                "name": "美食摊",
                "class_name": "高一(1)班"
            }
        }


class BoothUpdate(BaseModel):
    """Schema for updating a booth."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Booth name")
    class_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Class or team name")
    status: Optional[BoothStatus] = Field(None, description="Booth status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "美食摊",
                "class_name": "高一(2)班",
                "status": "active"
            }
        }


class BoothResponse(BaseModel):
    """Schema for booth response."""
    id: int
    event_id: int
    name: str
    class_name: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "event_id": 1,
                "name": "美食摊",
                "class_name": "高一(1)班",
                "status": "active",
                "created_at": "2024-03-01T08:00:00Z"
            }
        }
