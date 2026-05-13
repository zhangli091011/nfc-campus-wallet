"""
Random Discount routes for NFC Campus E-Wallet System.

随机立减管理 API 端点：配置管理、统计查询、记录查询。
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel, Field
import logging

from core.database import get_db
from core.security import get_current_user, RoleChecker
from services.random_discount_service import RandomDiscountService
from models.user import User
from core.exceptions import ValidationError, ResourceNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/random-discount", tags=["random-discount"])


# ==================== Request/Response Models ====================

class DiscountSettingRequest(BaseModel):
    """随机立减配置请求"""
    event_id: int = Field(..., description="活动ID")
    enabled: bool = Field(False, description="是否启用")
    min_discount_amount: float = Field(0.01, description="最小立减金额（元）", ge=0)
    max_discount_amount: float = Field(5.00, description="最大立减金额（元）", gt=0)
    probability: int = Field(100, description="触发概率（1-100）", ge=1, le=100)
    total_pool: float = Field(1000.00, description="总奖池金额（元）", gt=0)
    max_discount_per_transaction: Optional[float] = Field(None, description="单笔最大立减金额（元）")
    min_payment_amount: float = Field(1.00, description="触发立减的最低消费金额（元）", ge=0)
    daily_limit_per_user: Optional[int] = Field(None, description="每人每日最多享受次数")


class DiscountSettingResponse(BaseModel):
    """随机立减配置响应"""
    id: int
    event_id: int
    enabled: bool
    min_discount_amount: float
    max_discount_amount: float
    probability: int
    total_pool: float
    remaining_pool: float
    max_discount_per_transaction: Optional[float]
    min_payment_amount: float
    daily_limit_per_user: Optional[int]
    created_at: str
    updated_at: str


class ResetPoolRequest(BaseModel):
    """重置奖池请求"""
    new_pool: Optional[float] = Field(None, description="新的奖池金额（元），不填则重置为总奖池金额")


# ==================== API Endpoints ====================

@router.get("/settings/{event_id}")
async def get_discount_setting(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取活动的随机立减配置。
    
    需要管理员权限。
    """
    if current_user.role not in ('super_admin', 'event_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view discount settings"
        )
    
    service = RandomDiscountService(db)
    setting = service.get_setting(event_id)
    
    if setting is None:
        return {
            "configured": False,
            "event_id": event_id,
            "message": "No discount setting configured for this event"
        }
    
    return {
        "configured": True,
        "id": setting.id,
        "event_id": setting.event_id,
        "enabled": setting.enabled,
        "min_discount_amount": float(setting.min_discount_amount),
        "max_discount_amount": float(setting.max_discount_amount),
        "probability": setting.probability,
        "total_pool": float(setting.total_pool),
        "remaining_pool": float(setting.remaining_pool),
        "max_discount_per_transaction": float(setting.max_discount_per_transaction) if setting.max_discount_per_transaction else None,
        "min_payment_amount": float(setting.min_payment_amount),
        "daily_limit_per_user": setting.daily_limit_per_user,
        "created_at": setting.created_at.isoformat() if setting.created_at else None,
        "updated_at": setting.updated_at.isoformat() if setting.updated_at else None
    }


@router.post("/settings")
async def create_or_update_discount_setting(
    request: DiscountSettingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建或更新随机立减配置。
    
    需要超级管理员或活动管理员权限。
    """
    if current_user.role not in ('super_admin', 'event_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can manage discount settings"
        )
    
    try:
        service = RandomDiscountService(db)
        setting = service.create_or_update_setting(
            event_id=request.event_id,
            enabled=request.enabled,
            min_discount_amount=request.min_discount_amount,
            max_discount_amount=request.max_discount_amount,
            probability=request.probability,
            total_pool=request.total_pool,
            max_discount_per_transaction=request.max_discount_per_transaction,
            min_payment_amount=request.min_payment_amount,
            daily_limit_per_user=request.daily_limit_per_user
        )
        
        return {
            "success": True,
            "message": "Discount setting saved successfully",
            "id": setting.id,
            "event_id": setting.event_id,
            "enabled": setting.enabled,
            "min_discount_amount": float(setting.min_discount_amount),
            "max_discount_amount": float(setting.max_discount_amount),
            "probability": setting.probability,
            "total_pool": float(setting.total_pool),
            "remaining_pool": float(setting.remaining_pool),
            "max_discount_per_transaction": float(setting.max_discount_per_transaction) if setting.max_discount_per_transaction else None,
            "min_payment_amount": float(setting.min_payment_amount),
            "daily_limit_per_user": setting.daily_limit_per_user
        }
    
    except ValidationError as e:
        return JSONResponse(
            status_code=400,
            content={"error_code": e.error_code, "message": e.message}
        )


@router.post("/settings/{event_id}/reset-pool")
async def reset_discount_pool(
    event_id: int,
    request: ResetPoolRequest = ResetPoolRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    重置奖池金额。
    
    需要超级管理员权限。
    """
    if current_user.role != 'super_admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can reset discount pool"
        )
    
    try:
        service = RandomDiscountService(db)
        setting = service.reset_pool(event_id, request.new_pool)
        
        return {
            "success": True,
            "message": "Pool reset successfully",
            "total_pool": float(setting.total_pool),
            "remaining_pool": float(setting.remaining_pool)
        }
    
    except ResourceNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error_code": e.error_code, "message": e.message}
        )


@router.get("/statistics/{event_id}")
async def get_discount_statistics(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取随机立减统计信息。
    
    需要管理员权限。
    """
    if current_user.role not in ('super_admin', 'event_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view discount statistics"
        )
    
    service = RandomDiscountService(db)
    stats = service.get_statistics(event_id)
    return stats


@router.get("/records/{event_id}")
async def get_discount_records(
    event_id: int,
    participant_id: Optional[int] = Query(None, description="按参与者筛选"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取随机立减记录列表。
    
    需要管理员权限。
    """
    if current_user.role not in ('super_admin', 'event_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view discount records"
        )
    
    service = RandomDiscountService(db)
    result = service.get_records(
        event_id=event_id,
        participant_id=participant_id,
        limit=limit,
        offset=offset
    )
    return result
