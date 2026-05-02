"""
Pydantic schemas for Cash Reconciliation API.

现金对账相关的数据验证模式。
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class CashReconciliationCreate(BaseModel):
    """现金对账创建请求"""
    booth_id: int = Field(..., description="摊位ID", gt=0)
    event_id: int = Field(..., description="活动ID", gt=0)
    expected_cash: float = Field(..., description="预期现金金额（元）", ge=0)
    actual_cash: float = Field(..., description="实际现金金额（元）", ge=0)
    reason: Optional[str] = Field(None, description="差额原因说明", max_length=1000)
    
    @field_validator('expected_cash', 'actual_cash')
    @classmethod
    def validate_amount(cls, v):
        """验证金额精度（最多2位小数）"""
        if round(v, 2) != v:
            raise ValueError('Amount must have at most 2 decimal places')
        return v


class CashReconciliationResponse(BaseModel):
    """现金对账响应"""
    id: int
    booth_id: int
    event_id: int
    expected_cash: float = Field(..., description="预期现金金额（元）")
    actual_cash: float = Field(..., description="实际现金金额（元）")
    diff_amount: float = Field(..., description="差额（元）")
    reason: Optional[str]
    reviewer_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class CashReconciliationListResponse(BaseModel):
    """现金对账列表响应"""
    reconciliations: list[CashReconciliationResponse]
    total_count: int
