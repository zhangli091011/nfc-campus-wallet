"""
Cash Reconciliation routes for NFC Campus Event System.

提供现金对账相关的 API 端点。
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from core.database import get_db
from core.security import get_current_user
from services.cash_reconciliation_service import CashReconciliationService
from schemas.cash_reconciliation import (
    CashReconciliationCreate,
    CashReconciliationResponse,
    CashReconciliationListResponse
)
from models.user import User
from core.exceptions import ResourceNotFoundError, ValidationError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/cash-reconciliation", response_model=CashReconciliationResponse, status_code=201)
async def create_cash_reconciliation(
    reconciliation_data: CashReconciliationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建现金对账记录。
    
    权限要求：super_admin 或 event_admin
    
    Request Body:
        - booth_id: 摊位ID（必填）
        - event_id: 活动ID（必填）
        - expected_cash: 预期现金金额（元，必填）
        - actual_cash: 实际现金金额（元，必填）
        - reason: 差额原因说明（可选）
    
    Returns:
        CashReconciliationResponse: 创建的对账记录
        
    Error Responses:
        400: 验证错误
        403: 权限不足
        404: 摊位或活动不存在
        500: 内部服务器错误
    """
    try:
        # 权限验证
        if current_user.role not in ('super_admin', 'event_admin'):
            logger.warning(
                f"Cash reconciliation creation denied: role '{current_user.role}' "
                f"(user={current_user.username})"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error_code": "PERMISSION_DENIED",
                    "message": f"Role '{current_user.role}' cannot create cash reconciliations"
                }
            )
        
        reconciliation_service = CashReconciliationService(db)
        
        reconciliation = reconciliation_service.create_reconciliation(
            booth_id=reconciliation_data.booth_id,
            event_id=reconciliation_data.event_id,
            expected_cash_yuan=reconciliation_data.expected_cash,
            actual_cash_yuan=reconciliation_data.actual_cash,
            reviewer_id=current_user.id,
            reason=reconciliation_data.reason
        )
        
        logger.info(
            f"Cash reconciliation created: id={reconciliation.id}, "
            f"booth_id={reconciliation_data.booth_id}, "
            f"reviewer={current_user.username}"
        )
        
        return CashReconciliationResponse(
            id=reconciliation.id,
            booth_id=reconciliation.booth_id,
            event_id=reconciliation.event_id,
            expected_cash=reconciliation.expected_cash_yuan,
            actual_cash=reconciliation.actual_cash_yuan,
            diff_amount=reconciliation.diff_amount_yuan,
            reason=reconciliation.reason,
            reviewer_id=reconciliation.reviewer_id,
            created_at=reconciliation.created_at
        )
    
    except (ResourceNotFoundError, ValidationError) as e:
        logger.warning(f"Cash reconciliation creation failed: {str(e)}")
        return JSONResponse(
            status_code=404 if isinstance(e, ResourceNotFoundError) else 400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in cash reconciliation creation: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )


@router.get("/cash-reconciliation", response_model=CashReconciliationListResponse)
async def list_cash_reconciliations(
    booth_id: Optional[int] = Query(None, description="Filter by booth ID"),
    event_id: Optional[int] = Query(None, description="Filter by event ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取现金对账记录列表。
    
    权限要求：super_admin、event_admin 或 booth_cashier（只能查看自己摊位的记录）
    
    Query Parameters:
        - booth_id: 摊位ID过滤（可选）
        - event_id: 活动ID过滤（可选）
        - limit: 返回记录数限制（默认100，最大1000）
        - offset: 偏移量（默认0）
    
    Returns:
        CashReconciliationListResponse: 对账记录列表和总数
        
    Error Responses:
        403: 权限不足
        500: 内部服务器错误
    """
    try:
        # 权限验证
        if current_user.role == 'booth_cashier':
            # booth_cashier 只能查看自己摊位的记录
            if booth_id is not None and booth_id != current_user.booth_id:
                logger.warning(
                    f"Cash reconciliation query denied: booth_cashier {current_user.username} "
                    f"attempted to view records for booth {booth_id}"
                )
                return JSONResponse(
                    status_code=403,
                    content={
                        "error_code": "PERMISSION_DENIED",
                        "message": f"You can only view records for booth {current_user.booth_id}"
                    }
                )
            # 强制使用自己的 booth_id
            booth_id = current_user.booth_id
        elif current_user.role not in ('super_admin', 'event_admin'):
            logger.warning(
                f"Cash reconciliation query denied: role '{current_user.role}' "
                f"(user={current_user.username})"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error_code": "PERMISSION_DENIED",
                    "message": f"Role '{current_user.role}' cannot view cash reconciliations"
                }
            )
        
        reconciliation_service = CashReconciliationService(db)
        
        result = reconciliation_service.list_reconciliations(
            booth_id=booth_id,
            event_id=event_id,
            limit=limit,
            offset=offset
        )
        
        logger.info(
            f"Cash reconciliations listed: count={len(result['reconciliations'])}, "
            f"total={result['total_count']}, requested_by={current_user.username}"
        )
        
        return CashReconciliationListResponse(
            reconciliations=[
                CashReconciliationResponse(
                    id=r.id,
                    booth_id=r.booth_id,
                    event_id=r.event_id,
                    expected_cash=r.expected_cash_yuan,
                    actual_cash=r.actual_cash_yuan,
                    diff_amount=r.diff_amount_yuan,
                    reason=r.reason,
                    reviewer_id=r.reviewer_id,
                    created_at=r.created_at
                )
                for r in result['reconciliations']
            ],
            total_count=result['total_count']
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in cash reconciliation query: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )
