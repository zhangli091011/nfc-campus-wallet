"""
Balance query endpoint for NFC Campus Event Quota System.

提供 GET /balance 端点查询用户账户余额，支持活动模式和传统模式。
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from core.database import get_db
from services.user_service import UserService
from services.participant_service import ParticipantService, ParticipantNotFoundError
from services.account_service import AccountService
from services.event_service import EventService, EventNotFoundError
from core.exceptions import UserNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/balance")
async def get_balance(
    uid: Optional[str] = Query(None, description="User's unique identifier from NFC card (legacy mode)"),
    event_id: Optional[int] = Query(None, description="Event ID (event mode)"),
    card_uid: Optional[str] = Query(None, description="NFC card UID (event mode)"),
    timestamp: int = Query(..., description="Request timestamp in Unix seconds"),
    signature: str = Query(..., description="Request signature for authentication"),
    db: Session = Depends(get_db)
):
    """
    查询账户余额（支持活动模式和传统模式）。
    
    **Event Mode** (活动模式):
    Query Parameters:
        event_id: 活动ID
        card_uid: NFC卡片UID（十六进制字符串）
        timestamp: Unix时间戳（秒）
        signature: SHA256签名用于请求认证
    
    **Legacy Mode** (传统模式):
    Query Parameters:
        uid: 用户UID（十六进制字符串）
        timestamp: Unix时间戳（秒）
        signature: SHA256签名用于请求认证
    
    Returns:
        {
            "balance": 100.50
        }
    
    Error Responses:
        400: 参数错误、参与者不存在、活动不存在、用户不存在
        401: 认证失败（由中间件处理）
        500: 服务器内部错误
    
    Note:
        认证（时间戳和签名验证）由 SignatureVerificationMiddleware 处理。
    """
    try:
        # 判断请求模式
        event_mode = event_id is not None or card_uid is not None
        legacy_mode = uid is not None
        
        # 验证参数组合
        if event_mode and legacy_mode:
            logger.warning("Balance query failed: both event mode and legacy mode parameters provided")
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Cannot specify both event mode (event_id, card_uid) and legacy mode (uid) parameters"
                }
            )
        
        if not event_mode and not legacy_mode:
            logger.warning("Balance query failed: no valid parameters provided")
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Must specify either event mode (event_id, card_uid) or legacy mode (uid) parameters"
                }
            )
        
        # 活动模式
        if event_mode:
            # 验证活动模式参数完整性
            if event_id is None or card_uid is None:
                logger.warning("Balance query failed: incomplete event mode parameters")
                return JSONResponse(
                    status_code=400,
                    content={
                        "error_code": "VALIDATION_ERROR",
                        "message": "event_id and card_uid must both be present for event mode"
                    }
                )
            
            # 验证活动存在
            event_service = EventService(db)
            event = event_service.get_event(event_id)
            
            # 通过 card_uid 查找参与者
            participant_service = ParticipantService(db)
            participant = participant_service.get_participant_by_card(card_uid)
            
            # 查询账户余额
            account_service = AccountService(db)
            balance_cents = account_service.get_account_balance(participant.id, event_id)
            balance_yuan = balance_cents / 100.0
            
            logger.info(
                f"Balance query successful (event mode): event_id={event_id}, "
                f"card_uid={card_uid}, participant_id={participant.id}, "
                f"balance={balance_yuan} yuan"
            )
            
            return {"balance": balance_yuan}
        
        # 传统模式
        else:
            # 创建用户服务实例
            user_service = UserService(db)
            
            # 获取余额（元）
            balance_yuan = user_service.get_balance_yuan(uid)
            
            logger.info(f"Balance query successful (legacy mode): uid={uid}, balance={balance_yuan} yuan")
            
            return {"balance": balance_yuan}
    
    except EventNotFoundError as e:
        logger.warning(f"Balance query failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except ParticipantNotFoundError as e:
        logger.warning(f"Balance query failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except UserNotFoundError as e:
        logger.warning(f"Balance query failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in balance query: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )
