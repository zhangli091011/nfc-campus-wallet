"""
Booths routes for Booth Management System.

提供摊位管理相关的 API 端点。
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from typing import Optional, List
from pydantic import BaseModel, Field
import logging
import secrets
import string

from core.database import get_db
from core.security import get_current_user, RoleChecker, hash_password
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
    _: None = Depends(RoleChecker(["super_admin", "event_admin", "bank_clerk"])),
    db: Session = Depends(get_db)
):
    """
    获取摊位列表，支持活动和状态过滤。
    
    如果未指定 event_id，则自动使用当前激活的活动。
    如果没有激活的活动，则返回所有摊位。
    
    需要 event_admin、super_admin 或 bank_clerk 角色。
    
    Query Parameters:
        - event_id: 活动ID过滤（可选，默认为当前激活的活动）
        - status: 摊位状态过滤（可选）
        - limit: 返回记录数限制（默认100，最大1000）
        - offset: 偏移量（默认0）
    
    Returns:
        List[BoothResponse]: 摊位列表
        
    Error Responses:
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
        # 如果未指定 event_id，尝试使用当前激活的活动
        if event_id is None:
            from services.event_service import EventService
            event_service = EventService(db)
            active_event = event_service.get_active_event()
            
            if active_event is not None:
                event_id = active_event.id
                logger.info(f"Using active event: id={event_id}, name='{active_event.name}'")
            else:
                logger.info("No active event found, returning all booths")
        
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
    - bank_clerk（投资办理员）可以查看所有摊位（用于投资办理）
    
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
        # super_admin、event_admin 以及 bank_clerk 可以查看所有摊位
        if current_user.role in ('super_admin', 'event_admin', 'bank_clerk'):
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


