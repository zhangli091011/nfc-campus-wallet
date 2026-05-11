"""
退款模块 API

POST /api/trade/refund
  - 查询原订单 pay 流水，验证状态
  - 悲观锁锁定账户
  - 插入 refund 流水
  - 更新 accounts.balance
  - 扣减 booths 累计营业额/利润
  - 记录 audit_logs
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from core.database import get_db
from core.security import get_current_user
from models.account import Account
from models.transaction import Transaction
from models.booth import Booth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trade", tags=["Trade"])


# ============================================================================
# Schemas
# ============================================================================

class RefundRequest(BaseModel):
    """退款请求"""
    original_transaction_id: int = Field(..., description="原支付流水ID")
    operator_id: Optional[int] = Field(None, description="操作员ID（可从JWT自动获取）")
    reason: str = Field(..., min_length=1, max_length=500, description="退款原因")


class RefundResponse(BaseModel):
    """退款响应"""
    success: bool
    refund_transaction_id: int
    original_transaction_id: int
    participant_id: Optional[int]
    participant_name: Optional[str]
    refund_amount: float
    refund_amount_yuan: float
    balance_before: float
    balance_before_yuan: float
    balance_after: float
    balance_after_yuan: float
    booth_id: Optional[int]
    booth_name: Optional[str]
    reason: str
    operator_name: str
    created_at: str
    # 兼容安卓端字段名
    refunded_amount: Optional[float] = None
    new_balance: Optional[float] = None


# ============================================================================
# Helper
# ============================================================================

def _write_audit_log(
    db: Session,
    event_id: Optional[int],
    operator_id: int,
    action: str,
    detail: str
):
    """写入审计日志"""
    try:
        db.execute(
            text("""INSERT INTO audit_logs (event_id, operator_id, action, detail, created_at)
                    VALUES (:eid, :oid, :action, :detail, NOW())"""),
            {
                "eid": event_id,
                "oid": operator_id,
                "action": action,
                "detail": detail,
            }
        )
    except Exception:
        logger.debug("audit_logs table not available, skipping audit log")


# ============================================================================
# POST /api/trade/refund
# ============================================================================

@router.post("/refund", response_model=RefundResponse)
async def process_refund(
    req: RefundRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    处理退款

    业务流程：
      1. 权限校验（super_admin / event_admin）
      2. 查询原订单 pay 流水，验证类型和状态
      3. 检查是否已退款（防止重复退款）
      4. 悲观锁锁定用户账户 (SELECT ... FOR UPDATE)
      5. 插入 refund 类型流水，金额为原订单金额
      6. 更新 accounts.balance（加回退款金额）
      7. 如果原订单关联了 booth，扣减该摊位的累计营业额
      8. 记录 audit_logs
    """
    # ── 1. 权限校验 ──
    allowed_roles = ("super_admin", "event_admin")
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"仅 {', '.join(allowed_roles)} 可执行退款操作"
        )

    try:
        # ── 2. 查询原订单流水 ──
        original_txn = db.query(Transaction).filter(
            Transaction.id == req.original_transaction_id
        ).first()

        if original_txn is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"原交易流水 ID={req.original_transaction_id} 不存在"
            )

        # 验证原订单类型必须是 pay（支付）
        if original_txn.type != "pay":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"仅支持对 pay 类型交易退款，当前类型为 '{original_txn.type}'"
            )

        # ── 3. 检查是否已退款（防止重复退款） ──
        existing_refund = db.query(Transaction).filter(
            Transaction.related_txn_id == req.original_transaction_id,
            Transaction.type == "refund"
        ).first()

        if existing_refund is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"该交易已退款（退款流水ID={existing_refund.id}），不可重复退款"
            )

        # 获取原订单关联的账户
        if original_txn.account_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="原交易未关联账户，无法退款"
            )

        # ── 4. 悲观锁锁定账户 (SELECT ... FOR UPDATE) ──
        locked_account = db.query(Account).filter(
            Account.id == original_txn.account_id
        ).with_for_update().first()

        if locked_account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"账户 ID={original_txn.account_id} 不存在"
            )

        # 退款金额 = 原订单金额（全额退款）
        refund_amount = original_txn.amount  # 单位：分
        balance_before = locked_account.balance

        # ── 5. 插入 refund 流水 ──
        balance_after = balance_before + refund_amount

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
            remark=f"退款原因: {req.reason}",
            operator_id=str(current_user.id),
            booth_id=original_txn.booth_id,
            product_id=original_txn.product_id,
            booth_operator_id=current_user.id,
        )
        db.add(refund_txn)
        db.flush()  # 获取 refund_txn.id

        # ── 6. 更新账户余额 ──
        locked_account.balance = balance_after

        # ── 7. 扣减摊位累计营业额（如果原订单关联了 booth） ──
        booth_name = None
        if original_txn.booth_id is not None:
            booth = db.query(Booth).filter(
                Booth.id == original_txn.booth_id
            ).first()
            if booth is not None:
                booth_name = booth.name
                # 注意：booths 表本身没有 revenue 字段（营业额通过 transactions 聚合计算）
                # 退款流水已经记录了 booth_id，报表服务会自动在聚合时扣减
                # 如果有 booth_stats 表则更新之
                try:
                    db.execute(
                        text("""UPDATE booth_stats 
                                SET total_revenue = total_revenue - :amount,
                                    total_transactions = total_transactions - 1
                                WHERE booth_id = :bid"""),
                        {"amount": refund_amount, "bid": original_txn.booth_id}
                    )
                except Exception:
                    # booth_stats 表可能不存在，静默忽略
                    # 报表服务通过聚合 transactions 表计算，refund 流水会自动被统计
                    logger.debug("booth_stats table not available, skipping stats update")

        # ── 8. 审计日志 ──
        participant_name = None
        if original_txn.participant_id:
            from models.participant import Participant
            participant = db.query(Participant).filter(
                Participant.id == original_txn.participant_id
            ).first()
            if participant:
                participant_name = participant.display_name

        audit_detail = (
            f"退款成功: txn_id={original_txn.id} -> refund_txn_id={refund_txn.id}, "
            f"金额={float(refund_amount):.2f}元, "
            f"参与者={participant_name or 'N/A'}(card={original_txn.card_uid}), "
            f"摊位={booth_name or 'N/A'}, "
            f"原因={req.reason}, "
            f"余额: {float(balance_before):.2f} -> {float(balance_after):.2f}元"
        )
        _write_audit_log(
            db=db,
            event_id=original_txn.event_id,
            operator_id=current_user.id,
            action="trade_refund",
            detail=audit_detail
        )

        # ── 9. 提交事务 ──
        db.commit()

        logger.info(
            f"[REFUND_SUCCESS] original_txn={original_txn.id}, "
            f"refund_txn={refund_txn.id}, amount={refund_amount}, "
            f"account={locked_account.id}, balance: {balance_before} -> {balance_after}, "
            f"booth={original_txn.booth_id}, operator={current_user.username}, "
            f"reason={req.reason}"
        )

        return RefundResponse(
            success=True,
            refund_transaction_id=refund_txn.id,
            original_transaction_id=original_txn.id,
            participant_id=original_txn.participant_id,
            participant_name=participant_name,
            refund_amount=refund_amount,
            refund_amount_yuan=float(refund_amount),
            balance_before=balance_before,
            balance_before_yuan=float(balance_before),
            balance_after=balance_after,
            balance_after_yuan=float(balance_after),
            booth_id=original_txn.booth_id,
            booth_name=booth_name,
            reason=req.reason,
            operator_name=current_user.username,
            created_at=datetime.now(timezone.utc).isoformat(),
            # 兼容安卓端
            refunded_amount=float(refund_amount),
            new_balance=float(balance_after),
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"[REFUND_FAILED] original_txn={req.original_transaction_id}, error={e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"退款操作失败: {str(e)}"
        )
