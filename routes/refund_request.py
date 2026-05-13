"""
退款申请模块 API

收银员提交退款申请 → 超级管理员审批 → 审批通过后自动执行退款

POST /refund/requests          - 收银员提交退款申请
GET  /refund/requests          - 查看退款申请列表
POST /refund/requests/{id}/approve - 管理员审批通过
POST /refund/requests/{id}/reject  - 管理员驳回
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text, desc
import logging

from core.database import get_db
from core.security import get_current_user, RoleChecker
from models.transaction import Transaction
from models.account import Account
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/refund", tags=["Refund Request"])


# ============================================================================
# Schemas
# ============================================================================

class RefundRequestCreate(BaseModel):
    """收银员提交退款申请"""
    original_transaction_id: int = Field(..., description="原支付流水ID")
    reason: str = Field(..., min_length=1, max_length=500, description="退款原因")


class RefundRequestApprove(BaseModel):
    """管理员审批"""
    remark: str = Field("", max_length=255, description="审批备注")


# ============================================================================
# POST /refund/requests - 收银员提交退款申请
# ============================================================================

@router.post("/requests")
async def create_refund_request(
    req: RefundRequestCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    收银员提交退款申请。

    - booth_cashier 提交后需要 super_admin 审批
    - super_admin / event_admin 提交后自动通过（直接执行退款）
    """
    # 验证原交易存在且为 pay 类型
    original_txn = db.query(Transaction).filter(
        Transaction.id == req.original_transaction_id
    ).first()

    if original_txn is None:
        raise HTTPException(status_code=404, detail="原交易流水不存在")

    if original_txn.type != "pay":
        raise HTTPException(status_code=400, detail=f"仅支持对 pay 类型交易退款，当前类型为 '{original_txn.type}'")

    # 检查是否已退款
    existing_refund = db.query(Transaction).filter(
        Transaction.related_txn_id == req.original_transaction_id,
        Transaction.type == "refund"
    ).first()
    if existing_refund:
        raise HTTPException(status_code=400, detail="该交易已退款，不可重复退款")

    # 检查是否已有待审批的申请
    existing_request = db.execute(
        text("""SELECT id FROM refund_requests 
                WHERE original_transaction_id = :tid AND status = 'pending'"""),
        {"tid": req.original_transaction_id}
    ).first()
    if existing_request:
        raise HTTPException(status_code=400, detail="该交易已有待审批的退款申请")

    # 如果是管理员，直接执行退款
    if current_user.role in ("super_admin", "event_admin"):
        return await _execute_refund(db, original_txn, current_user, req.reason)

    # booth_cashier 提交申请
    try:
        db.execute(
            text("""INSERT INTO refund_requests 
                    (original_transaction_id, requester_id, booth_id, reason, status, created_at)
                    VALUES (:tid, :uid, :bid, :reason, 'pending', NOW())"""),
            {
                "tid": req.original_transaction_id,
                "uid": current_user.id,
                "bid": current_user.booth_id,
                "reason": req.reason,
            }
        )
        db.commit()

        logger.info(
            f"Refund request created: txn_id={req.original_transaction_id}, "
            f"requester={current_user.username}, reason={req.reason}"
        )

        return {
            "success": True,
            "status": "pending",
            "message": "退款申请已提交，等待管理员审批",
        }

    except Exception as e:
        db.rollback()
        # 如果表不存在，创建它
        if "refund_requests" in str(e).lower() and "exist" in str(e).lower():
            _ensure_table(db)
            return await create_refund_request(req, current_user, db)
        logger.error(f"Create refund request failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GET /refund/requests - 查看退款申请列表
# ============================================================================

@router.get("/requests")
async def get_refund_requests(
    status_filter: Optional[str] = Query(None, description="状态过滤: pending/approved/rejected"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    查看退款申请列表。

    - super_admin / event_admin: 查看所有申请
    - booth_cashier: 只能查看自己提交的申请
    """
    try:
        where_clauses = []
        params = {"limit": limit, "offset": offset}

        if current_user.role == "booth_cashier":
            where_clauses.append("rr.requester_id = :uid")
            params["uid"] = current_user.id

        if status_filter:
            where_clauses.append("rr.status = :status")
            params["status"] = status_filter

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        rows = db.execute(
            text(f"""SELECT rr.*, 
                        t.amount as txn_amount, t.card_uid, t.participant_id,
                        t.booth_id as txn_booth_id, t.created_at as txn_time,
                        u.username as requester_name,
                        au.username as approver_name
                    FROM refund_requests rr
                    LEFT JOIN transactions t ON rr.original_transaction_id = t.id
                    LEFT JOIN users u ON rr.requester_id = u.id
                    LEFT JOIN users au ON rr.approver_id = au.id
                    WHERE {where_sql}
                    ORDER BY rr.created_at DESC
                    LIMIT :limit OFFSET :offset"""),
            params
        ).mappings().all()

        count_result = db.execute(
            text(f"""SELECT COUNT(*) as cnt FROM refund_requests rr WHERE {where_sql}"""),
            params
        ).mappings().first()

        requests = []
        for row in rows:
            requests.append({
                "id": row["id"],
                "original_transaction_id": row["original_transaction_id"],
                "requester_id": row["requester_id"],
                "requester_name": row["requester_name"],
                "booth_id": row["booth_id"],
                "reason": row["reason"],
                "status": row["status"],
                "approver_name": row["approver_name"],
                "approve_remark": row.get("approve_remark"),
                "txn_amount": float(row["txn_amount"]) if row["txn_amount"] else 0,
                "card_uid": row["card_uid"],
                "txn_time": row["txn_time"].isoformat() if row["txn_time"] else None,
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "approved_at": row["approved_at"].isoformat() if row.get("approved_at") else None,
            })

        return {
            "requests": requests,
            "total_count": count_result["cnt"] if count_result else 0,
        }

    except Exception as e:
        if "refund_requests" in str(e).lower():
            _ensure_table(db)
            return {"requests": [], "total_count": 0}
        logger.error(f"Get refund requests failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# POST /refund/requests/{id}/approve - 管理员审批通过
# ============================================================================

@router.post("/requests/{request_id}/approve")
async def approve_refund_request(
    request_id: int,
    body: RefundRequestApprove = RefundRequestApprove(),
    current_user=Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db),
):
    """管理员审批通过退款申请，自动执行退款。"""
    # 查询申请
    row = db.execute(
        text("SELECT * FROM refund_requests WHERE id = :id AND status = 'pending'"),
        {"id": request_id}
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="退款申请不存在或已处理")

    # 查询原交易
    original_txn = db.query(Transaction).filter(
        Transaction.id == row["original_transaction_id"]
    ).first()

    if not original_txn:
        raise HTTPException(status_code=404, detail="原交易流水不存在")

    # 执行退款
    result = await _execute_refund(db, original_txn, current_user, row["reason"])

    # 更新申请状态
    db.execute(
        text("""UPDATE refund_requests 
                SET status = 'approved', approver_id = :aid, approve_remark = :remark, approved_at = NOW()
                WHERE id = :id"""),
        {"id": request_id, "aid": current_user.id, "remark": body.remark}
    )
    db.commit()

    logger.info(f"Refund request {request_id} approved by {current_user.username}")

    return {
        "success": True,
        "message": "退款申请已通过，退款已执行",
        "refund_result": result,
    }


# ============================================================================
# POST /refund/requests/{id}/reject - 管理员驳回
# ============================================================================

@router.post("/requests/{request_id}/reject")
async def reject_refund_request(
    request_id: int,
    body: RefundRequestApprove = RefundRequestApprove(),
    current_user=Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db),
):
    """管理员驳回退款申请。"""
    result = db.execute(
        text("""UPDATE refund_requests 
                SET status = 'rejected', approver_id = :aid, approve_remark = :remark, approved_at = NOW()
                WHERE id = :id AND status = 'pending'"""),
        {"id": request_id, "aid": current_user.id, "remark": body.remark}
    )
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="退款申请不存在或已处理")

    logger.info(f"Refund request {request_id} rejected by {current_user.username}")

    return {"success": True, "message": "退款申请已驳回"}


# ============================================================================
# Helper: 执行退款
# ============================================================================

async def _execute_refund(db: Session, original_txn: Transaction, operator, reason: str):
    """执行退款逻辑（与 trade/refund 相同）"""
    # 检查重复退款
    existing = db.query(Transaction).filter(
        Transaction.related_txn_id == original_txn.id,
        Transaction.type == "refund"
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该交易已退款")

    # 锁定账户
    locked_account = db.query(Account).filter(
        Account.id == original_txn.account_id
    ).with_for_update().first()

    if not locked_account:
        raise HTTPException(status_code=404, detail="账户不存在")

    refund_amount = original_txn.amount
    balance_before = locked_account.balance
    balance_after = float(balance_before) + float(refund_amount)

    # 创建退款流水
    refund_txn = Transaction(
        uid=original_txn.uid,
        card_uid=original_txn.card_uid,
        event_id=original_txn.event_id,
        participant_id=original_txn.participant_id,
        account_id=original_txn.account_id,
        type="refund",
        amount=refund_amount,
        balance_before=balance_before,
        balance_after=balance_after,
        merchant_id=original_txn.merchant_id,
        related_txn_id=original_txn.id,
        remark=f"退款原因: {reason}",
        operator_id=str(operator.id),
    )
    if hasattr(refund_txn, 'booth_id'):
        refund_txn.booth_id = original_txn.booth_id if hasattr(original_txn, 'booth_id') else None

    db.add(refund_txn)

    # 更新余额
    locked_account.balance = balance_after

    db.commit()
    db.refresh(refund_txn)

    return {
        "success": True,
        "refund_transaction_id": refund_txn.id,
        "refunded_amount": float(refund_amount),
        "new_balance": float(balance_after),
        "balance_before": float(balance_before),
    }


# ============================================================================
# Helper: 确保表存在
# ============================================================================

def _ensure_table(db: Session):
    """创建 refund_requests 表（如果不存在）"""
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS refund_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                original_transaction_id INT NOT NULL,
                requester_id INT NOT NULL,
                booth_id INT DEFAULT NULL,
                reason VARCHAR(500) NOT NULL,
                status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
                approver_id INT DEFAULT NULL,
                approve_remark VARCHAR(255) DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP NULL DEFAULT NULL,
                INDEX idx_refund_req_status (status),
                INDEX idx_refund_req_requester (requester_id),
                INDEX idx_refund_req_txn (original_transaction_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='退款申请表'
        """))
        db.commit()
        logger.info("Created refund_requests table")
    except Exception as e:
        logger.error(f"Failed to create refund_requests table: {e}")
