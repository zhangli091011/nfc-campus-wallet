"""
Product schemas for Booth Management System.

Pydantic models for product-related requests and responses.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class ProductCreate(BaseModel):
    """Schema for creating a new product."""
    booth_id: int = Field(..., description="Booth ID the product belongs to")
    name: str = Field(..., min_length=1, max_length=100, description="Product name")
    price: int = Field(..., ge=0, description="Selling price in cents (分)")
    cost_price: Optional[int] = Field(None, ge=0, description="Cost price in cents (分)")
    stock: Optional[int] = Field(None, ge=0, description="Stock quantity (null means unlimited)")
    
    @field_validator("price")
    @classmethod
    def validate_price_non_negative(cls, v):
        """Validate price is non-negative."""
        if v < 0:
            raise ValueError("price must be non-negative")
        return v
    
    @field_validator("cost_price")
    @classmethod
    def validate_cost_price_non_negative(cls, v):
        """Validate cost_price is non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError("cost_price must be non-negative")
        return v
    
    @field_validator("stock")
    @classmethod
    def validate_stock_non_negative(cls, v):
        """Validate stock is non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError("stock must be non-negative")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "booth_id": 1,
                "name": "奶茶",
                "price": 500,
                "cost_price": 300,
                "stock": 100
            }
        }


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Product name")
    price: Optional[int] = Field(None, ge=0, description="Selling price in cents (分)")
    cost_price: Optional[int] = Field(None, ge=0, description="Cost price in cents (分)")
    stock: Optional[int] = Field(None, ge=0, description="Stock quantity")
    enabled: Optional[bool] = Field(None, description="Whether product is enabled for sale")
    
    @field_validator("price")
    @classmethod
    def validate_price_non_negative(cls, v):
        """Validate price is non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError("price must be non-negative")
        return v
    
    @field_validator("cost_price")
    @classmethod
    def validate_cost_price_non_negative(cls, v):
        """Validate cost_price is non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError("cost_price must be non-negative")
        return v
    
    @field_validator("stock")
    @classmethod
    def validate_stock_non_negative(cls, v):
        """Validate stock is non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError("stock must be non-negative")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "奶茶",
                "price": 600,
                "cost_price": 350,
                "stock": 80,
                "enabled": True
            }
        }


class ProductResponse(BaseModel):
    """Schema for product response."""
    id: int
    booth_id: int
    name: str
    price: int
    cost_price: Optional[int]
    stock: Optional[int]
    enabled: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "booth_id": 1,
                "name": "奶茶",
                "price": 500,
                "cost_price": 300,
                "stock": 100,
                "enabled": True,
                "created_at": "2024-03-01T08:00:00Z"
            }
        }
