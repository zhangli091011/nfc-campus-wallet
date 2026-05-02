"""
Leaderboard endpoints for NFC Campus E-Wallet System.

Provides leaderboard endpoints for booths and products.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import logging

from core.database import get_db
from services.report_service import ReportService
from schemas.report import LeaderboardResponse, ProductLeaderboardResponse
from middleware.auth import require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/leaderboard")


# ============================================================================
# Revenue Leaderboard
# ============================================================================

@router.get(
    "/revenue",
    response_model=LeaderboardResponse,
    summary="获取营业额排行榜"
)
async def get_revenue_leaderboard(
    event_id: Optional[int] = Query(None, description="活动ID（可选）"),
    limit: int = Query(10, description="返回数量限制", ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["super_admin", "event_admin", "reviewer"]))
):
    """
    获取营业额排行榜（TOP N）。
    
    按摊位营业额降序排序。
    
    权限要求：super_admin, event_admin, reviewer
    """
    try:
        report_service = ReportService(db)
        leaderboard = report_service.get_revenue_leaderboard(event_id, limit)
        
        logger.info(
            f"Revenue leaderboard retrieved by user {current_user.username} "
            f"for event_id={event_id}, limit={limit}"
        )
        
        return leaderboard
    
    except Exception as e:
        logger.error(f"Error retrieving revenue leaderboard: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve revenue leaderboard")


# ============================================================================
# Profit Leaderboard
# ============================================================================

@router.get(
    "/profit",
    response_model=LeaderboardResponse,
    summary="获取利润排行榜"
)
async def get_profit_leaderboard(
    event_id: Optional[int] = Query(None, description="活动ID（可选）"),
    limit: int = Query(10, description="返回数量限制", ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["super_admin", "event_admin", "reviewer"]))
):
    """
    获取利润排行榜（TOP N）。
    
    按摊位利润降序排序。
    
    权限要求：super_admin, event_admin, reviewer
    """
    try:
        report_service = ReportService(db)
        leaderboard = report_service.get_profit_leaderboard(event_id, limit)
        
        logger.info(
            f"Profit leaderboard retrieved by user {current_user.username} "
            f"for event_id={event_id}, limit={limit}"
        )
        
        return leaderboard
    
    except Exception as e:
        logger.error(f"Error retrieving profit leaderboard: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve profit leaderboard")


# ============================================================================
# ROI (Profit Margin) Leaderboard
# ============================================================================

@router.get(
    "/roi",
    response_model=LeaderboardResponse,
    summary="获取利润率排行榜"
)
async def get_roi_leaderboard(
    event_id: Optional[int] = Query(None, description="活动ID（可选）"),
    limit: int = Query(10, description="返回数量限制", ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["super_admin", "event_admin", "reviewer"]))
):
    """
    获取利润率排行榜（TOP N）。
    
    按摊位利润率降序排序。
    
    权限要求：super_admin, event_admin, reviewer
    """
    try:
        report_service = ReportService(db)
        leaderboard = report_service.get_roi_leaderboard(event_id, limit)
        
        logger.info(
            f"ROI leaderboard retrieved by user {current_user.username} "
            f"for event_id={event_id}, limit={limit}"
        )
        
        return leaderboard
    
    except Exception as e:
        logger.error(f"Error retrieving ROI leaderboard: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve ROI leaderboard")


# ============================================================================
# Product Leaderboard
# ============================================================================

@router.get(
    "/products",
    response_model=ProductLeaderboardResponse,
    summary="获取商品排行榜"
)
async def get_product_leaderboard(
    metric: str = Query("sales", description="排序指标（sales=销量, revenue=收入, profit=利润）"),
    event_id: Optional[int] = Query(None, description="活动ID（可选）"),
    limit: int = Query(10, description="返回数量限制", ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["super_admin", "event_admin", "reviewer"]))
):
    """
    获取商品排行榜（TOP N）。
    
    支持的排序指标：
    - sales: 销量（件数）
    - revenue: 收入（元）
    - profit: 利润（元）
    
    权限要求：super_admin, event_admin, reviewer
    """
    try:
        report_service = ReportService(db)
        leaderboard = report_service.get_product_leaderboard(metric, event_id, limit)
        
        logger.info(
            f"Product leaderboard retrieved by user {current_user.username} "
            f"for metric={metric}, event_id={event_id}, limit={limit}"
        )
        
        return leaderboard
    
    except ValueError as e:
        logger.warning(f"Invalid product leaderboard request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error retrieving product leaderboard: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve product leaderboard")
