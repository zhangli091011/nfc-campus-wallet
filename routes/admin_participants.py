"""
Admin participants routes for NFC Campus Event Quota System.

提供管理后台查看参与者余额的 API 端点。
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from core.database import get_db
from core.security import get_current_user, RoleChecker
from models.user import User
from models.participant import Participant
from models.account import Account

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin")


@router.get("/participants/balances")
async def get_participants_balances(
    event_id: int = Query(..., description="活动ID"),
    search: Optional[str] = Query(None, description="搜索关键词（姓名/卡号/学号）"),
    sort_by: Optional[str] = Query("balance_desc", description="排序方式: balance_desc, balance_asc, name"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    查询指定活动下所有参与者的余额信息。

    Query Parameters:
        - event_id: 活动ID（必填）
        - search: 搜索关键词，支持姓名/卡号/学号模糊匹配（可选）
        - sort_by: 排序方式（可选，默认按余额降序）
        - limit: 返回记录数限制（默认100，最大1000）
        - offset: 偏移量（默认0）

    Returns:
        {
            "participants": [...],
            "total_count": 100,
            "total_balance": 5000.00,
            "event_id": 1
        }

    Error Responses:
        401: 未认证
        403: 权限不足
        500: 内部服务器错误
    """
    try:
        # 构建查询：参与者 LEFT JOIN 账户
        query = db.query(
            Participant.id,
            Participant.name,
            Participant.card_uid,
            Participant.class_name,
            Participant.student_no,
            Participant.status,
            Account.balance,
            Account.credit_borrowed,
            Account.credit_fee_paid,
        ).outerjoin(
            Account,
            (Account.participant_id == Participant.id) & (Account.event_id == event_id)
        )

        # 搜索过滤
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Participant.name.like(search_pattern)) |
                (Participant.card_uid.like(search_pattern)) |
                (Participant.student_no.like(search_pattern))
            )

        # 获取总数
        total_count = query.count()

        # 计算总余额
        total_balance_result = db.query(
            func.coalesce(func.sum(Account.balance), 0)
        ).filter(Account.event_id == event_id).scalar()
        total_balance = float(total_balance_result) if total_balance_result else 0.0

        # 排序
        if sort_by == "balance_asc":
            query = query.order_by(func.coalesce(Account.balance, 0).asc())
        elif sort_by == "name":
            query = query.order_by(Participant.name.asc())
        else:  # balance_desc (default)
            query = query.order_by(func.coalesce(Account.balance, 0).desc())

        # 分页
        results = query.limit(limit).offset(offset).all()

        # 构建响应
        participants_data = []
        for row in results:
            participants_data.append({
                "id": row.id,
                "name": row.name,
                "card_uid": row.card_uid,
                "class_name": row.class_name,
                "student_no": row.student_no,
                "status": row.status,
                "balance": float(row.balance) if row.balance is not None else 0.0,
                "credit_borrowed": float(row.credit_borrowed) if row.credit_borrowed is not None else 0.0,
                "credit_fee_paid": float(row.credit_fee_paid) if row.credit_fee_paid is not None else 0.0,
            })

        logger.info(
            f"Admin participants balances queried: event_id={event_id}, "
            f"count={len(participants_data)}, total={total_count}, "
            f"by user={current_user.username}"
        )

        return {
            "participants": participants_data,
            "total_count": total_count,
            "total_balance": total_balance,
            "event_id": event_id,
        }

    except Exception as e:
        logger.error(
            f"Unexpected error in admin participants balances: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )
