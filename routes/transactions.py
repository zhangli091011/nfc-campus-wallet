"""
Transaction history endpoint for NFC Campus E-Wallet System.

Provides GET /transactions endpoint to retrieve transaction history with booth management support.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel
import logging

from core.database import get_db
from core.security import get_current_user, RoleChecker
from services.transaction_service import TransactionService
from models.user import User
from models.transaction import Transaction as TransactionModel
from models.booth import Booth
from core.exceptions import ResourceNotFoundError, ValidationError
from services.event_service import EventNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/transactions")
async def get_transactions(
    event_id: Optional[int] = Query(None, description="Filter by event ID"),
    booth_id: Optional[int] = Query(None, description="Filter by booth ID"),
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    type: Optional[str] = Query(None, description="Filter by transaction type(s), comma-separated"),
    start_date: Optional[str] = Query(None, description="Start date filter (ISO format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO format: YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of transactions to return"),
    offset: int = Query(0, ge=0, description="Number of transactions to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve transaction history with booth management support.
    
    权限验证：
    - super_admin 和 event_admin 可以查看所有交易
    - booth_cashier 只能查看自己摊位的交易
    - issuer 可以查看所有交易（用于审计）
    
    Query Parameters:
        - event_id: 活动ID过滤（可选）
        - booth_id: 摊位ID过滤（可选）
        - product_id: 商品ID过滤（可选）
        - start_date: 开始日期过滤（可选，ISO格式：YYYY-MM-DD）
        - end_date: 结束日期过滤（可选，ISO格式：YYYY-MM-DD）
        - limit: 返回记录数限制（默认100，最大1000）
        - offset: 偏移量（默认0）
    
    Returns:
        JSON response with transaction list and total count:
        {
            "transactions": [
                {
                    "id": 12345,
                    "type": "pay",
                    "amount": 25.00,
                    "balance_before": 100.50,
                    "balance_after": 75.50,
                    "participant_id": 1,
                    "card_uid": "A1B2C3D4",
                    "booth_id": 1,
                    "product_id": 5,
                    "operator_id": 3,
                    "merchant_id": null,
                    "related_txn_id": null,
                    "remark": "购买奶茶",
                    "created_at": "2024-01-15T10:30:00Z"
                }
            ],
            "total_count": 1
        }
    
    Error Responses:
        401: 未认证
        403: 权限不足（booth_cashier 查看其他摊位交易）
        404: 摊位或商品不存在
        500: 内部服务器错误
    
    Note:
        Transactions are returned in descending order by created_at (most recent first).
        
    Validates Requirements:
        - Requirement 11.4: Include booth_id, product_id, operator_id in response
        - Requirement 11.5: Support filtering transactions by booth_id
        - Requirement 11.6: Support filtering transactions by product_id
    """
    try:
        transaction_service = TransactionService(db)
        
        # 解析交易类型过滤
        transaction_types = None
        if type:
            transaction_types = [t.strip() for t in type.split(',') if t.strip()]
        
        # 权限验证和过滤逻辑
        # super_admin, event_admin, reviewer, school_inspector 可以查看所有交易
        if current_user.role in ('super_admin', 'event_admin', 'reviewer', 'school_inspector'):
            # 如果指定了 booth_id，使用 get_booth_transactions
            if booth_id is not None:
                result = transaction_service.get_booth_transactions(
                    booth_id=booth_id,
                    product_id=product_id,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                    offset=offset
                )
            # 如果指定了 event_id，使用 get_event_transaction_history
            elif event_id is not None:
                result = transaction_service.get_event_transaction_history(
                    event_id=event_id,
                    participant_id=None,
                    transaction_types=transaction_types,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                    offset=offset
                )
            else:
                # 查询所有交易（需要实现通用查询方法）
                # 暂时返回错误，要求指定 event_id 或 booth_id
                logger.warning(
                    f"Transaction query without event_id or booth_id by {current_user.username}"
                )
                return JSONResponse(
                    status_code=400,
                    content={
                        "error_code": "MISSING_FILTER",
                        "message": "Please specify either event_id or booth_id to filter transactions"
                    }
                )
        
        # booth_cashier 只能查看自己摊位的交易
        elif current_user.role == 'booth_cashier':
            # 验证 booth_id 参数
            if booth_id is not None and booth_id != current_user.booth_id:
                logger.warning(
                    f"Transaction query denied: booth_cashier {current_user.username} "
                    f"attempted to view transactions for booth {booth_id} (assigned booth: {current_user.booth_id})"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. You can only view transactions for booth {current_user.booth_id}. Requested booth: {booth_id}"
                )
            
            # 强制使用自己的 booth_id
            result = transaction_service.get_booth_transactions(
                booth_id=current_user.booth_id,
                product_id=product_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                offset=offset
            )
        
        # issuer 可以查看所有交易（用于审计）
        elif current_user.role == 'issuer':
            # 如果指定了 booth_id，使用 get_booth_transactions
            if booth_id is not None:
                result = transaction_service.get_booth_transactions(
                    booth_id=booth_id,
                    product_id=product_id,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                    offset=offset
                )
            # 如果指定了 event_id，使用 get_event_transaction_history
            elif event_id is not None:
                result = transaction_service.get_event_transaction_history(
                    event_id=event_id,
                    participant_id=None,
                    transaction_types=transaction_types,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                    offset=offset
                )
            else:
                # 要求指定 event_id 或 booth_id
                logger.warning(
                    f"Transaction query without event_id or booth_id by issuer {current_user.username}"
                )
                return JSONResponse(
                    status_code=400,
                    content={
                        "error_code": "MISSING_FILTER",
                        "message": "Please specify either event_id or booth_id to filter transactions"
                    }
                )
        
        # 其他角色不能查看交易
        else:
            logger.warning(
                f"Transaction query denied: role '{current_user.role}' cannot view transactions "
                f"(user={current_user.username})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Role '{current_user.role}' cannot view transaction history"
            )
        
        logger.info(
            f"Transaction history retrieved: count={len(result['transactions'])}, "
            f"total={result['total_count']}, event_id={event_id}, booth_id={booth_id}, "
            f"product_id={product_id}, requested_by={current_user.username}"
        )
        
        return result
    
    except HTTPException:
        # Re-raise HTTPException (403 errors from permission validation)
        raise
    
    except EventNotFoundError as e:
        logger.warning(f"Transaction query failed - event not found: {str(e)}")
        return JSONResponse(
            status_code=404,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except ResourceNotFoundError as e:
        logger.warning(f"Transaction query failed: {str(e)}")
        return JSONResponse(
            status_code=404,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except ValidationError as e:
        logger.warning(f"Transaction query validation failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except ValueError as e:
        logger.warning(f"Invalid date format in transaction query: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "INVALID_DATE_FORMAT",
                "message": "Invalid date format. Use ISO format: YYYY-MM-DD"
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in transaction query: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )


# ============ Transaction Transfer ============

class TransactionTransferRequest(BaseModel):
    """请求体：将交易转移到另一个摊位"""
    target_booth_id: int
    reason: str = ""


@router.post("/transactions/{transaction_id}/transfer")
async def transfer_transaction(
    transaction_id: int,
    request: TransactionTransferRequest,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["event_admin", "super_admin"])),
    db: Session = Depends(get_db)
):
    """
    将一笔交易转移到另一个摊位（用于修正账目错误）。
    
    仅修改交易的 booth_id 字段，不影响金额和余额。
    需要 event_admin 或 super_admin 权限。
    
    Path Parameters:
        - transaction_id: 要转移的交易ID
    
    Request Body:
        - target_booth_id: 目标摊位ID
        - reason: 转移原因（可选）
    
    Returns:
        转移后的交易信息
    """
    try:
        # 1. 查询交易
        transaction = db.query(TransactionModel).filter(
            TransactionModel.id == transaction_id
        ).first()
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error_code": "TRANSACTION_NOT_FOUND", "message": f"交易 {transaction_id} 不存在"}
            )
        
        # 2. 查询目标摊位
        target_booth = db.query(Booth).filter(
            Booth.id == request.target_booth_id
        ).first()
        
        if not target_booth:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error_code": "BOOTH_NOT_FOUND", "message": f"目标摊位 {request.target_booth_id} 不存在"}
            )
        
        # 3. 记录原始摊位信息
        original_booth_id = transaction.booth_id
        original_booth_name = ""
        if original_booth_id:
            original_booth = db.query(Booth).filter(Booth.id == original_booth_id).first()
            original_booth_name = original_booth.name if original_booth else f"ID:{original_booth_id}"
        
        # 4. 执行转移
        transaction.booth_id = request.target_booth_id
        
        # 5. 追加备注记录转移操作
        transfer_note = f"[流水转移] 从「{original_booth_name or '无摊位'}」转至「{target_booth.name}」"
        if request.reason:
            transfer_note += f"，原因：{request.reason}"
        transfer_note += f"（操作人：{current_user.username}）"
        
        if transaction.remark:
            transaction.remark = f"{transaction.remark} | {transfer_note}"
        else:
            transaction.remark = transfer_note
        
        db.commit()
        db.refresh(transaction)
        
        logger.info(
            f"交易转移成功: txn_id={transaction_id}, "
            f"from_booth={original_booth_id} to_booth={request.target_booth_id}, "
            f"operator={current_user.username}, reason={request.reason}"
        )
        
        return {
            "success": True,
            "transaction_id": transaction.id,
            "original_booth_id": original_booth_id,
            "original_booth_name": original_booth_name or None,
            "target_booth_id": target_booth.id,
            "target_booth_name": target_booth.name,
            "message": f"交易 #{transaction_id} 已从「{original_booth_name or '无摊位'}」转移至「{target_booth.name}」"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"交易转移失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "转移失败，请重试"}
        )