@router.delete("/booths/{booth_id}", status_code=204)
async def delete_booth(
    booth_id: int,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    删除摊位。

    仅 super_admin 和 event_admin 可执行此操作。
    会级联删除关联的商品记录。关联的交易记录和收银员账号不会被删除。

    Path Parameters:
        - booth_id: 摊位ID
    """
    from models.booth import Booth

    booth = db.query(Booth).filter(Booth.id == booth_id).first()
    if booth is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"摊位 {booth_id} 不存在"
        )

    # 解除收银员关联
    for cashier in booth.cashiers:
        cashier.booth_id = None

    db.delete(booth)
    db.commit()

    logger.info(
        f"Booth deleted: id={booth_id}, name={booth.name}, "
        f"operator={current_user.username}"
    )
    return None


class BoothStockEnabledRequest(BaseModel):
    """请求体：设置摊位是否允许参与股票市场"""
    stock_enabled: bool = Field(..., description="是否允许参与股票市场")


@router.patch("/booths/{booth_id}/stock-enabled")
async def update_booth_stock_enabled(
    booth_id: int,
    request: BoothStockEnabledRequest,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    设置摊位是否允许参与股票市场。
    
    仅 super_admin 和 event_admin 可执行此操作。
    
    Path Parameters:
        - booth_id: 摊位ID
    
    Request Body:
        - stock_enabled: 是否允许参与股票市场
    
    Returns:
        更新后的摊位信息
    """
    from models.booth import Booth

    booth = db.query(Booth).filter(Booth.id == booth_id).first()
    if booth is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"摊位 {booth_id} 不存在"
        )

    booth.stock_enabled = 1 if request.stock_enabled else 0
    db.commit()
    db.refresh(booth)

    logger.info(
        f"Booth stock_enabled updated: id={booth_id}, name={booth.name}, "
        f"stock_enabled={request.stock_enabled}, operator={current_user.username}"
    )

    return {
        "id": booth.id,
        "name": booth.name,
        "class_name": booth.class_name,
        "stock_enabled": bool(booth.stock_enabled),
        "message": f"摊位「{booth.name}」{'已开启' if request.stock_enabled else '已关闭'}股票参与权限"
    }


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
        
        # 计算随机立减（如果表不存在则跳过）
        from services.random_discount_service import RandomDiscountService, DiscountResult
        discount_result = DiscountResult(applied=False, original_amount=payment_request.amount, actual_amount=payment_request.amount)
        participant = None
        
        try:
            from services.participant_service import ParticipantService
            discount_service = RandomDiscountService(db)
            participant_service_inst = ParticipantService(db)
            participant = participant_service_inst.get_participant_by_card(payment_request.card_uid)
            
            discount_result = discount_service.calculate_discount(
                event_id=event_id,
                participant_id=participant.id,
                payment_amount=payment_request.amount
            )
        except Exception as e:
            logger.warning(f"Random discount calculation skipped: {e}")
            discount_result = DiscountResult(applied=False, original_amount=payment_request.amount, actual_amount=payment_request.amount)
        
        # 使用立减后的实际金额进行支付
        actual_payment_amount = discount_result.actual_amount if discount_result.applied else payment_request.amount
        
        result = transaction_service.process_booth_payment(
            event_id=event_id,
            card_uid=payment_request.card_uid,
            booth_id=booth_id,
            amount_yuan=actual_payment_amount,
            operator_id=current_user.id,
            product_id=payment_request.product_id,
            remark=payment_request.remark
        )
        
        # 如果立减生效，记录立减信息
        if discount_result.applied and participant:
            try:
                discount_service.apply_discount(
                    event_id=event_id,
                    participant_id=participant.id,
                    transaction_id=result.transaction_id,
                    discount_result=discount_result,
                    booth_id=booth_id
                )
            except Exception as e:
                logger.warning(f"Failed to record discount: {e}")
        
        logger.info(
            f"Booth payment successful: booth_id={booth_id}, event_id={event_id}, "
            f"card_uid={payment_request.card_uid}, amount={payment_request.amount} yuan, "
            f"product_id={payment_request.product_id}, operator={current_user.username}, "
            f"txn_id={result.transaction_id}"
            f"{f', discount={discount_result.discount_amount}' if discount_result.applied else ''}"
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
            operator_id=current_user.id,
            discount_applied=discount_result.applied,
            discount_amount=discount_result.discount_amount if discount_result.applied else None,
            original_amount=discount_result.original_amount if discount_result.applied else None,
            actual_amount=discount_result.actual_amount if discount_result.applied else None
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


class CashPaymentRequest(BaseModel):
    """现金收款请求"""
    amount: float = Field(..., gt=0, description="现金收款金额（元）")
    remark: Optional[str] = Field(None, max_length=255, description="备注")
    event_id: Optional[int] = Field(None, description="活动ID（可选，默认使用当前活动）")


@router.post("/booths/{booth_id}/cash-payment")
async def process_cash_payment(
    booth_id: int,
    request: CashPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    记录现金收款（不扣卡内余额）。

    用于摊位收取现金时记录入账，方便后台对账。
    交易类型为 cash_payment，不关联任何参与者卡片。

    权限：super_admin、event_admin、booth_cashier（仅自己摊位）
    """
    from models.transaction import Transaction
    from datetime import datetime, timezone

    # 权限验证
    if current_user.role == 'booth_cashier':
        if current_user.booth_id != booth_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"只能为自己的摊位记录现金收款"
            )
    elif current_user.role not in ('super_admin', 'event_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )

    # 确定活动ID
    event_id = request.event_id
    if event_id is None:
        from services.event_service import EventService
        event_service = EventService(db)
        active_event = event_service.get_active_event()
        if active_event is None:
            return JSONResponse(
                status_code=400,
                content={"error_code": "NO_ACTIVE_EVENT", "message": "没有活跃的活动"}
            )
        event_id = active_event.id

    # 验证摊位存在
    from models.booth import Booth
    booth = db.query(Booth).filter(Booth.id == booth_id).first()
    if not booth:
        raise HTTPException(status_code=404, detail="摊位不存在")

    try:
        # 创建现金收款流水记录（使用原生SQL，因为 participant_id 在数据库中可能有NOT NULL约束）
        from datetime import datetime, timezone as tz
        now = datetime.now(tz.utc)
        
        result = db.execute(
            text("""INSERT INTO transactions 
                    (uid, card_uid, event_id, participant_id, account_id, type, amount, 
                     balance_before, balance_after, merchant_id, remark, operator_id, booth_id, created_at)
                    VALUES (NULL, NULL, :event_id, NULL, NULL, 'cash_payment', :amount,
                     0, 0, NULL, :remark, :operator_id, :booth_id, :created_at)"""),
            {
                "event_id": event_id,
                "amount": request.amount,
                "remark": request.remark or "现金收款",
                "operator_id": str(current_user.id),
                "booth_id": booth_id,
                "created_at": now,
            }
        )
        db.commit()
        
        txn_id = result.lastrowid

        logger.info(
            f"Cash payment recorded: booth_id={booth_id}, amount=¥{request.amount:.2f}, "
            f"event_id={event_id}, operator={current_user.username}, txn_id={txn_id}"
        )

        return {
            "success": True,
            "transaction_id": txn_id,
            "amount": request.amount,
            "booth_id": booth_id,
            "booth_name": booth.name,
            "event_id": event_id,
            "operator": current_user.username,
            "message": f"现金收款 ¥{request.amount:.2f} 已记录",
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Cash payment failed: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": str(e)}
        )


@router.get("/booths/{booth_id}/transactions")
async def get_booth_transactions(
    booth_id: int,
    has_product: Optional[bool] = Query(None, description="Filter by product association (true=with product, false=without product)"),
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
            has_product=has_product,
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


# ============================================================================
# 摊位账号凭据管理 (Booth Credentials Management)
# ============================================================================


def _generate_password(length: int = 8) -> str:
    """生成随机密码（数字+字母）"""
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


class BoothCredentialResponse(BaseModel):
    """摊位登录凭据响应"""
    booth_id: int
    booth_name: str
    username: str
    password: Optional[str] = Field(None, description="仅在生成时返回明文密码")
    user_id: Optional[int] = None
    user_status: Optional[str] = None


class BoothCashierInfo(BaseModel):
    """摊位收银员信息"""
    id: int
    username: str
    status: str
    created_at: str


class AssignCashierRequest(BaseModel):
    """指定收银员请求"""
    user_id: int = Field(..., description="要分配到此摊位的用户ID")


class GenerateCredentialRequest(BaseModel):
    """生成摊位凭据请求"""
    username: Optional[str] = Field(None, description="自定义用户名（可选，默认自动生成）")
    password: Optional[str] = Field(None, description="自定义密码（可选，默认自动生成）")


@router.get("/booths/{booth_id}/credentials", response_model=BoothCredentialResponse)
async def get_booth_credentials(
    booth_id: int,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    获取摊位的登录账号信息。
    
    显示该摊位关联的收银员账号用户名（密码不可查看，只能重新生成）。
    
    需要 super_admin 或 event_admin 角色。
    """
    try:
        booth_service = BoothService(db)
        booth = booth_service.get_booth(booth_id)
        
        # 查找该摊位关联的收银员账号
        cashier = db.query(User).filter(
            User.booth_id == booth_id,
            User.role == 'booth_cashier'
        ).first()
        
        if cashier:
            return BoothCredentialResponse(
                booth_id=booth.id,
                booth_name=booth.name,
                username=cashier.username,
                password=None,  # 不返回密码
                user_id=cashier.id,
                user_status=cashier.status
            )
        else:
            return BoothCredentialResponse(
                booth_id=booth.id,
                booth_name=booth.name,
                username="",
                password=None,
                user_id=None,
                user_status=None
            )
    
    except BoothNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error_code": e.error_code, "message": e.message}
        )
    except Exception as e:
        logger.error(f"Error getting booth credentials: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "An internal error occurred."}
        )


@router.post("/booths/{booth_id}/credentials", response_model=BoothCredentialResponse)
async def generate_booth_credentials(
    booth_id: int,
    request_data: Optional[GenerateCredentialRequest] = None,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    为摊位生成登录凭据（账号+密码）。
    
    如果摊位已有收银员账号，则重置密码。
    如果没有，则创建新的收银员账号。
    
    需要 super_admin 或 event_admin 角色。
    
    Returns:
        BoothCredentialResponse: 包含明文密码（仅此一次可见）
    """
    try:
        booth_service = BoothService(db)
        booth = booth_service.get_booth(booth_id)
        
        # 确定用户名和密码
        custom_username = request_data.username if request_data else None
        custom_password = request_data.password if request_data else None
        
        password = custom_password or _generate_password(8)
        
        # 查找该摊位已有的收银员账号
        existing_cashier = db.query(User).filter(
            User.booth_id == booth_id,
            User.role == 'booth_cashier'
        ).first()
        
        if existing_cashier:
            # 重置密码
            existing_cashier.password_hash = hash_password(password)
            db.commit()
            db.refresh(existing_cashier)
            
            logger.info(
                f"Booth credentials reset: booth_id={booth_id}, username='{existing_cashier.username}', "
                f"reset_by={current_user.username}"
            )
            
            return BoothCredentialResponse(
                booth_id=booth.id,
                booth_name=booth.name,
                username=existing_cashier.username,
                password=password,
                user_id=existing_cashier.id,
                user_status=existing_cashier.status
            )
        else:
            # 创建新的收银员账号
            username = custom_username or f"booth_{booth_id}"
            
            # 检查用户名是否已存在
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                # 如果默认用户名已存在，加上随机后缀
                username = f"booth_{booth_id}_{secrets.token_hex(2)}"
            
            new_user = User(
                username=username,
                password_hash=hash_password(password),
                role='booth_cashier',
                booth_id=booth_id,
                status='active'
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            logger.info(
                f"Booth credentials created: booth_id={booth_id}, username='{username}', "
                f"user_id={new_user.id}, created_by={current_user.username}"
            )
            
            return BoothCredentialResponse(
                booth_id=booth.id,
                booth_name=booth.name,
                username=username,
                password=password,
                user_id=new_user.id,
                user_status=new_user.status
            )
    
    except BoothNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error_code": e.error_code, "message": e.message}
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating booth credentials: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "An internal error occurred."}
        )


@router.get("/booths/{booth_id}/cashiers", response_model=List[BoothCashierInfo])
async def get_booth_cashiers(
    booth_id: int,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    获取摊位的所有收银员列表。
    
    需要 super_admin 或 event_admin 角色。
    """
    try:
        booth_service = BoothService(db)
        booth_service.get_booth(booth_id)  # 验证摊位存在
        
        cashiers = db.query(User).filter(
            User.booth_id == booth_id,
            User.role == 'booth_cashier'
        ).all()
        
        return [
            BoothCashierInfo(
                id=c.id,
                username=c.username,
                status=c.status,
                created_at=c.created_at.isoformat() if c.created_at else ""
            )
            for c in cashiers
        ]
    
    except BoothNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error_code": e.error_code, "message": e.message}
        )
    except Exception as e:
        logger.error(f"Error getting booth cashiers: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "An internal error occurred."}
        )


@router.post("/booths/{booth_id}/cashiers")
async def assign_cashier_to_booth(
    booth_id: int,
    request_data: AssignCashierRequest,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    将用户指定为摊位收银员。
    
    将指定用户的角色设为 booth_cashier 并关联到此摊位。
    
    需要 super_admin 或 event_admin 角色。
    """
    try:
        booth_service = BoothService(db)
        booth_service.get_booth(booth_id)  # 验证摊位存在
        
        # 获取目标用户
        target_user = db.query(User).filter(User.id == request_data.user_id).first()
        if not target_user:
            return JSONResponse(
                status_code=404,
                content={"error_code": "USER_NOT_FOUND", "message": f"User with id {request_data.user_id} not found"}
            )
        
        # 更新用户角色和摊位
        target_user.role = 'booth_cashier'
        target_user.booth_id = booth_id
        db.commit()
        db.refresh(target_user)
        
        logger.info(
            f"Cashier assigned to booth: user_id={target_user.id}, username='{target_user.username}', "
            f"booth_id={booth_id}, assigned_by={current_user.username}"
        )
        
        return {
            "success": True,
            "message": f"User '{target_user.username}' assigned to booth {booth_id} as cashier",
            "user_id": target_user.id,
            "username": target_user.username,
            "booth_id": booth_id
        }
    
    except BoothNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error_code": e.error_code, "message": e.message}
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error assigning cashier to booth: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "An internal error occurred."}
        )


# ============================================================================
# 后扣款功能 (Post-Payment Deduction)
# ============================================================================


class PostPaymentDeductionRequest(BaseModel):
    """后扣款请求模型 - 给定卡号、商铺、商品或金额，添加流水并扣款"""
    card_uid: str = Field(..., description="NFC卡片UID")
    booth_id: int = Field(..., description="商铺ID")
    product_id: Optional[int] = Field(None, description="商品ID（可选，若提供则使用商品价格）")
    amount: Optional[float] = Field(None, description="扣款金额（元，若未指定商品则必填）", gt=0)
    event_id: Optional[int] = Field(None, description="活动ID（可选，默认使用当前激活的活动）")
    remark: Optional[str] = Field(None, max_length=255, description="备注（可选）")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "card_uid": "A1B2C3D4",
                    "booth_id": 1,
                    "product_id": 5,
                    "remark": "后扣款 - 先消费后付款"
                },
                {
                    "card_uid": "A1B2C3D4",
                    "booth_id": 1,
                    "amount": 15.00,
                    "remark": "后扣款 - 手动指定金额"
                }
            ]
        }


@router.post("/booths/post-deduction")
async def post_payment_deduction(
    request: PostPaymentDeductionRequest,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    后扣款：给定卡号、商铺、商品或金额，添加流水并进行扣款。

    适用场景：先消费后付款，管理员事后补录扣款流水。

    逻辑：
    1. 如果指定了 product_id，使用商品价格作为扣款金额
    2. 如果未指定 product_id，则必须提供 amount
    3. 验证卡号、商铺、商品的有效性
    4. 从卡片对应账户余额中扣款，生成交易流水

    权限：仅 super_admin 和 event_admin 可操作。

    Request Body:
        - card_uid: NFC卡片UID（必填）
        - booth_id: 商铺ID（必填）
        - product_id: 商品ID（可选，若提供则使用商品价格）
        - amount: 扣款金额（可选，若未指定商品则必填）
        - event_id: 活动ID（可选，默认使用当前激活的活动）
        - remark: 备注（可选）

    Returns:
        JSON: 扣款结果，包含交易ID、扣款金额、余额变化等

    Error Responses:
        400: 参数错误（金额和商品都未指定、余额不足等）
        401: 未认证
        403: 权限不足
        404: 卡号/商铺/商品不存在
        500: 内部服务器错误
    """
    from models.booth import Booth
    from models.product import Product
    from models.transaction import Transaction

    try:
        # 1. 确定活动ID
        event_id = request.event_id
        if event_id is None:
            from services.event_service import EventService
            event_service = EventService(db)
            active_event = event_service.get_active_event()
            if active_event is None:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error_code": "NO_ACTIVE_EVENT",
                        "message": "没有活跃的活动，请指定 event_id 或激活一个活动"
                    }
                )
            event_id = active_event.id

        # 2. 验证商铺存在且属于该活动
        booth = db.query(Booth).filter(Booth.id == request.booth_id).first()
        if booth is None:
            return JSONResponse(
                status_code=404,
                content={
                    "error_code": "BOOTH_NOT_FOUND",
                    "message": f"商铺 ID {request.booth_id} 不存在"
                }
            )
        if booth.event_id != event_id:
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "BOOTH_NOT_IN_EVENT",
                    "message": f"商铺 {request.booth_id} 不属于活动 {event_id}"
                }
            )

        # 3. 确定扣款金额
        deduction_amount = None
        product_id = request.product_id
        product_name = None

        if product_id is not None:
            # 使用商品价格
            product = db.query(Product).filter(Product.id == product_id).first()
            if product is None:
                return JSONResponse(
                    status_code=404,
                    content={
                        "error_code": "PRODUCT_NOT_FOUND",
                        "message": f"商品 ID {product_id} 不存在"
                    }
                )
            if product.booth_id != request.booth_id:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error_code": "PRODUCT_NOT_IN_BOOTH",
                        "message": f"商品 {product_id} 不属于商铺 {request.booth_id}"
                    }
                )
            deduction_amount = float(product.price)
            product_name = product.name
        elif request.amount is not None:
            deduction_amount = request.amount
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "AMOUNT_REQUIRED",
                    "message": "必须指定 product_id 或 amount 中的至少一个"
                }
            )

        if deduction_amount <= 0:
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "INVALID_AMOUNT",
                    "message": "扣款金额必须大于0"
                }
            )

        # 4. 查找参与者
        from services.participant_service import ParticipantService
        participant_service = ParticipantService(db)
        try:
            participant = participant_service.get_participant_by_card(request.card_uid)
        except Exception:
            return JSONResponse(
                status_code=404,
                content={
                    "error_code": "PARTICIPANT_NOT_FOUND",
                    "message": f"卡号 {request.card_uid} 对应的参与者不存在"
                }
            )

        # 5. 获取或创建账户
        from services.account_service import AccountService
        account_service = AccountService(db)
        account = account_service.get_or_create_account(
            participant_id=participant.id,
            event_id=event_id
        )

        # 6. 构建备注
        remark = request.remark or "后扣款"
        if product_name:
            remark = f"{remark} - {product_name}"

        # 7. 执行扣款（通过 LedgerService）
        from services.ledger_service import LedgerService
        ledger_service = LedgerService(db)

        try:
            ledger_entry = ledger_service.append_debit_from_account(
                account_id=account.id,
                amount_yuan=deduction_amount,
                transaction_type="pay",
                event_id=event_id,
                participant_id=participant.id,
                merchant_id=None,
                remark=remark,
                booth_id=request.booth_id,
                product_id=product_id,
                operator_id=current_user.id
            )
        except Exception as e:
            from core.exceptions import InsufficientFundsError
            if isinstance(e, InsufficientFundsError):
                return JSONResponse(
                    status_code=400,
                    content={
                        "error_code": "INSUFFICIENT_FUNDS",
                        "message": f"余额不足，当前余额 {float(account.balance):.2f} 元，需扣款 {deduction_amount:.2f} 元"
                    }
                )
            raise

        logger.info(
            f"Post-payment deduction successful: card_uid={request.card_uid}, "
            f"booth_id={request.booth_id}, product_id={product_id}, "
            f"amount={deduction_amount:.2f} yuan, txn_id={ledger_entry.transaction_id}, "
            f"balance: {ledger_entry.balance_before} -> {ledger_entry.balance_after}, "
            f"operator={current_user.username}"
        )

        return {
            "success": True,
            "transaction_id": ledger_entry.transaction_id,
            "card_uid": request.card_uid,
            "participant_name": participant.name,
            "booth_id": request.booth_id,
            "booth_name": booth.name,
            "product_id": product_id,
            "product_name": product_name,
            "amount": deduction_amount,
            "balance_before": float(ledger_entry.balance_before),
            "balance_after": float(ledger_entry.balance_after),
            "event_id": event_id,
            "operator": current_user.username,
            "remark": remark,
            "message": f"后扣款成功：从 {participant.name} 扣款 ¥{deduction_amount:.2f}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Post-payment deduction failed: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": f"后扣款失败：{str(e)}"
            }
        )
