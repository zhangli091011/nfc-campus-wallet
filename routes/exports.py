"""
Export routes for NFC Campus Event System.

提供数据导出相关的 API 端点。
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import logging
import io

from core.database import get_db
from core.security import get_current_user
from services.export_service import ExportService
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/export/class-settlement")
async def export_class_settlement(
    event_id: int = Query(..., description="活动ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    导出班级结算单。
    
    权限要求：super_admin 或 event_admin
    
    Query Parameters:
        - event_id: 活动ID（必填）
    
    Returns:
        Excel 文件流
    """
    try:
        # 权限验证
        if current_user.role not in ('super_admin', 'event_admin'):
            return {"error": "Permission denied"}
        
        export_service = ExportService(db)
        excel_data = export_service.export_class_settlement(event_id)
        
        logger.info(
            f"Class settlement exported: event_id={event_id}, "
            f"exported_by={current_user.username}"
        )
        
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=class_settlement_event_{event_id}.xlsx"
            }
        )
    
    except Exception as e:
        logger.error(f"Export failed: {str(e)}", exc_info=True)
        return {"error": str(e)}


@router.get("/export/transactions")
async def export_transactions(
    event_id: Optional[int] = Query(None, description="活动ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    导出全量流水。
    
    权限要求：super_admin、event_admin 或 issuer
    
    Query Parameters:
        - event_id: 活动ID（可选）
    
    Returns:
        Excel 文件流
    """
    try:
        # 权限验证
        if current_user.role not in ('super_admin', 'event_admin', 'issuer'):
            return {"error": "Permission denied"}
        
        export_service = ExportService(db)
        excel_data = export_service.export_to_excel("transactions", event_id)
        
        logger.info(
            f"Transactions exported: event_id={event_id}, "
            f"exported_by={current_user.username}"
        )
        
        filename = f"transactions_event_{event_id}.xlsx" if event_id else "transactions_all.xlsx"
        
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except Exception as e:
        logger.error(f"Export failed: {str(e)}", exc_info=True)
        return {"error": str(e)}


@router.get("/export/refund-adjustments")
async def export_refund_adjustments(
    event_id: Optional[int] = Query(None, description="活动ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    导出退款/更正清单。
    
    权限要求：super_admin 或 event_admin
    
    Query Parameters:
        - event_id: 活动ID（可选）
    
    Returns:
        Excel 文件流
    """
    try:
        # 权限验证
        if current_user.role not in ('super_admin', 'event_admin'):
            return {"error": "Permission denied"}
        
        export_service = ExportService(db)
        excel_data = export_service.export_refund_adjustments(event_id)
        
        logger.info(
            f"Refund/adjustments exported: event_id={event_id}, "
            f"exported_by={current_user.username}"
        )
        
        filename = f"refund_adjustments_event_{event_id}.xlsx" if event_id else "refund_adjustments_all.xlsx"
        
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except Exception as e:
        logger.error(f"Export failed: {str(e)}", exc_info=True)
        return {"error": str(e)}


@router.get("/export/leaderboard")
async def export_leaderboard(
    event_id: int = Query(..., description="活动ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    导出排名表。
    
    权限要求：super_admin 或 event_admin
    
    Query Parameters:
        - event_id: 活动ID（必填）
    
    Returns:
        Excel 文件流
    """
    try:
        # 权限验证
        if current_user.role not in ('super_admin', 'event_admin'):
            return {"error": "Permission denied"}
        
        export_service = ExportService(db)
        excel_data = export_service.export_leaderboard(event_id)
        
        logger.info(
            f"Leaderboard exported: event_id={event_id}, "
            f"exported_by={current_user.username}"
        )
        
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=leaderboard_event_{event_id}.xlsx"
            }
        )
    
    except Exception as e:
        logger.error(f"Export failed: {str(e)}", exc_info=True)
        return {"error": str(e)}


@router.get("/export/booth-transactions")
async def export_booth_transactions(
    booth_id: int = Query(..., description="摊位ID"),
    start_date: Optional[str] = Query(None, description="开始日期（ISO格式：YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（ISO格式：YYYY-MM-DD）"),
    has_product: Optional[bool] = Query(None, description="是否关联商品（true=商品收款，false=非商品收款）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    按商铺导出账目明细。
    
    权限要求：super_admin、event_admin 或该商铺的 booth_cashier
    
    Query Parameters:
        - booth_id: 摊位ID（必填）
        - start_date: 开始日期（可选，ISO格式：YYYY-MM-DD）
        - end_date: 结束日期（可选，ISO格式：YYYY-MM-DD）
        - has_product: 是否关联商品（可选，true=仅商品收款，false=仅非商品收款）
    
    Returns:
        Excel 文件流
    """
    try:
        # 权限验证
        if current_user.role in ('super_admin', 'event_admin'):
            pass  # 允许
        elif current_user.role == 'booth_cashier':
            if current_user.booth_id != booth_id:
                return {"error": "Permission denied. You can only export your own booth's transactions."}
        else:
            return {"error": "Permission denied"}
        
        export_service = ExportService(db)
        excel_data = export_service.export_booth_transactions(
            booth_id=booth_id,
            start_date=start_date,
            end_date=end_date,
            has_product=has_product
        )
        
        logger.info(
            f"Booth transactions exported: booth_id={booth_id}, "
            f"start_date={start_date}, end_date={end_date}, has_product={has_product}, "
            f"exported_by={current_user.username}"
        )
        
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=booth_transactions_{booth_id}.xlsx"
            }
        )
    
    except ValueError as e:
        logger.warning(f"Booth transactions export failed: {str(e)}")
        return {"error": str(e)}
    
    except Exception as e:
        logger.error(f"Booth transactions export failed: {str(e)}", exc_info=True)
        return {"error": str(e)}
