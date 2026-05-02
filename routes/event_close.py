"""
Event Close routes for NFC Campus Event System.

提供活动关场相关的 API 端点。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from core.database import get_db
from core.security import get_current_user
from services.event_service import EventService, EventNotFoundError
from services.ledger_service import LedgerService
from models.user import User
from models.account import Account
from models.transaction import Transaction
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class EventCloseRequest(BaseModel):
    """活动关场请求"""
    expire_quotas: bool = True  # 是否执行额度失效逻辑


class EventCloseResponse(BaseModel):
    """活动关场响应"""
    event_id: int
    status: str
    expired_accounts: int
    total_expired_amount: float


@router.post("/events/{event_id}/close", response_model=EventCloseResponse)
async def close_event(
    event_id: int,
    close_request: EventCloseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    关闭活动并执行额度失效逻辑。
    
    权限要求：super_admin 或 event_admin
    
    关场后的限制：
    - 禁止 pay（消费）
    - 禁止 recharge（充值）
    - 禁止 issue（发卡）
    - 仅管理员可进行 refund（退款）和 adjust（调整）
    
    Path Parameters:
        - event_id: 活动ID
    
    Request Body:
        - expire_quotas: 是否执行额度失效逻辑（默认 true）
    
    Returns:
        EventCloseResponse: 关场结果
        
    Error Responses:
        400: 活动不存在或已关闭
        403: 权限不足
        500: 内部服务器错误
    """
    try:
        # 权限验证
        if current_user.role not in ('super_admin', 'event_admin'):
            logger.warning(
                f"Event close denied: role '{current_user.role}' "
                f"(user={current_user.username})"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error_code": "PERMISSION_DENIED",
                    "message": f"Role '{current_user.role}' cannot close events"
                }
            )
        
        event_service = EventService(db)
        ledger_service = LedgerService(db)
        
        # 获取活动
        event = event_service.get_event(event_id)
        
        # 检查活动状态
        if event.status == 'ended':
            logger.warning(f"Event already closed: event_id={event_id}")
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "EVENT_ALREADY_CLOSED",
                    "message": f"Event {event_id} is already closed"
                }
            )
        
        # 更新活动状态为 ended
        event = event_service.update_event(
            event_id,
            status='ended',
            recharge_enabled=False,
            consume_enabled=False
        )
        
        expired_accounts = 0
        total_expired_amount = 0
        
        # 执行额度失效逻辑
        if close_request.expire_quotas:
            # 查询所有有余额的账户
            accounts = db.query(Account).filter(
                Account.event_id == event_id,
                Account.balance > 0
            ).all()
            
            for account in accounts:
                try:
                    # 生成 expire 类型流水，余额归零
                    ledger_entry = ledger_service.append_debit_from_account(
                        account_id=account.id,
                        amount_yuan=account.balance / 100.0,
                        transaction_type="expire",
                        event_id=event_id,
                        participant_id=account.participant_id,
                        remark=f"活动关场，额度失效"
                    )
                    
                    expired_accounts += 1
                    total_expired_amount += ledger_entry.amount
                    
                    logger.info(
                        f"Account expired: account_id={account.id}, "
                        f"amount={ledger_entry.amount} cents"
                    )
                    
                except Exception as e:
                    logger.error(
                        f"Failed to expire account {account.id}: {str(e)}",
                        exc_info=True
                    )
                    # 继续处理其他账户
                    continue
        
        logger.info(
            f"Event closed: event_id={event_id}, "
            f"expired_accounts={expired_accounts}, "
            f"total_expired_amount={total_expired_amount} cents, "
            f"closed_by={current_user.username}"
        )
        
        return EventCloseResponse(
            event_id=event_id,
            status=event.status,
            expired_accounts=expired_accounts,
            total_expired_amount=total_expired_amount / 100.0
        )
    
    except EventNotFoundError as e:
        logger.warning(f"Event not found: {event_id}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in event close: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )
