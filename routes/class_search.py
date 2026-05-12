"""
Class search routes for NFC Campus Event Quota System.

提供按班级搜索参与者及其交易流水的 API 端点。
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
import logging

from core.database import get_db
from core.security import get_current_user, RoleChecker
from models.user import User
from models.participant import Participant
from models.account import Account
from models.transaction import Transaction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin")


@router.get("/class-search")
async def search_by_class(
    event_id: int = Query(..., description="活动ID"),
    class_name: str = Query(..., min_length=1, description="班级名称（支持模糊搜索）"),
    include_transactions: bool = Query(False, description="是否包含交易流水"),
    txn_limit: int = Query(20, ge=1, le=100, description="每人交易流水条数限制"),
    limit: int = Query(100, ge=1, le=500, description="返回参与者数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    按班级搜索参与者及其交易流水。

    Query Parameters:
        - event_id: 活动ID（必填）
        - class_name: 班级名称，支持模糊匹配（必填）
        - include_transactions: 是否包含每人的交易流水（默认 false）
        - txn_limit: 每人交易流水条数限制（默认20，最大100）
        - limit: 返回参与者数量限制（默认100，最大500）
        - offset: 偏移量（默认0）

    Returns:
        {
            "class_name": "高一(1)班",
            "event_id": 1,
            "participants": [...],
            "total_count": 25,
            "summary": {
                "total_balance": 2500.00,
                "total_consumed": 1200.00,
                "total_recharged": 3000.00,
                "total_credit_borrowed": 500.00,
                "participant_count": 25
            }
        }
    """
    try:
        search_pattern = f"%{class_name}%"

        # 查询参与者 + 账户信息
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
        ).filter(
            Participant.class_name.like(search_pattern)
        )

        # 总数
        total_count = query.count()

        # 班级汇总统计
        summary_query = db.query(
            func.coalesce(func.sum(Account.balance), 0).label("total_balance"),
            func.coalesce(func.sum(Account.credit_borrowed), 0).label("total_credit_borrowed"),
            func.coalesce(func.sum(Account.credit_fee_paid), 0).label("total_credit_fee"),
        ).join(
            Participant,
            Account.participant_id == Participant.id
        ).filter(
            Participant.class_name.like(search_pattern),
            Account.event_id == event_id
        )
        summary_row = summary_query.first()

        # 班级消费/充值统计
        from sqlalchemy import case
        txn_summary = db.query(
            func.coalesce(
                func.sum(case((Transaction.type == 'pay', Transaction.amount), else_=0)), 0
            ).label("total_consumed"),
            func.coalesce(
                func.sum(case((Transaction.type == 'recharge', Transaction.amount), else_=0)), 0
            ).label("total_recharged"),
            func.coalesce(
                func.sum(case((Transaction.type == 'refund', Transaction.amount), else_=0)), 0
            ).label("total_refunded"),
        ).join(
            Participant,
            Transaction.participant_id == Participant.id
        ).filter(
            Participant.class_name.like(search_pattern),
            Transaction.event_id == event_id
        ).first()

        # 排序：按余额降序
        query = query.order_by(func.coalesce(Account.balance, 0).desc())

        # 分页
        results = query.limit(limit).offset(offset).all()

        # 构建参与者列表
        participants_data = []
        participant_ids = []
        for row in results:
            participant_ids.append(row.id)
            p_data = {
                "id": row.id,
                "name": row.name,
                "card_uid": row.card_uid,
                "class_name": row.class_name,
                "student_no": row.student_no,
                "status": row.status,
                "balance": float(row.balance) if row.balance is not None else 0.0,
                "credit_borrowed": float(row.credit_borrowed) if row.credit_borrowed is not None else 0.0,
                "credit_fee_paid": float(row.credit_fee_paid) if row.credit_fee_paid is not None else 0.0,
                "transactions": [],
            }
            participants_data.append(p_data)

        # 如果需要交易流水，批量查询
        if include_transactions and participant_ids:
            # 查询每人最近的 N 条交易
            txn_query = db.query(Transaction).filter(
                Transaction.participant_id.in_(participant_ids),
                Transaction.event_id == event_id
            ).order_by(Transaction.participant_id, Transaction.created_at.desc())

            txn_rows = txn_query.all()

            # 按 participant_id 分组，每人最多 txn_limit 条
            txn_map: dict = {}
            for txn in txn_rows:
                pid = txn.participant_id
                if pid not in txn_map:
                    txn_map[pid] = []
                if len(txn_map[pid]) < txn_limit:
                    txn_map[pid].append({
                        "id": txn.id,
                        "type": txn.type,
                        "amount": float(txn.amount),
                        "balance_before": float(txn.balance_before),
                        "balance_after": float(txn.balance_after),
                        "remark": txn.remark,
                        "operator_id": txn.operator_id,
                        "card_uid": txn.card_uid,
                        "created_at": txn.created_at.isoformat() if txn.created_at else None,
                    })

            # 填充到参与者数据中
            for p_data in participants_data:
                p_data["transactions"] = txn_map.get(p_data["id"], [])

        summary = {
            "total_balance": float(summary_row.total_balance) if summary_row else 0.0,
            "total_credit_borrowed": float(summary_row.total_credit_borrowed) if summary_row else 0.0,
            "total_credit_fee": float(summary_row.total_credit_fee) if summary_row else 0.0,
            "total_consumed": float(txn_summary.total_consumed) if txn_summary else 0.0,
            "total_recharged": float(txn_summary.total_recharged) if txn_summary else 0.0,
            "total_refunded": float(txn_summary.total_refunded) if txn_summary else 0.0,
            "participant_count": total_count,
        }

        logger.info(
            f"Class search: class_name='{class_name}', event_id={event_id}, "
            f"found={total_count}, include_txn={include_transactions}, "
            f"by user={current_user.username}"
        )

        return {
            "class_name": class_name,
            "event_id": event_id,
            "participants": participants_data,
            "total_count": total_count,
            "summary": summary,
        }

    except Exception as e:
        logger.error(f"Class search failed: {str(e)}", exc_info=True)
        return {"error_code": "INTERNAL_ERROR", "message": str(e)}


