"""
Recharge endpoint for NFC Campus E-Wallet System (Ledger Mode + Event Mode).

提供 POST /recharge 端点处理充值交易，支持活动模式和传统模式。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
import logging

from app.database import get_db
from app.config import get_settings
from schemas.transaction import RechargeRequest, TransactionResponse
from services.transaction_service import TransactionService
from core.exceptions import UserNotFoundError, InvalidTransactionError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/recharge", response_model=TransactionResponse)
async def process_recharge(
    request: RechargeRequest,
    db: Session = Depends(get_db)
):
    """
    处理充值交易（支持活动模式和传统模式）。
    
    **活动模式 Request Body:**
    ```json
    {
        "event_id": 1,
        "card_uid": "A1B2C3D4",
        "amount": 50.00,
        "timestamp": 1234567890,
        "signature": "abc123...",
        "operator_id": "ADMIN001",
        "remark": "现金充值"
    }
    ```
    
    **传统模式 Request Body:**
    ```json
    {
        "uid": "A1B2C3D4",
        "amount": 50.00,
        "timestamp": 1234567890,
        "signature": "abc123...",
        "operator_id": "ADMIN001",
        "remark": "现金充值"
    }
    ```
    
    **Returns:**
    ```json
    {
        "success": true,
        "new_balance": 150.50,
        "transaction_id": 12346,
        "balance_before": 100.50
    }
    ```
    
    **Error Responses:**
    - 400: 验证错误、用户/参与者不存在、活动不允许充值
    - 401: 认证失败（由中间件处理）
    - 500: 内部服务器错误
    
    **Note:**
    - 认证（时间戳和签名验证）由 SignatureVerificationMiddleware 处理
    - 管理员授权是占位符，生产环境需要实现
    - 请求模式通过字段自动检测：event_id + card_uid = 活动模式，uid = 传统模式
    """
    try:
        # 获取配置
        settings = get_settings()
        
        # TODO: 验证管理员授权（占位符）
        # 生产环境需要检查请求用户是否有管理员权限
        
        # 验证金额限制
        if request.amount > settings.max_transaction_amount:
            logger.warning(
                f"Recharge validation failed: Amount {request.amount} exceeds "
                f"maximum {settings.max_transaction_amount}"
            )
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "VALIDATION_ERROR",
                    "message": f"Amount exceeds maximum transaction limit of {settings.max_transaction_amount}",
                    "field": "amount",
                    "value": request.amount
                }
            )
        
        # 创建交易服务实例
        transaction_service = TransactionService(db)
        
        # 请求模式判断：活动模式 vs 传统模式
        if request.event_id and request.card_uid:
            # 活动模式（新）
            result = transaction_service.process_event_recharge(
                event_id=request.event_id,
                card_uid=request.card_uid,
                amount_yuan=request.amount,
                operator_id=request.operator_id,
                remark=request.remark
            )
            
            logger.info(
                f"Event recharge successful: event_id={request.event_id}, "
                f"card_uid={request.card_uid}, amount={request.amount} yuan, "
                f"txn_id={result.transaction_id}, "
                f"balance: {result.balance_before_yuan} -> {result.new_balance_yuan} yuan"
            )
        
        elif request.uid:
            # 传统模式（旧）
            result = transaction_service.process_recharge(
                uid=request.uid,
                amount_yuan=request.amount,
                operator_id=request.operator_id,
                remark=request.remark
            )
            
            logger.info(
                f"Legacy recharge successful: uid={request.uid}, amount={request.amount} yuan, "
                f"txn_id={result.transaction_id}, "
                f"balance: {result.balance_before_yuan} -> {result.new_balance_yuan} yuan"
            )
        
        else:
            # 不应该到达这里，因为 RechargeRequest 已经验证了
            logger.error("Invalid request mode: neither event mode nor legacy mode")
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Invalid request: must specify either event mode (event_id, card_uid) or legacy mode (uid)"
                }
            )
        
        return TransactionResponse(
            success=result.success,
            new_balance=result.new_balance_yuan,
            transaction_id=result.transaction_id,
            balance_before=result.balance_before_yuan
        )
    
    except UserNotFoundError as e:
        logger.warning(f"Recharge failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except InvalidTransactionError as e:
        logger.warning(f"Recharge failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except ValueError as e:
        logger.warning(f"Recharge validation failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": str(e)
            }
        )
    
    except Exception as e:
        # Import event-related exceptions dynamically to handle them
        from services.event_service import EventNotFoundError, EventInactiveError
        from services.participant_service import ParticipantNotFoundError
        
        # Check if it's an event-related exception
        if isinstance(e, (EventNotFoundError, EventInactiveError, ParticipantNotFoundError)):
            logger.warning(f"Recharge failed: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": e.error_code,
                    "message": e.message
                }
            )
        
        # Unknown error
        logger.error(
            f"Unexpected error in recharge processing: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )
