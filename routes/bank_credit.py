"""
官方银行信用垫资 API (ORM + 悲观锁版)

Business Rules:
  - 名义借款 N 元，手续费 5%，实际到账 N * 0.95
  - 账本精确记录：本金(loan_issue)、手续费(loan_fee)、实际到账余额变动
  - 使用 SELECT ... FOR UPDATE 悲观锁保证并发安全
  - 完整审计日志

核心接口: POST /api/bank/issue_loan
  入参: event_id, card_uid (NFC读取), nominal_amount (名义借款金额，单位：分)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import math
import csv
import io
import logging

from core.database import get_db
from core.security import get_current_user, RoleChecker
from models.account import Account
from models.participant import Participant
from models.transaction import Transaction
from models.event import Event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bank", tags=["Bank Credit"])

# Legacy router for backward compatibility with web-admin frontend
legacy_router = APIRouter(prefix="/api/bank-credit", tags=["Bank Credit (Legacy)"])


# ============================================================================
# Constants
# ============================================================================

# 单人借款上限（分），默认 200 元 = 20000 分
DEFAULT_MAX_PER_PERSON = 20000
# 全场信贷总额上限（分），默认 10000 元
DEFAULT_MAX_TOTAL_CREDIT = 1000000
# 默认手续费率
DEFAULT_FEE_RATE = 0.05


# ============================================================================
# Schemas
# ============================================================================

class IssueLoanRequest(BaseModel):
    """放贷请求"""
    event_id: int = Field(..., description="活动ID")
    card_uid: str = Field(..., min_length=1, max_length=32, description="NFC卡片UID")
    nominal_amount: Optional[float] = Field(None, description="名义借款金额（元）")
    principal_amount: Optional[float] = Field(None, description="名义借款金额 - 兼容安卓端字段名（元）")
    deposit_card_fee: Optional[float] = Field(None, description="专用消费卡押金（元），从借款中扣除")
    remark: Optional[str] = Field(None, max_length=255, description="备注（如借条编号）")
    # 允许安卓端发送的额外字段（timestamp, signature）
    timestamp: Optional[int] = Field(None, exclude=True)
    signature: Optional[str] = Field(None, exclude=True)

    class Config:
        extra = "allow"


class IssueLoanResponse(BaseModel):
    """放贷响应"""
    success: bool
    loan_id: int
    event_id: int
    participant_id: int
    participant_name: str
    card_uid: str
    nominal_amount: float
    nominal_amount_yuan: float
    fee_rate: float
    fee_amount: float
    fee_amount_yuan: float
    actual_grant: float
    actual_grant_yuan: float
    balance_before: float
    balance_before_yuan: float
    balance_after: float
    balance_after_yuan: float
    credit_borrowed_total: float
    credit_borrowed_total_yuan: float
    credit_fee_paid_total: float
    credit_fee_paid_total_yuan: float
    loan_issue_txn_id: int
    loan_fee_txn_id: int
    operator_name: str
    created_at: str
    # 兼容安卓端字段名
    disbursed_amount: Optional[float] = None
    new_balance: Optional[float] = None
    principal_amount: Optional[float] = None
    message: Optional[str] = None


class LoanRecord(BaseModel):
    """贷款记录"""
    id: int
    event_id: int
    participant_id: int
    participant_name: Optional[str] = None
    class_name: Optional[str] = None
    student_no: Optional[str] = None
    card_uid: Optional[str] = None
    operator_name: Optional[str] = None
    principal_amount: int
    principal_amount_yuan: float
    fee_rate: float
    fee_amount: int
    fee_amount_yuan: float
    disbursed_amount: int
    disbursed_amount_yuan: float
    status: str
    remark: Optional[str] = None
    created_at: str


class CreditDashboardStats(BaseModel):
    """央行宏观风控看板数据"""
    total_principal: int
    total_principal_yuan: float
    total_fee: int
    total_fee_yuan: float
    total_disbursed: int
    total_disbursed_yuan: float
    total_loans: int
    total_borrowers: int
    total_participants: int
    penetration_rate: float
    credit_limit: int
    credit_limit_yuan: float
    credit_utilization: float
    avg_loan_amount: float
    avg_loan_amount_yuan: float
    class_distribution: List[dict]
    lending_trend: List[dict]
    top_debtors: List[dict]


class CreditConfig(BaseModel):
    """信贷配置"""
    max_total_credit: int = DEFAULT_MAX_TOTAL_CREDIT
    max_per_person: int = DEFAULT_MAX_PER_PERSON
    fee_rate: float = DEFAULT_FEE_RATE
    is_enabled: bool = True


# ============================================================================
# Helper Functions
# ============================================================================

def _get_credit_config(db: Session, event_id: int) -> dict:
    """获取信贷配置，如果表不存在或无记录则返回默认值"""
    try:
        config_row = db.execute(
            text("SELECT * FROM bank_credit_config WHERE event_id = :eid"),
            {"eid": event_id}
        ).mappings().first()

        if config_row:
            return {
                "fee_rate": float(config_row["fee_rate"]),
                "max_total_credit": config_row["max_total_credit"],
                "max_per_person": config_row["max_per_person"],
                "is_enabled": bool(config_row["is_enabled"]),
            }
    except Exception:
        # 表不存在或查询失败，使用默认值
        pass

    return {
        "fee_rate": DEFAULT_FEE_RATE,
        "max_total_credit": DEFAULT_MAX_TOTAL_CREDIT,
        "max_per_person": DEFAULT_MAX_PER_PERSON,
        "is_enabled": True,
    }


def _write_audit_log(
    db: Session,
    event_id: int,
    operator_id: int,
    action: str,
    detail: str
):
    """写入审计日志（如果 audit_logs 表存在）"""
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
        # audit_logs 表可能不存在，静默忽略
        logger.debug("audit_logs table not available, skipping audit log")


# ============================================================================
# Core Endpoint: POST /api/bank/issue_loan
# ============================================================================

@router.post("/issue_loan", response_model=IssueLoanResponse)
async def issue_loan(
    req: IssueLoanRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    发放官方银行信用垫资（核心接口）

    业务流程：
      1. 校验操作员权限（bank_clerk / super_admin）
      2. 通过 card_uid 查找参与者
      3. 获取或创建活动账户
      4. 校验单人借款额度上限（如 200 元）
      5. 计算：fee_amount = nominal_amount * 0.05, actual_grant = nominal_amount - fee_amount
      6. 使用悲观锁(SELECT ... FOR UPDATE) 锁定账户行
      7. 写入流水表：loan_issue (+nominal_amount), loan_fee (-fee_amount)
      8. 更新账户：balance += actual_grant, credit_borrowed += nominal_amount, credit_fee_paid += fee_amount
      9. 写入 bank_loans 记录
      10. 记录审计日志
    """
    # ── 1. 权限校验 ──
    if current_user.role not in ("bank_clerk", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅银行柜员(bank_clerk)或超级管理员可执行放贷操作"
        )

    # ── 1.5 解析金额（兼容 nominal_amount 和 principal_amount 两种字段名） ──
    nominal_amount = req.nominal_amount or req.principal_amount
    logger.info(f"[LOAN_REQUEST] card_uid={req.card_uid}, nominal_amount={req.nominal_amount}, principal_amount={req.principal_amount}, resolved={nominal_amount}")
    if not nominal_amount or nominal_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="借款金额必须大于0"
        )

    try:
        # ── 2. 验证活动存在 ──
        event = db.query(Event).filter(Event.id == req.event_id).first()
        if event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"活动 {req.event_id} 不存在"
            )

        # ── 3. 通过 card_uid 查找参与者 ──
        participant = db.query(Participant).filter(
            Participant.card_uid == req.card_uid
        ).first()
        if participant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到 NFC 卡 UID={req.card_uid} 对应的参与者"
            )
        if participant.status != 'active':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"参与者 {participant.name} 状态异常({participant.status})，无法借款"
            )

        # ── 实名认证校验（已取消，输入后直接可用） ──
        # if not participant.is_verified:
        #     raise HTTPException(...)

        # ── 4. 获取信贷配置 ──
        config = _get_credit_config(db, req.event_id)
        if not config["is_enabled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前活动信贷功能已关闭"
            )
        fee_rate = config["fee_rate"]
        max_per_person = config["max_per_person"]
        max_total = config["max_total_credit"]

        # ── 5. 获取或创建账户 ──
        account = db.query(Account).filter(
            Account.participant_id == participant.id,
            Account.event_id == req.event_id
        ).first()
        if account is None:
            account = Account(
                participant_id=participant.id,
                event_id=req.event_id,
                balance=0,
                credit_borrowed=0,
                credit_fee_paid=0
            )
            db.add(account)
            db.flush()  # 获取 account.id

        # ── 6. 校验单人借款额度（已取消限制，允许任意金额） ──
        existing_borrowed = db.execute(
            text("""SELECT COALESCE(SUM(principal_amount), 0) as total
                    FROM bank_loans
                    WHERE participant_id = :pid AND event_id = :eid AND status = 'active'"""),
            {"pid": participant.id, "eid": req.event_id}
        ).mappings().first()["total"]

        # 不再限制单人借款上限
        # if existing_borrowed + req.nominal_amount > max_per_person:
        #     raise HTTPException(...)

        # ── 7. 校验全场总额度（已取消限制） ──
        global_borrowed = db.execute(
            text("""SELECT COALESCE(SUM(principal_amount), 0) as total
                    FROM bank_loans
                    WHERE event_id = :eid AND status = 'active'"""),
            {"eid": req.event_id}
        ).mappings().first()["total"]

        # 不再限制全场总额度
        # if global_borrowed + req.nominal_amount > max_total:
        #     raise HTTPException(...)

        # ── 8. 计算手续费和实际到账（金额单位：元） ──
        from decimal import Decimal, ROUND_HALF_UP
        nominal_amount = Decimal(str(nominal_amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        fee_amount = (nominal_amount * Decimal(str(fee_rate))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # 专用消费卡押金
        deposit_card_fee = Decimal('0')
        if req.deposit_card_fee and req.deposit_card_fee > 0:
            deposit_card_fee = Decimal(str(req.deposit_card_fee)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        actual_grant = nominal_amount - fee_amount - deposit_card_fee

        # ── 9. 悲观锁锁定账户行 (SELECT ... FOR UPDATE) ──
        locked_account = db.query(Account).filter(
            Account.id == account.id
        ).with_for_update().first()

        if locked_account is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="账户锁定失败"
            )

        balance_before = locked_account.balance

        # ── 10. 写入流水表 ──
        # 10a. loan_issue 流水：记录名义本金入账(+nominal_amount)
        txn_loan_issue = Transaction(
            uid=None,
            card_uid=req.card_uid,
            event_id=req.event_id,
            participant_id=participant.id,
            account_id=locked_account.id,
            type="loan_issue",
            amount=nominal_amount,
            balance_before=balance_before,
            balance_after=balance_before + nominal_amount,
            merchant_id=None,
            remark=f"银行垫资发放：名义本金 {nominal_amount:.2f} 元",
            operator_id=str(current_user.id)
        )
        db.add(txn_loan_issue)
        db.flush()

        # 10b. loan_fee 流水：记录手续费扣除 (-fee_amount)
        balance_after_issue = balance_before + nominal_amount
        txn_loan_fee = Transaction(
            uid=None,
            card_uid=req.card_uid,
            event_id=req.event_id,
            participant_id=participant.id,
            account_id=locked_account.id,
            type="loan_fee",
            amount=fee_amount,
            balance_before=balance_after_issue,
            balance_after=balance_after_issue - fee_amount,
            merchant_id=None,
            remark=f"银行垫资手续费：{fee_rate*100:.1f}% = {fee_amount:.2f} 元",
            operator_id=str(current_user.id)
        )
        db.add(txn_loan_fee)
        db.flush()

        # ── 11. 更新账户余额 ──
        balance_after = balance_before + actual_grant
        locked_account.balance = balance_after
        locked_account.credit_borrowed = locked_account.credit_borrowed + nominal_amount
        locked_account.credit_fee_paid = locked_account.credit_fee_paid + fee_amount

        # ── 12. 写入 bank_loans 记录 ──
        db.execute(
            text("""INSERT INTO bank_loans
                    (event_id, participant_id, operator_id, principal_amount,
                     fee_rate, fee_amount, disbursed_amount, remark, status)
                    VALUES (:eid, :pid, :oid, :principal, :rate, :fee, :disbursed, :remark, 'active')"""),
            {
                "eid": req.event_id,
                "pid": participant.id,
                "oid": current_user.id,
                "principal": nominal_amount,
                "rate": fee_rate,
                "fee": fee_amount,
                "disbursed": actual_grant,
                "remark": req.remark,
            }
        )

        # 获取新插入的 loan ID
        loan_id_row = db.execute(text("SELECT LAST_INSERT_ID() as id")).mappings().first()
        loan_id = loan_id_row["id"]

        # ── 13. 审计日志 ──
        deposit_info = f", 消费卡押金={deposit_card_fee:.2f}元" if deposit_card_fee > 0 else ""
        audit_detail = (
            f"放贷成功: participant={participant.name}(card={req.card_uid}), "
            f"本金={nominal_amount:.2f}元, 手续费={fee_amount:.2f}元{deposit_info}, "
            f"实际到账={actual_grant:.2f}元, "
            f"余额: {float(balance_before):.2f} -> {float(balance_after):.2f}元"
        )
        _write_audit_log(
            db=db,
            event_id=req.event_id,
            operator_id=current_user.id,
            action="bank_loan_issue",
            detail=audit_detail
        )

        # ── 14. 提交事务 ──
        db.commit()

        logger.info(
            f"[LOAN_ISSUED] event={req.event_id}, participant={participant.name}, "
            f"card_uid={req.card_uid}, nominal={nominal_amount}, "
            f"fee={fee_amount}, actual={actual_grant}, "
            f"balance: {balance_before} -> {balance_after}, "
            f"operator={current_user.username}"
        )

        return IssueLoanResponse(
            success=True,
            loan_id=loan_id,
            event_id=req.event_id,
            participant_id=participant.id,
            participant_name=participant.name,
            card_uid=req.card_uid,
            nominal_amount=nominal_amount,
            nominal_amount_yuan=float(nominal_amount),
            fee_rate=fee_rate,
            fee_amount=fee_amount,
            fee_amount_yuan=float(fee_amount),
            actual_grant=actual_grant,
            actual_grant_yuan=float(actual_grant),
            balance_before=balance_before,
            balance_before_yuan=float(balance_before),
            balance_after=balance_after,
            balance_after_yuan=float(balance_after),
            credit_borrowed_total=locked_account.credit_borrowed,
            credit_borrowed_total_yuan=float(locked_account.credit_borrowed),
            credit_fee_paid_total=locked_account.credit_fee_paid,
            credit_fee_paid_total_yuan=float(locked_account.credit_fee_paid),
            loan_issue_txn_id=txn_loan_issue.id,
            loan_fee_txn_id=txn_loan_fee.id,
            operator_name=current_user.username,
            created_at=datetime.now(timezone.utc).isoformat(),
            # 兼容安卓端
            disbursed_amount=float(actual_grant),
            new_balance=float(balance_after),
            principal_amount=nominal_amount,
            message=f"放贷成功：实际到账 {actual_grant} 元"
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[LOAN_FAILED] card_uid={req.card_uid}, error={e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"放贷操作失败: {str(e)}"
        )


# ============================================================================
# Legacy Compatibility: POST /api/bank/credit/loan (participant_id based)
# ============================================================================

class LegacyLoanRequest(BaseModel):
    """兼容旧版放贷请求（使用 participant_id）"""
    event_id: int
    participant_id: int
    principal_amount: int = Field(..., gt=0, description="名义借款金额（分）")
    remark: Optional[str] = None


@router.post("/credit/loan", response_model=IssueLoanResponse)
async def create_loan_legacy(
    req: LegacyLoanRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    兼容旧版放贷接口（通过 participant_id）。
    内部转换为 card_uid 调用核心逻辑。
    """
    if current_user.role not in ("bank_clerk", "super_admin"):
        raise HTTPException(status_code=403, detail="仅银行柜员或超级管理员可操作")

    # 通过 participant_id 查找 card_uid
    participant = db.query(Participant).filter(
        Participant.id == req.participant_id
    ).first()
    if participant is None:
        raise HTTPException(status_code=404, detail=f"参与者 ID={req.participant_id} 不存在")

    # 转发到核心接口
    core_req = IssueLoanRequest(
        event_id=req.event_id,
        card_uid=participant.card_uid,
        nominal_amount=req.principal_amount,
        remark=req.remark
    )
    return await issue_loan(core_req, current_user, db)


# ============================================================================
# Dashboard: GET /api/bank/dashboard/{event_id}
# ============================================================================

@router.get("/dashboard/{event_id}", response_model=CreditDashboardStats)
async def get_credit_dashboard(
    event_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """央行宏观经济与信用风险看板数据"""
    if current_user.role not in ("bank_clerk", "super_admin", "event_admin"):
        raise HTTPException(status_code=403, detail="权限不足")

    # 核心指标
    stats = db.execute(
        text("""SELECT
            COALESCE(SUM(principal_amount), 0) as total_principal,
            COALESCE(SUM(fee_amount), 0) as total_fee,
            COALESCE(SUM(disbursed_amount), 0) as total_disbursed,
            COUNT(*) as total_loans,
            COUNT(DISTINCT participant_id) as total_borrowers,
            COALESCE(AVG(principal_amount), 0) as avg_loan
           FROM bank_loans
           WHERE event_id = :eid AND status = 'active'"""),
        {"eid": event_id}
    ).mappings().first()

    # 活动总参与人数
    total_participants_row = db.execute(
        text("SELECT COUNT(*) as total FROM accounts WHERE event_id = :eid"),
        {"eid": event_id}
    ).mappings().first()
    total_participants = total_participants_row["total"]

    # 信贷配置
    config = _get_credit_config(db, event_id)
    credit_limit = config["max_total_credit"]

    # 按班级分布
    class_rows = db.execute(
        text("""SELECT
            COALESCE(p.class_name, '未知班级') as class_name,
            SUM(l.principal_amount) as total_amount,
            COUNT(*) as loan_count,
            COUNT(DISTINCT l.participant_id) as borrower_count
           FROM bank_loans l
           JOIN participants p ON l.participant_id = p.id
           WHERE l.event_id = :eid AND l.status = 'active'
           GROUP BY p.class_name
           ORDER BY total_amount DESC"""),
        {"eid": event_id}
    ).mappings().all()

    class_distribution = [
        {
            "class_name": row["class_name"],
            "total_amount": row["total_amount"],
            "total_amount_yuan": row["total_amount"] / 1,
            "loan_count": row["loan_count"],
            "borrower_count": row["borrower_count"]
        }
        for row in class_rows
    ]

    # 放贷趋势（按分钟聚合）
    trend_rows = db.execute(
        text("""SELECT
            DATE_FORMAT(created_at, '%H:%i') as time_slot,
            SUM(principal_amount) as amount,
            COUNT(*) as count
           FROM bank_loans
           WHERE event_id = :eid AND status = 'active'
           GROUP BY time_slot
           ORDER BY time_slot"""),
        {"eid": event_id}
    ).mappings().all()

    lending_trend = [
        {
            "time": row["time_slot"],
            "amount": row["amount"],
            "amount_yuan": row["amount"] / 1,
            "count": row["count"]
        }
        for row in trend_rows
    ]

    # 大额债务人列表(TOP 100)
    debtor_rows = db.execute(
        text("""SELECT
            p.class_name,
            p.student_no,
            CASE WHEN (p.class_name IS NOT NULL AND p.class_name != '') OR (p.student_no IS NOT NULL AND p.student_no != '')
                 THEN p.name ELSE p.card_uid END as participant_name,
            p.card_uid,
            SUM(l.principal_amount) as total_principal,
            SUM(l.fee_amount) as total_fee,
            SUM(l.disbursed_amount) as total_disbursed,
            u.username as operator_name,
            MAX(l.created_at) as last_loan_time,
            COUNT(*) as loan_count
           FROM bank_loans l
           JOIN participants p ON l.participant_id = p.id
           JOIN users u ON l.operator_id = u.id
           WHERE l.event_id = :eid AND l.status = 'active'
           GROUP BY l.participant_id, p.class_name, p.student_no, p.name, p.card_uid, u.username
           ORDER BY total_principal DESC
           LIMIT 100"""),
        {"eid": event_id}
    ).mappings().all()

    top_debtors = [
        {
            "class_name": row["class_name"] or "未知",
            "student_no": row["student_no"] or "未知",
            "participant_name": row["participant_name"],
            "card_uid": row["card_uid"],
            "total_principal": row["total_principal"],
            "total_principal_yuan": row["total_principal"] / 1,
            "total_fee": row["total_fee"],
            "total_fee_yuan": row["total_fee"] / 1,
            "total_disbursed": row["total_disbursed"],
            "total_disbursed_yuan": row["total_disbursed"] / 1,
            "operator_name": row["operator_name"],
            "last_loan_time": row["last_loan_time"].isoformat() if row["last_loan_time"] else None,
            "loan_count": row["loan_count"]
        }
        for row in debtor_rows
    ]

    total_principal = stats["total_principal"]
    penetration_rate = (
        stats["total_borrowers"] / total_participants * 100
    ) if total_participants > 0 else 0
    credit_utilization = (
        total_principal / credit_limit * 100
    ) if credit_limit > 0 else 0

    return CreditDashboardStats(
        total_principal=total_principal,
        total_principal_yuan=total_principal / 1,
        total_fee=stats["total_fee"],
        total_fee_yuan=stats["total_fee"] / 1,
        total_disbursed=stats["total_disbursed"],
        total_disbursed_yuan=stats["total_disbursed"] / 1,
        total_loans=stats["total_loans"],
        total_borrowers=stats["total_borrowers"],
        total_participants=total_participants,
        penetration_rate=round(penetration_rate, 2),
        credit_limit=credit_limit,
        credit_limit_yuan=credit_limit / 1,
        credit_utilization=round(credit_utilization, 2),
        avg_loan_amount=float(stats["avg_loan"]),
        avg_loan_amount_yuan=float(stats["avg_loan"]) / 1,
        class_distribution=class_distribution,
        lending_trend=lending_trend,
        top_debtors=top_debtors
    )


# ============================================================================
# Loans List: GET /api/bank/loans/{event_id}
# ============================================================================

@router.get("/loans/{event_id}", response_model=List[LoanRecord])
async def get_loans(
    event_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    class_name: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取贷款列表"""
    if current_user.role not in ("bank_clerk", "super_admin", "event_admin"):
        raise HTTPException(status_code=403, detail="权限不足")

    query = """
        SELECT l.*,
               CASE WHEN (p.class_name IS NOT NULL AND p.class_name != '') OR (p.student_no IS NOT NULL AND p.student_no != '')
                    THEN p.name ELSE p.card_uid END as participant_name,
               p.class_name, p.student_no, p.card_uid,
               u.username as operator_name
        FROM bank_loans l
        JOIN participants p ON l.participant_id = p.id
        JOIN users u ON l.operator_id = u.id
        WHERE l.event_id = :eid
    """
    params: dict = {"eid": event_id}

    if status_filter:
        query += " AND l.status = :status"
        params["status"] = status_filter
    if class_name:
        query += " AND p.class_name = :class_name"
        params["class_name"] = class_name

    query += " ORDER BY l.created_at DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset

    rows = db.execute(text(query), params).mappings().all()

    return [
        LoanRecord(
            id=row["id"],
            event_id=row["event_id"],
            participant_id=row["participant_id"],
            participant_name=row["participant_name"],
            class_name=row["class_name"],
            student_no=row["student_no"],
            card_uid=row["card_uid"],
            operator_name=row["operator_name"],
            principal_amount=row["principal_amount"],
            principal_amount_yuan=row["principal_amount"] / 1,
            fee_rate=float(row["fee_rate"]),
            fee_amount=row["fee_amount"],
            fee_amount_yuan=row["fee_amount"] / 1,
            disbursed_amount=row["disbursed_amount"],
            disbursed_amount_yuan=row["disbursed_amount"] / 1,
            status=row["status"],
            remark=row["remark"],
            created_at=row["created_at"].isoformat() if row["created_at"] else ""
        )
        for row in rows
    ]


# ============================================================================
# Export: GET /api/bank/export/{event_id}
# ============================================================================

@router.get("/export/{event_id}")
async def export_loans_csv(
    event_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导出全场对账单 CSV"""
    if current_user.role not in ("bank_clerk", "super_admin", "event_admin"):
        raise HTTPException(status_code=403, detail="权限不足")

    rows = db.execute(
        text("""SELECT l.*,
                       CASE WHEN (p.class_name IS NOT NULL AND p.class_name != '') OR (p.student_no IS NOT NULL AND p.student_no != '')
                            THEN p.name ELSE p.card_uid END as participant_name,
                       p.class_name, p.student_no, p.card_uid,
                       u.username as operator_name
               FROM bank_loans l
               JOIN participants p ON l.participant_id = p.id
               JOIN users u ON l.operator_id = u.id
               WHERE l.event_id = :eid
               ORDER BY l.principal_amount DESC"""),
        {"eid": event_id}
    ).mappings().all()

    output = io.StringIO()
    output.write('\ufeff')  # BOM for Excel compatibility
    writer = csv.writer(output)
    writer.writerow([
        "序号", "班级", "学号", "姓名", "NFC卡号", "名义借款(元)", "手续费(元)",
        "实际到账(元)", "手续费率", "状态", "放贷操作员", "放贷时间", "备注"
    ])

    status_map = {"active": "未还", "repaid": "已还", "written_off": "核销"}

    for idx, row in enumerate(rows, 1):
        writer.writerow([
            idx,
            row["class_name"] or "未知",
            row["student_no"] or "未知",
            row["participant_name"],
            row["card_uid"],
            f"{row['principal_amount'] / 1:.2f}",
            f"{row['fee_amount'] / 1:.2f}",
            f"{row['disbursed_amount'] / 1:.2f}",
            f"{float(row['fee_rate']) * 100:.1f}%",
            status_map.get(row["status"], row["status"]),
            row["operator_name"],
            row["created_at"].strftime("%Y-%m-%d %H:%M:%S") if row["created_at"] else "",
            row["remark"] or ""
        ])

    output.seek(0)
    content = output.getvalue()

    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=bank_credit_report_event_{event_id}.csv"
        }
    )


# ============================================================================
# Config: GET/PUT /api/bank/config/{event_id}
# ============================================================================

@router.get("/config/{event_id}")
async def get_credit_config_endpoint(
    event_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取信贷配置"""
    config = _get_credit_config(db, event_id)
    return {
        "event_id": event_id,
        "max_total_credit": config["max_total_credit"],
        "max_total_credit_yuan": config["max_total_credit"] / 1,
        "max_per_person": config["max_per_person"],
        "max_per_person_yuan": config["max_per_person"] / 1,
        "fee_rate": config["fee_rate"],
        "is_enabled": config["is_enabled"]
    }


@router.put("/config/{event_id}")
async def update_credit_config(
    event_id: int,
    config: CreditConfig,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新信贷配置（仅 super_admin）"""
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="仅超级管理员可修改信贷配置")

    db.execute(
        text("""INSERT INTO bank_credit_config (event_id, max_total_credit, max_per_person, fee_rate, is_enabled)
               VALUES (:eid, :max_total, :max_person, :rate, :enabled)
               ON DUPLICATE KEY UPDATE
               max_total_credit = VALUES(max_total_credit),
               max_per_person = VALUES(max_per_person),
               fee_rate = VALUES(fee_rate),
               is_enabled = VALUES(is_enabled)"""),
        {
            "eid": event_id,
            "max_total": config.max_total_credit,
            "max_person": config.max_per_person,
            "rate": config.fee_rate,
            "enabled": config.is_enabled
        }
    )
    db.commit()

    _write_audit_log(
        db=db,
        event_id=event_id,
        operator_id=current_user.id,
        action="bank_config_update",
        detail=f"信贷配置更新: max_total={config.max_total_credit}, max_person={config.max_per_person}, fee_rate={config.fee_rate}"
    )

    return {"message": "配置更新成功", "config": config.dict()}


# ============================================================================
# Account Credit Summary: GET /api/bank/account_credit/{event_id}/{card_uid}
# ============================================================================

@router.get("/account_credit/{event_id}/{card_uid}")
async def get_account_credit_summary(
    event_id: int,
    card_uid: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """查询指定参与者的信贷账户汇总（通过 NFC 卡号）"""
    participant = db.query(Participant).filter(
        Participant.card_uid == card_uid
    ).first()
    if participant is None:
        raise HTTPException(status_code=404, detail=f"未找到卡号 {card_uid} 对应的参与者")

    account = db.query(Account).filter(
        Account.participant_id == participant.id,
        Account.event_id == event_id
    ).first()

    if account is None:
        return {
            "participant_name": participant.display_name,
            "card_uid": card_uid,
            "balance": 0,
            "balance_yuan": 0.0,
            "credit_borrowed": 0,
            "credit_borrowed_yuan": 0.0,
            "credit_fee_paid": 0,
            "credit_fee_paid_yuan": 0.0,
            "loan_count": 0
        }

    # 查询贷款笔数
    loan_count_row = db.execute(
        text("""SELECT COUNT(*) as cnt FROM bank_loans
                WHERE participant_id = :pid AND event_id = :eid AND status = 'active'"""),
        {"pid": participant.id, "eid": event_id}
    ).mappings().first()

    return {
        "participant_name": participant.display_name,
        "card_uid": card_uid,
        "balance": account.balance,
        "balance_yuan": account.balance / 1,
        "credit_borrowed": account.credit_borrowed,
        "credit_borrowed_yuan": account.credit_borrowed / 1,
        "credit_fee_paid": account.credit_fee_paid,
        "credit_fee_paid_yuan": account.credit_fee_paid / 1,
        "loan_count": loan_count_row["cnt"]
    }


# ============================================================================
# Legacy Routes (backward compatibility with /api/bank-credit/ prefix)
# These mirror the main routes for the web-admin frontend
# ============================================================================

@legacy_router.post("/loan", response_model=IssueLoanResponse)
async def legacy_create_loan(
    req: LegacyLoanRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """兼容旧版放贷接口 (POST /api/bank-credit/loan)"""
    return await create_loan_legacy(req, current_user, db)


@legacy_router.get("/dashboard/{event_id}", response_model=CreditDashboardStats)
async def legacy_get_dashboard(
    event_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """兼容旧版看板接口 (GET /api/bank-credit/dashboard/{event_id})"""
    return await get_credit_dashboard(event_id, current_user, db)


@legacy_router.get("/loans/{event_id}", response_model=List[LoanRecord])
async def legacy_get_loans(
    event_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    class_name: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """兼容旧版贷款列表接口 (GET /api/bank-credit/loans/{event_id})"""
    return await get_loans(event_id, status_filter, class_name, limit, offset, current_user, db)


@legacy_router.get("/export/{event_id}")
async def legacy_export_csv(
    event_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """兼容旧版导出接口 (GET /api/bank-credit/export/{event_id})"""
    return await export_loans_csv(event_id, current_user, db)


@legacy_router.get("/config/{event_id}")
async def legacy_get_config(
    event_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """兼容旧版配置接口 (GET /api/bank-credit/config/{event_id})"""
    return await get_credit_config_endpoint(event_id, current_user, db)


@legacy_router.put("/config/{event_id}")
async def legacy_update_config(
    event_id: int,
    config: CreditConfig,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """兼容旧版配置更新接口 (PUT /api/bank-credit/config/{event_id})"""
    return await update_credit_config(event_id, config, current_user, db)
