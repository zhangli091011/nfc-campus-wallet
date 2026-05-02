"""
Payment endpoint for NFC Campus E-Wallet System (Ledger Mode + Event Mode + Booth Mode).

提供 POST /pay 端点处理支付交易，支持活动模式、传统模式和摊位模式。
"""

from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from app.database import get_db
from app.config import get_settings
from schemas.transaction import PaymentRequest, TransactionResponse
from services.transaction_service import TransactionService
from core.exceptions import (
    InsufficientFundsError,
    UserNotFoundError,
    InvalidTransactionError,
    ValidationError,
    ResourceNotFoundError
)
from services.merchant_service import (
    MerchantService,
    MerchantNotFoundError,
    MerchantInactiveError
)
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

# Optional HTTPBearer for JWT authentication
optional_security = HTTPBearer(auto_error=False)


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional JWT authentication dependency.
    Returns User if valid token is provided, None otherwise.
    Does not raise exceptions for missing or invalid tokens.
    """
    if credentials is None:
        return None
    
    try:
        from core.security import decode_access_token
        from core.config import get_settings
        
        settings = get_settings()
        token = credentials.credentials
        
        # Decode and verify JWT token
        payload = decode_access_token(
            token=token,
            jwt_secret_key=settings.jwt_secret_key,
            jwt_algorithm=settings.jwt_algorithm
        )
        
        # Extract user_id from payload
        user_id: int = payload.get("user_id")
        if user_id is None:
            return None
        
        # Query user from database
        user = db.query(User).filter(User.id == user_id).first()
        
        # Check if user exists and is active
        if user is None or user.status in ('blocked', 'inactive'):
            return None
        
        return user
    
    except Exception as e:
        # Log the error but don't raise exception (optional authentication)
        logger.debug(f"Optional JWT authentication failed: {str(e)}")
        return None


@router.post("/pay", response_model=TransactionResponse)
async def process_payment(
    request: PaymentRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    处理支付交易（支持活动模式、传统模式和摊位模式）。
    
    **摊位模式 Request Body:**
    ```json
    {
        "event_id": 1,
        "card_uid": "A1B2C3D4",
        "booth_id": 1,
        "product_id": 5,
        "amount": 25.00,
        "timestamp": 1234567890,
        "signature": "abc123..."
    }
    ```
    Headers: Authorization: Bearer <JWT_TOKEN>
    
    **活动模式 Request Body:**
    ```json
    {
        "event_id": 1,
        "card_uid": "A1B2C3D4",
        "amount": 25.00,
        "timestamp": 1234567890,
        "signature": "abc123...",
        "merchant_id": "MERCHANT001",
        "remark": "购买商品"
    }
    ```
    
    **传统模式 Request Body:**
    ```json
    {
        "uid": "A1B2C3D4",
        "amount": 25.00,
        "timestamp": 1234567890,
        "signature": "abc123...",
        "merchant_id": "MERCHANT001",
        "remark": "购买商品"
    }
    ```
    
    **Returns:**
    ```json
    {
        "success": true,
        "new_balance": 75.50,
        "transaction_id": 12345,
        "balance_before": 100.50,
        "booth_id": 1,
        "product_id": 5,
        "operator_id": 3
    }
    ```
    
    **Error Responses:**
    - 400: 验证错误、余额不足、用户/参与者不存在、活动不允许消费
    - 401: 认证失败（摊位模式需要 JWT 令牌）
    - 403: 权限不足（操作员无权操作该摊位）
    - 500: 内部服务器错误
    
    **Note:**
    - 认证（时间戳和签名验证）由 SignatureVerificationMiddleware 处理
    - 摊位模式需要 JWT 认证，从令牌中提取 operator_id
    - 请求模式通过字段自动检测：
      - booth_id 存在 = 摊位模式（需要 JWT 认证）
      - event_id + card_uid = 活动模式
      - uid = 传统模式
    
    Validates Requirements:
        - Requirement 10.1: Require event_id, booth_id, and operator_id for booth payments
        - Requirement 10.2: Accept optional product_id
        - Requirement 10.3: Verify product belongs to booth
        - Requirement 10.4: Verify booth belongs to event
        - Requirement 10.5: Verify operator has permission
        - Requirement 10.6: Record booth_id, product_id, operator_id
        - Requirement 10.7: Maintain backward compatibility
        - Requirement 16.2: Allow existing payment operations without booth information
    """
    try:
        # 获取配置
        settings = get_settings()
        
        # 验证金额限制
        if request.amount > settings.max_transaction_amount:
            logger.warning(
                f"Payment validation failed: Amount {request.amount} exceeds "
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
        
        # 验证商户（如果提供）
        if request.merchant_id:
            merchant_service = MerchantService(db)
            merchant_service.validate_merchant(request.merchant_id)
        
        # 创建交易服务实例
        transaction_service = TransactionService(db)
        
        # 请求模式判断：摊位模式 vs 活动模式 vs 传统模式
        if request.booth_id is not None:
            # 摊位模式（Booth Management System）
            # 需要 JWT 认证，从令牌中提取 operator_id
            
            # 验证 JWT 认证
            if current_user is None:
                logger.warning("Booth payment attempted without JWT authentication")
                return JSONResponse(
                    status_code=401,
                    content={
                        "error_code": "AUTHENTICATION_REQUIRED",
                        "message": "Booth payments require JWT authentication. Please provide a valid Bearer token in the Authorization header."
                    }
                )
            
            # 验证必需的活动模式字段
            if request.event_id is None or request.card_uid is None:
                logger.warning("Booth payment missing required event mode fields")
                return JSONResponse(
                    status_code=400,
                    content={
                        "error_code": "VALIDATION_ERROR",
                        "message": "Booth payments require event_id and card_uid fields"
                    }
                )
            
            # 调用摊位支付处理
            result = transaction_service.process_booth_payment(
                event_id=request.event_id,
                card_uid=request.card_uid,
                booth_id=request.booth_id,
                amount_yuan=request.amount,
                operator_id=current_user.id,  # 从 JWT 令牌提取
                product_id=request.product_id,
                remark=request.remark
            )
            
            logger.info(
                f"Booth payment successful: event_id={request.event_id}, "
                f"card_uid={request.card_uid}, booth_id={request.booth_id}, "
                f"product_id={request.product_id}, operator_id={current_user.id}, "
                f"amount={request.amount} yuan, txn_id={result.transaction_id}, "
                f"balance: {result.balance_before_yuan} -> {result.new_balance_yuan} yuan"
            )
            
            # 返回包含摊位信息的响应
            return TransactionResponse(
                success=result.success,
                new_balance=result.new_balance_yuan,
                transaction_id=result.transaction_id,
                balance_before=result.balance_before_yuan,
                booth_id=request.booth_id,
                product_id=request.product_id,
                operator_id=current_user.id
            )
        
        elif request.event_id and request.card_uid:
            # 活动模式（新）
            result = transaction_service.process_event_payment(
                event_id=request.event_id,
                card_uid=request.card_uid,
                amount_yuan=request.amount,
                merchant_id=request.merchant_id,
                remark=request.remark
            )
            
            logger.info(
                f"Event payment successful: event_id={request.event_id}, "
                f"card_uid={request.card_uid}, amount={request.amount} yuan, "
                f"txn_id={result.transaction_id}, "
                f"balance: {result.balance_before_yuan} -> {result.new_balance_yuan} yuan"
            )
        
        elif request.uid:
            # 传统模式（旧）
            result = transaction_service.process_payment(
                uid=request.uid,
                amount_yuan=request.amount,
                merchant_id=request.merchant_id,
                remark=request.remark
            )
            
            logger.info(
                f"Legacy payment successful: uid={request.uid}, amount={request.amount} yuan, "
                f"txn_id={result.transaction_id}, "
                f"balance: {result.balance_before_yuan} -> {result.new_balance_yuan} yuan"
            )
        
        else:
            # 不应该到达这里，因为 PaymentRequest 已经验证了
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
        logger.warning(f"Payment failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except MerchantNotFoundError as e:
        logger.warning(f"Payment failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except MerchantInactiveError as e:
        logger.warning(f"Payment failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except InsufficientFundsError as e:
        logger.warning(f"Payment failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except InvalidTransactionError as e:
        logger.warning(f"Payment failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except ValidationError as e:
        logger.warning(f"Payment failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except ResourceNotFoundError as e:
        logger.warning(f"Payment failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except ValueError as e:
        logger.warning(f"Payment validation failed: {str(e)}")
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
            logger.warning(f"Payment failed: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": e.error_code,
                    "message": e.message
                }
            )
        
        # Unknown error
        logger.error(
            f"Unexpected error in payment processing: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )
