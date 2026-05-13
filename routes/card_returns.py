"""
Card Return Records API - 退卡记录查询

提供后台查看退卡记录的接口，包含：
- 退卡人信息（姓名、班级、学号）
- 原卡号
- 退卡时余额、退款金额
- 关联的交易流水
- 贷款清偿情况
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, desc
from typing import Optional
import logging

from core.database import get_db
from core.security import get_current_user, RoleChecker
from models.user import User
from models.participant import Participant
from models.transaction import Transaction
from models.account import Account

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/card-returns", tags=["Card Returns"])


@router.get("")
async def get_card_return_records(
    event_id: int = Query(..., description="活动ID"),
    search: Optional[str] = Query(None, description="搜索关键词（姓名/卡号/学号）"),
    limit: int = Query(50, ge=1, le=500, description="返回记录数"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db),
):
    """
    获取退卡记录列表。

    退卡记录通过以下方式识别：
    - 参与者 status = 'inactive' 且 card_uid 以 'RETURNED_' 开头

    返回每条记录包含：
    - 参与者基本信息
    - 原卡号
    - 退卡时的余额和退款金额
    - 退卡操作时间
    - 关联贷款信息
    """
    try:
        # 查询已退卡的参与者
        query = db.query(Participant).filter(
            Participant.status == 'inactive',
            Participant.card_uid.like('RETURNED_%')
        )

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Participant.name.like(search_pattern)) |
                (Participant.card_uid.like(search_pattern)) |
                (Participant.student_no.like(search_pattern))
            )

        total_count = query.count()
        participants = query.order_by(desc(Participant.updated_at)).offset(offset).limit(limit).all()

        records = []
        for p in participants:
            # 从 card_uid 中提取原始卡号: RETURNED_{original_uid}_{id}
            original_card_uid = _extract_original_card_uid(p.card_uid, p.id)

            # 查询账户信息
            account = db.query(Account).filter(
                Account.participant_id == p.id,
                Account.event_id == event_id,
            ).first()

            # 查询退卡相关的 correction 流水（退款记录）
            return_txns = db.query(Transaction).filter(
                Transaction.participant_id == p.id,
                Transaction.event_id == event_id,
                Transaction.type == 'correction',
                Transaction.remark.like('%退卡%'),
            ).order_by(desc(Transaction.created_at)).all()

            # 退款金额和退卡时间
            refunded_amount = 0.0
            return_time = None
            balance_at_return = 0.0
            operator_id = None

            if return_txns:
                for txn in return_txns:
                    refunded_amount += float(txn.amount)
                # 最后一笔退卡流水的时间作为退卡时间
                return_time = return_txns[0].created_at.isoformat() if return_txns[0].created_at else None
                balance_at_return = float(return_txns[-1].balance_before) if return_txns else 0.0
                operator_id = return_txns[0].operator_id

            # 查询贷款情况
            loan_info = db.execute(
                text("""SELECT COUNT(*) as cnt, 
                        COALESCE(SUM(principal_amount), 0) as total_principal,
                        SUM(CASE WHEN status = 'card_returned' THEN principal_amount ELSE 0 END) as remaining_debt
                        FROM bank_loans
                        WHERE participant_id = :pid AND event_id = :eid"""),
                {"pid": p.id, "eid": event_id}
            ).mappings().first()

            # 查询操作员名称
            operator_name = None
            if operator_id:
                try:
                    op_user = db.query(User).filter(User.id == int(operator_id)).first()
                    if op_user:
                        operator_name = op_user.username
                except (ValueError, TypeError):
                    pass

            records.append({
                "id": p.id,
                "name": p.name,
                "class_name": p.class_name,
                "student_no": p.student_no,
                "original_card_uid": original_card_uid,
                "balance_at_return": balance_at_return,
                "refunded_amount": refunded_amount,
                "return_time": return_time,
                "operator_name": operator_name,
                "loan_count": int(loan_info["cnt"]) if loan_info else 0,
                "loan_total_principal": float(loan_info["total_principal"]) if loan_info else 0.0,
                "loan_remaining_debt": float(loan_info["remaining_debt"]) if loan_info else 0.0,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            })

        return {
            "records": records,
            "total_count": total_count,
            "event_id": event_id,
        }

    except Exception as e:
        logger.error(f"Get card return records failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{participant_id}/detail")
async def get_card_return_detail(
    participant_id: int,
    event_id: int = Query(..., description="活动ID"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db),
):
    """
    获取单个退卡记录的完整明细，包含全部交易流水。
    """
    try:
        participant = db.query(Participant).filter(Participant.id == participant_id).first()
        if not participant:
            raise HTTPException(status_code=404, detail="参与者不存在")

        original_card_uid = _extract_original_card_uid(participant.card_uid, participant.id)

        # 查询该参与者在该活动下的所有交易流水
        transactions = db.query(Transaction).filter(
            Transaction.participant_id == participant_id,
            Transaction.event_id == event_id,
        ).order_by(desc(Transaction.created_at), desc(Transaction.id)).all()

        txn_list = []
        for txn in transactions:
            txn_list.append({
                "id": txn.id,
                "type": txn.type,
                "amount": float(txn.amount),
                "balance_before": float(txn.balance_before) if txn.balance_before is not None else 0.0,
                "balance_after": float(txn.balance_after) if txn.balance_after is not None else 0.0,
                "remark": txn.remark,
                "operator_id": txn.operator_id,
                "booth_id": txn.booth_id if hasattr(txn, 'booth_id') else None,
                "merchant_id": txn.merchant_id,
                "created_at": txn.created_at.isoformat() if txn.created_at else None,
            })

        # 查询贷款记录
        loans = db.execute(
            text("""SELECT id, principal_amount, fee_amount, disbursed_amount, 
                           status, remark, created_at, repaid_at
                    FROM bank_loans
                    WHERE participant_id = :pid AND event_id = :eid
                    ORDER BY created_at DESC"""),
            {"pid": participant_id, "eid": event_id}
        ).mappings().all()

        loan_list = []
        for loan in loans:
            loan_list.append({
                "id": loan["id"],
                "principal_amount": float(loan["principal_amount"]),
                "fee_amount": float(loan["fee_amount"]),
                "disbursed_amount": float(loan["disbursed_amount"]),
                "status": loan["status"],
                "remark": loan["remark"],
                "created_at": loan["created_at"].isoformat() if loan["created_at"] else None,
                "repaid_at": loan["repaid_at"].isoformat() if loan["repaid_at"] else None,
            })

        # 账户信息
        account = db.query(Account).filter(
            Account.participant_id == participant_id,
            Account.event_id == event_id,
        ).first()

        return {
            "participant": {
                "id": participant.id,
                "name": participant.name,
                "class_name": participant.class_name,
                "student_no": participant.student_no,
                "original_card_uid": original_card_uid,
                "status": participant.status,
                "created_at": participant.created_at.isoformat() if participant.created_at else None,
            },
            "account": {
                "balance": float(account.balance) if account else 0.0,
                "credit_borrowed": float(account.credit_borrowed) if account and account.credit_borrowed else 0.0,
                "credit_fee_paid": float(account.credit_fee_paid) if account and account.credit_fee_paid else 0.0,
            } if account else None,
            "transactions": txn_list,
            "loans": loan_list,
            "transaction_count": len(txn_list),
            "loan_count": len(loan_list),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get card return detail failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _extract_original_card_uid(stored_uid: str, participant_id: int) -> str:
    """从存储的 card_uid 中提取原始卡号。格式: RETURNED_{original}_{id}"""
    prefix = "RETURNED_"
    suffix = f"_{participant_id}"
    if stored_uid.startswith(prefix) and stored_uid.endswith(suffix):
        return stored_uid[len(prefix):-len(suffix)]
    elif stored_uid.startswith(prefix):
        # 兼容：去掉前缀，尝试去掉最后的 _数字
        rest = stored_uid[len(prefix):]
        parts = rest.rsplit("_", 1)
        if len(parts) == 2 and parts[1].isdigit():
            return parts[0]
        return rest
    return stored_uid