@router.get("/class-list")
async def get_class_list(
    event_id: Optional[int] = Query(None, description="活动ID（可选，不填则返回所有班级）"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    获取所有班级列表及人数统计。

    Returns:
        {
            "classes": [
                {"class_name": "高一(1)班", "participant_count": 30, "total_balance": 1500.00},
                ...
            ]
        }
    """
    try:
        query = db.query(
            Participant.class_name,
            func.count(Participant.id).label("participant_count"),
        ).filter(
            Participant.class_name.isnot(None),
            Participant.class_name != "",
            Participant.status == "active",
        ).group_by(Participant.class_name)

        # 如果指定了 event_id，只统计有账户的参与者
        if event_id:
            query = db.query(
                Participant.class_name,
                func.count(func.distinct(Participant.id)).label("participant_count"),
                func.coalesce(func.sum(Account.balance), 0).label("total_balance"),
            ).join(
                Account,
                (Account.participant_id == Participant.id) & (Account.event_id == event_id)
            ).filter(
                Participant.class_name.isnot(None),
                Participant.class_name != "",
                Participant.status == "active",
            ).group_by(Participant.class_name)

        rows = query.order_by(Participant.class_name).all()

        classes = []
        for row in rows:
            item = {
                "class_name": row.class_name,
                "participant_count": row.participant_count,
            }
            if event_id:
                item["total_balance"] = float(row.total_balance)
            classes.append(item)

        return {"classes": classes, "total_classes": len(classes)}

    except Exception as e:
        logger.error(f"Get class list failed: {str(e)}", exc_info=True)
        return {"error_code": "INTERNAL_ERROR", "message": str(e)}
