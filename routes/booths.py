"""
Booths routes for Booth Management System.

提供摊位管理相关的 API 端点。
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from typing import Optional, List
from pydantic import BaseModel, Field
import logging

from core.database import get_db
from core.security import get_current_user, RoleChecker
from services.booth_service import (
    BoothService,
    BoothNotFoundError,
    InvalidEventError,
    BoothInactiveError
)
from services.transaction_service import TransactionService
from schemas.booth import BoothCreate, BoothResponse
from schemas.transaction import TransactionResponse
from models.user import User
from core.exceptions import BusinessException, ValidationError, ResourceNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter()


class BoothPaymentRequest(BaseModel):
    """摊位支付请求模型"""
    event_id: Optional[int] = Field(None, description="活动ID（可选，默认使用当前激活的活动）")
    card_uid: str = Field(..., description="NFC卡片UID")
    amount: float = Field(..., description="支付金额（元）", gt=0)
    product_id: Optional[int] = Field(None, description="商品ID（可选）")
    remark: Optional[str] = Field(None, max_length=255, description="备注（可选）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "card_uid": "A1B2C3D4",
                "amount": 25.00,
                "product_id": 5,
                "remark": "购买奶茶"
            }
        }


@router.post("/booths", response_model=BoothResponse, status_code=201)
async def create_booth(
    booth_data: BoothCreate,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    创建新摊位。
    
    如果未指定 event_id，则自动使用当前激活的活动。
    
    需要 event_admin 或 super_admin 角色。
    
    Request Body:
        - event_id: 活动ID（可选，默认为当前激活的活动）
        - name: 摊位名称（必填，1-100字符）
        - class_name: 班级名称（必填，1-100字符）
    
    Returns:
        BoothResponse: 创建的摊位信息
        
    Error Responses:
        400: 验证错误（如活动不存在或没有激活的活动）
        401: 未认证
        403: 权限不足
        500: 内部服务器错误
    
    Example:
        POST /booths
        {
            "name": "美食摊",
            "class_name": "高一(1)班"
        }
    
    Validates Requirements:
        - Requirement 8.1: POST /booths creates a new booth
        - Requirement 8.5: Validate event_id exists before creating booth
        - Requirement 8.6: Require authentication for booth management endpoints
    """
    try:
        # 如果未指定 event_id，使用当前激活的活动
        event_id = booth_data.event_id
        if event_id is None:
            from services.event_service import EventService
            event_service = EventService(db)
            active_event = event_service.get_active_event()
            
            if active_event is None:
                logger.warning("No active event found and no event_id specified for booth creation")
                return JSONResponse(
                    status_code=400,
                    content={
                        "error_code": "NO_ACTIVE_EVENT",
                        "message": "No active event found. Please specify event_id or activate an event."
                    }
                )
            
            event_id = active_event.id
            logger.info(f"Using active event for booth creation: id={event_id}, name='{active_event.name}'")
        
        booth_service = BoothService(db)
        
        booth = booth_service.create_booth(
            event_id=event_id,
            name=booth_data.name,
            class_name=booth_data.class_name
        )
        
        logger.info(
            f"Booth created successfully: id={booth.id}, name='{booth.name}', "
            f"event_id={booth.event_id}, created_by={current_user.username}"
        )
        
        return BoothResponse.model_validate(booth)
    
    except InvalidEventError as e:
        logger.warning(f"Booth creation failed - invalid event: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except ValueError as e:
        logger.warning(f"Booth creation validation failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": str(e)
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in booth creation: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )


@router.get("/booths", response_model=List[BoothResponse])
async def list_booths(
    event_id: Optional[int] = Query(None, description="Filter by event ID (defaults to active event if not specified)"),
    status: Optional[str] = Query(None, description="Filter by booth status (active/inactive/closed)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of booths to return"),
    offset: int = Query(0, ge=0, description="Number of booths to skip"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    获取摊位列表，支持活动和状态过滤。
    
    如果未指定 event_id，则自动使用当前激活的活动。
    
    需要 event_admin 或 super_admin 角色。
    
    Query Parameters:
        - event_id: 活动ID过滤（可选，默认为当前激活的活动）
        - status: 摊位状态过滤（可选）
        - limit: 返回记录数限制（默认100，最大1000）
        - offset: 偏移量（默认0）
    
    Returns:
        List[BoothResponse]: 摊位列表
        
    Error Responses:
        400: 没有激活的活动且未指定 event_id
        401: 未认证
        403: 权限不足
        500: 内部服务器错误
    
    Example:
        GET /booths?status=active&limit=10&offset=0
    
    Validates Requirements:
        - Requirement 8.2: GET /booths returns list of booths with optional filtering
        - Requirement 8.6: Require authentication for booth management endpoints
    """
    try:
        # 如果未指定 event_id，使用当前激活的活动
        if event_id is None:
            from services.event_service import EventService
            event_service = EventService(db)
            active_event = event_service.get_active_event()
            
            if active_event is None:
                logger.warning("No active event found and no event_id specified")
                return JSONResponse(
                    status_code=400,
                    content={
                        "error_code": "NO_ACTIVE_EVENT",
                        "message": "No active event found. Please specify event_id or activate an event."
                    }
                )
            
            event_id = active_event.id
            logger.info(f"Using active event: id={event_id}, name='{active_event.name}'")
        
        booth_service = BoothService(db)
        
        booths = booth_service.list_booths(
            event_id=event_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        logger.info(
            f"Booths listed: count={len(booths)}, event_id={event_id}, "
            f"status={status}, requested_by={current_user.username}"
        )
        
        return [BoothResponse.model_validate(booth) for booth in booths]
    
    except Exception as e:
        logger.error(
            f"Unexpected error in booth listing: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )


@router.get("/booths/{booth_id}", response_model=BoothResponse)
async def get_booth(
    booth_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取摊位详情。
    
    权限验证：
    - super_admin 和 event_admin 可以查看所有摊位
    - booth_cashier 只能查看自己的摊位
    
    Path Parameters:
        - booth_id: 摊位ID
    
    Returns:
        BoothResponse: 摊位详细信息
        
    Error Responses:
        401: 未认证
        403: 权限不足（booth_cashier 访问其他摊位）
        404: 摊位不存在
        500: 内部服务器错误
    
    Example:
        GET /booths/1
    
    Validates Requirements:
        - Requirement 8.3: GET /booths/{id} returns booth details
        - Requirement 8.4: Booth not found returns 404 error
        - Requirement 8.6: Require authentication for booth management endpoints
        - Requirement 5.3: booth_cashier accessing another booth gets 403 error
    """
    try:
        booth_service = BoothService(db)
        
        # Get booth first to check if it exists
        booth = booth_service.get_booth(booth_id)
        
        # Permission validation
        # super_admin and event_admin can view all booths
        if current_user.role in ('super_admin', 'event_admin'):
            logger.info(
                f"Booth retrieved: id={booth_id}, name='{booth.name}', "
                f"requested_by={current_user.username} (role={current_user.role})"
            )
            return BoothResponse.model_validate(booth)
        
        # booth_cashier can only view their own booth
        elif current_user.role == 'booth_cashier':
            if current_user.booth_id != booth_id:
                logger.warning(
                    f"Booth access denied: booth_cashier {current_user.username} "
                    f"attempted to access booth {booth_id} (assigned booth: {current_user.booth_id})"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. You can only access booth {current_user.booth_id}. Requested booth: {booth_id}"
                )
            
            logger.info(
                f"Booth retrieved: id={booth_id}, name='{booth.name}', "
                f"requested_by={current_user.username} (booth_cashier)"
            )
            return BoothResponse.model_validate(booth)
        
        # Other roles (issuer, reviewer) cannot access booth-specific data
        else:
            logger.warning(
                f"Booth access denied: role '{current_user.role}' cannot access booth-specific data "
                f"(user={current_user.username}, booth_id={booth_id})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Role '{current_user.role}' cannot access booth-specific data"
            )
    
    except BoothNotFoundError as e:
        logger.warning(f"Booth not found: {booth_id}")
        return JSONResponse(
            status_code=404,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except HTTPException:
        # Re-raise HTTPException (403 errors from permission validation)
        raise
    
    except Exception as e:
        logger.error(
            f"Unexpected error in booth retrieval: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )



@router.post("/booths/{booth_id}/pay", response_model=TransactionResponse)
async def process_booth_payment(
    booth_id: int,
    payment_request: BoothPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    处理摊位支付交易（需要 JWT 认证）。
    
    权限验证：
    - super_admin 和 event_admin 可以操作所有摊位
    - booth_cashier 只能操作自己的摊位
    - issuer 和 reviewer 不能处理支付
    
    Path Parameters:
        - booth_id: 摊位ID
    
    Request Body:
        - event_id: 活动ID（必填）
        - card_uid: NFC卡片UID（必填）
        - amount: 支付金额（必填，元）
        - product_id: 商品ID（可选）
        - remark: 备注（可选）
    
    Returns:
        TransactionResponse: 交易结果
        
    Error Responses:
        400: 验证错误（摊位不属于活动、商品不属于摊位、余额不足等）
        401: 未认证
        403: 权限不足（booth_cashier 操作其他摊位、issuer 尝试支付等）
        404: 摊位、商品或参与者不存在
        500: 内部服务器错误
    
    Example:
        POST /booths/1/pay
        Headers: Authorization: Bearer <jwt_token>
        {
            "event_id": 1,
            "card_uid": "A1B2C3D4",
            "amount": 25.00,
            "product_id": 5,
            "remark": "购买奶茶"
        }
        
        Response:
        {
            "success": true,
            "new_balance": 75.50,
            "transaction_id": 12345,
            "balance_before": 100.50,
            "event_id": 1,
            "participant_id": 1,
            "booth_id": 1,
            "product_id": 5,
            "operator_id": 3
        }
    
    Validates Requirements:
        - Requirement 10.1: Require event_id, booth_id, and operator_id
        - Requirement 10.2: Accept optional product_id
        - Requirement 10.3: Verify product belongs to booth
        - Requirement 10.4: Verify booth belongs to event
        - Requirement 10.5: Verify operator has permission
        - Requirement 10.6: Record booth_id, product_id, operator_id
        - Requirement 5.2: booth_cashier can only create payment transactions for their booth
        - Requirement 5.3: booth_cashier attempting to access another booth gets 403 error
        - Requirement 6.2: issuer attempting payment gets 403 error
    """
    try:
        # 权限验证
        # super_admin 和 event_admin 可以操作所有摊位
        if current_user.role in ('super_admin', 'event_admin'):
            pass  # 允许
        
        # booth_cashier 只能操作自己的摊位
        elif current_user.role == 'booth_cashier':
            if current_user.booth_id != booth_id:
                logger.warning(
                    f"Booth payment denied: booth_cashier {current_user.username} "
                    f"attempted to process payment for booth {booth_id} (assigned booth: {current_user.booth_id})"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. You can only process payments for booth {current_user.booth_id}. Requested booth: {booth_id}"
                )
        
        # issuer 不能处理支付
        elif current_user.role == 'issuer':
            logger.warning(
                f"Booth payment denied: issuer {current_user.username} attempted to process payment"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Issuers can only process recharge transactions, not payments"
            )
        
        # 其他角色不能处理支付
        else:
            logger.warning(
                f"Booth payment denied: role '{current_user.role}' cannot process payments "
                f"(user={current_user.username})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Role '{current_user.role}' cannot process payment transactions"
            )
        
        # 如果未指定 event_id，使用当前激活的活动
        event_id = payment_request.event_id
        if event_id is None:
            from services.event_service import EventService
            event_service = EventService(db)
            active_event = event_service.get_active_event()
            
            if active_event is None:
                logger.warning("No active event found and no event_id specified for booth payment")
                return JSONResponse(
                    status_code=400,
                    content={
                        "error_code": "NO_ACTIVE_EVENT",
                        "message": "No active event found. Please specify event_id or activate an event."
                    }
                )
            
            event_id = active_event.id
            logger.info(f"Using active event for booth payment: id={event_id}, name='{active_event.name}'")
        
        # 处理摊位支付
        transaction_service = TransactionService(db)
        
        result = transaction_service.process_booth_payment(
            event_id=event_id,
            card_uid=payment_request.card_uid,
            booth_id=booth_id,
            amount_yuan=payment_request.amount,
            operator_id=current_user.id,
            product_id=payment_request.product_id,
            remark=payment_request.remark
        )
        
        logger.info(
            f"Booth payment successful: booth_id={booth_id}, event_id={event_id}, "
            f"card_uid={payment_request.card_uid}, amount={payment_request.amount} yuan, "
            f"product_id={payment_request.product_id}, operator={current_user.username}, "
            f"txn_id={result.transaction_id}"
        )
        
        # 获取交易详情以返回完整信息
        from models.transaction import Transaction
        transaction = db.query(Transaction).filter(Transaction.id == result.transaction_id).first()
        
        return TransactionResponse(
            success=result.success,
            new_balance=result.new_balance_yuan,
            transaction_id=result.transaction_id,
            balance_before=result.balance_before_yuan,
            event_id=transaction.event_id if transaction else event_id,
            participant_id=transaction.participant_id if transaction else None,
            booth_id=booth_id,
            product_id=payment_request.product_id,
            operator_id=current_user.id
        )
    
    except HTTPException:
        # Re-raise HTTPException (403 errors from permission validation)
        raise
    
    except ValidationError as e:
        logger.warning(f"Booth payment validation failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except ResourceNotFoundError as e:
        logger.warning(f"Booth payment failed - resource not found: {str(e)}")
        return JSONResponse(
            status_code=404,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except Exception as e:
        # Import event-related exceptions dynamically to handle them
        from services.event_service import EventNotFoundError, EventInactiveError
        from services.participant_service import ParticipantNotFoundError
        from core.exceptions import InsufficientFundsError
        
        # Check if it's a known exception
        if isinstance(e, (EventNotFoundError, EventInactiveError)):
            logger.warning(f"Booth payment failed: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": e.error_code,
                    "message": e.message
                }
            )
        
        if isinstance(e, ParticipantNotFoundError):
            logger.warning(f"Booth payment failed: {str(e)}")
            return JSONResponse(
                status_code=404,
                content={
                    "error_code": e.error_code,
                    "message": e.message
                }
            )
        
        if isinstance(e, InsufficientFundsError):
            logger.warning(f"Booth payment failed: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": e.error_code,
                    "message": e.message
                }
            )
        
        # Unknown error
        logger.error(
            f"Unexpected error in booth payment: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )



@router.get("/booths/{booth_id}/transactions")
async def get_booth_transactions(
    booth_id: int,
    start_date: Optional[str] = Query(None, description="Start date filter (ISO format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO format: YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of transactions to return"),
    offset: int = Query(0, ge=0, description="Number of transactions to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取摊位交易记录。
    
    权限验证：
    - super_admin 和 event_admin 可以查看所有摊位交易
    - booth_cashier 只能查看自己摊位的交易
    
    Path Parameters:
        - booth_id: 摊位ID
    
    Query Parameters:
        - start_date: 开始日期过滤（可选，ISO格式：YYYY-MM-DD）
        - end_date: 结束日期过滤（可选，ISO格式：YYYY-MM-DD）
        - limit: 返回记录数限制（默认100，最大1000）
        - offset: 偏移量（默认0）
    
    Returns:
        JSON response with transaction list and total count
        
    Error Responses:
        401: 未认证
        403: 权限不足（booth_cashier 查看其他摊位交易）
        404: 摊位不存在
        500: 内部服务器错误
    
    Example:
        GET /booths/1/transactions?start_date=2024-01-01&limit=10
        Headers: Authorization: Bearer <jwt_token>
        
        Response:
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
                    "created_at": "2024-01-15T10:30:00Z"
                }
            ],
            "total_count": 1
        }
    
    Validates Requirements:
        - Requirement 11.4: Include booth_id, product_id, operator_id in response
        - Requirement 11.5: Support filtering transactions by booth_id
        - Requirement 7.3: event_admin can view activity-wide statistics
    """
    try:
        # 权限验证
        # super_admin 和 event_admin 可以查看所有摊位交易
        if current_user.role in ('super_admin', 'event_admin'):
            pass  # 允许
        
        # booth_cashier 只能查看自己摊位的交易
        elif current_user.role == 'booth_cashier':
            if current_user.booth_id != booth_id:
                logger.warning(
                    f"Booth transactions access denied: booth_cashier {current_user.username} "
                    f"attempted to view transactions for booth {booth_id} (assigned booth: {current_user.booth_id})"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. You can only view transactions for booth {current_user.booth_id}. Requested booth: {booth_id}"
                )
        
        # 其他角色不能查看摊位交易
        else:
            logger.warning(
                f"Booth transactions access denied: role '{current_user.role}' cannot view booth transactions "
                f"(user={current_user.username})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Role '{current_user.role}' cannot view booth-specific transactions"
            )
        
        # 获取摊位交易记录
        transaction_service = TransactionService(db)
        
        result = transaction_service.get_booth_transactions(
            booth_id=booth_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        logger.info(
            f"Booth transactions retrieved: booth_id={booth_id}, count={len(result['transactions'])}, "
            f"total={result['total_count']}, requested_by={current_user.username}"
        )
        
        return result
    
    except HTTPException:
        # Re-raise HTTPException (403 errors from permission validation)
        raise
    
    except ResourceNotFoundError as e:
        logger.warning(f"Booth transactions query failed: {str(e)}")
        return JSONResponse(
            status_code=404,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except ValueError as e:
        logger.warning(f"Invalid date format in booth transactions query: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "INVALID_DATE_FORMAT",
                "message": "Invalid date format. Use ISO format: YYYY-MM-DD"
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in booth transactions query: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )
