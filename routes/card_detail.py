"""
Card Detail API - 刷卡查看用户全部明细信息

提供通过 card_uid 查询参与者完整信息的接口，包括：
- 基本信息（姓名、班级、学号、状态）
- 账户余额
- 贷款摘要
- 最近交易流水
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import logging

from core.database import get_db
from core.security import get_current_user
from models.participant import Participant
from models.account import Account
from models.transaction import Transaction
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/card-detail", tags=["Card Detail"])


@router.get("/{card_uid}")
async def get_card_detail(
    card_uid: str,
    event_id: int = Query(..., description="活动ID"),
    txn_limit: int = Query(50, ge=1, le=200, description="交易记录数量限制"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    通过 NFC 卡片 UID 查询用户全部明细信息。

    返回：
    - participant: 参与者基本信息
    - account: 账户余额和信贷信息
    - loans: 贷款摘要（活跃贷款数量和总额）
    - transactions: 最近交易流水列表
    - stock_holdings: 股票持仓摘要

    权限：所有已登录用户均可查询（用于各终端刷卡查看）
    """
    # 1. 查找参与者
    participant = db.query(Participant).filter(
        Participant.card_uid == card_uid
    ).first()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到卡片 UID={card_uid} 对应的参与者"
        )

    # 2. 查询账户
    account = db.query(Account).filter(
        Account.participant_id == participant.id,
        Account.event_id == event_id,
    ).first()

    balance = float(account.balance) if account else 0.0
    credit_borrowed = float(account.credit_borrowed) if account and account.credit_borrowed else 0.0
    credit_fee_paid = float(account.credit_fee_paid) if account and account.credit_fee_paid else 0.0

    # 3. 查询贷款摘要
    loan_result = db.execute(
        text("""SELECT COUNT(*) as cnt, COALESCE(SUM(principal_amount), 0) as total
                FROM bank_loans
                WHERE participant_id = :pid AND event_id = :eid AND status = 'active'"""),
        {"pid": participant.id, "eid": event_id}
    ).mappings().first()

    loan_count = int(loan_result["cnt"]) if loan_result else 0
    loan_total = float(loan_result["total"]) if loan_result else 0.0

    # 4. 查询最近交易流水
    transactions_query = db.query(Transaction).filter(
        Transaction.participant_id == participant.id,
        Transaction.event_id == event_id,
    ).order_by(Transaction.created_at.desc(), Transaction.id.desc()).limit(txn_limit)

    transactions = transactions_query.all()

    txn_list = []
    for txn in transactions:
        txn_list.append({
            "id": txn.id,
            "type": txn.type,
            "amount": float(txn.amount) if txn.amount else 0.0,
            "balance_before": float(txn.balance_before) if txn.balance_before is not None else None,
            "balance_after": float(txn.balance_after) if txn.balance_after is not None else None,
            "remark": txn.remark,
            "operator_id": txn.operator_id,
            "booth_id": txn.booth_id if hasattr(txn, 'booth_id') else None,
            "created_at": txn.created_at.isoformat() if txn.created_at else None,
        })

    # 5. 查询股票持仓摘要（如果表存在）
    stock_holdings = []
    try:
        stock_rows = db.execute(
            text("""SELECT so.booth_id, b.name as booth_name,
                           SUM(CASE WHEN so.order_type = 'buy' THEN so.shares ELSE 0 END) -
                           SUM(CASE WHEN so.order_type = 'sell' THEN so.shares ELSE 0 END) as net_shares,
                           SUM(CASE WHEN so.order_type = 'buy' THEN so.total_amount ELSE 0 END) as total_invested
                    FROM stock_orders so
                    LEFT JOIN booths b ON so.booth_id = b.id
                    WHERE so.participant_id = :pid AND so.event_id = :eid
                    GROUP BY so.booth_id, b.name
                    HAVING net_shares > 0"""),
            {"pid": participant.id, "eid": event_id}
        ).mappings().all()

        for row in stock_rows:
            stock_holdings.append({
                "booth_id": row["booth_id"],
                "booth_name": row["booth_name"],
                "shares": int(row["net_shares"]),
                "total_invested": float(row["total_invested"]),
            })
    except Exception:
        # stock_orders 表可能不存在，静默忽略
        pass

    logger.info(
        f"Card detail queried: card_uid={card_uid}, participant={participant.name}, "
        f"balance={balance}, loans={loan_count}, txns={len(txn_list)}, "
        f"by={current_user.username}"
    )

    return {
        "participant": {
            "id": participant.id,
            "name": participant.name,
            "card_uid": participant.card_uid,
            "class_name": participant.class_name,
            "student_no": participant.student_no,
            "status": participant.status,
            "created_at": participant.created_at.isoformat() if participant.created_at else None,
        },
        "account": {
            "balance": balance,
            "credit_borrowed": credit_borrowed,
            "credit_fee_paid": credit_fee_paid,
        },
        "loans": {
            "active_count": loan_count,
            "total_debt": loan_total,
        },
        "stock_holdings": stock_holdings,
        "transactions": txn_list,
        "transaction_count": len(txn_list),
    }
