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


# ============================================================================
# 管理员操作：充值/扣款/发放贷款
# ============================================================================

from pydantic import BaseModel, Field
from models.account import Account as AccountModel
from models.transaction import Transaction
from sqlalchemy import text


class AdminAdjustBalanceRequest(BaseModel):
    """管理员调整余额请求"""
    event_id: int = Field(..., description="活动ID")
    participant_id: int = Field(..., description="参与者ID")
    amount: float = Field(..., description="金额（正数为充值，负数为扣除）")
    remark: str = Field("", max_length=255, description="备注说明")


class AdminIssueLoanRequest(BaseModel):
    """管理员发放贷款请求"""
    event_id: int = Field(..., description="活动ID")
    participant_id: int = Field(..., description="参与者ID")
    amount: float = Field(..., gt=0, description="贷款金额（元）")
    fee_rate: float = Field(0.05, ge=0, le=1, description="手续费率（默认5%）")
    remark: str = Field("", max_length=255, description="备注说明")


@router.post("/participants/adjust-balance")
async def admin_adjust_balance(
    req: AdminAdjustBalanceRequest,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    管理员调整参与者余额（充值或扣款）。

    - amount > 0: 充值（增加余额）
    - amount < 0: 扣款（减少余额）

    仅 super_admin 和 event_admin 可执行。
    """
    try:
        if req.amount == 0:
            return JSONResponse(status_code=400, content={"error_code": "VALIDATION_ERROR", "message": "金额不能为0"})

        # 查找参与者
        participant = db.query(Participant).filter(Participant.id == req.participant_id).first()
        if not participant:
            return JSONResponse(status_code=404, content={"error_code": "NOT_FOUND", "message": "参与者不存在"})

        # 获取或创建账户
        account = db.query(AccountModel).filter(
            AccountModel.participant_id == req.participant_id,
            AccountModel.event_id == req.event_id
        ).first()
        if not account:
            account = AccountModel(
                participant_id=req.participant_id,
                event_id=req.event_id,
                balance=0,
                credit_borrowed=0,
                credit_fee_paid=0
            )
            db.add(account)
            db.flush()

        balance_before = float(account.balance)
        balance_after = balance_before + req.amount

        # 扣款时检查余额是否足够（允许扣成负数，管理员操作不限制）
        txn_type = "recharge" if req.amount > 0 else "correction"
        remark = req.remark or ("管理员充值" if req.amount > 0 else "管理员扣款")

        # 写入交易记录
        txn = Transaction(
            uid=None,
            card_uid=participant.card_uid,
            event_id=req.event_id,
            participant_id=participant.id,
            account_id=account.id,
            type=txn_type,
            amount=abs(req.amount),
            balance_before=balance_before,
            balance_after=balance_after,
            merchant_id=None,
            remark=remark,
            operator_id=str(current_user.id)
        )
        db.add(txn)

        # 更新余额
        account.balance = balance_after
        db.commit()

        action = "充值" if req.amount > 0 else "扣款"
        logger.info(
            f"Admin {action}: participant={participant.name}(id={participant.id}), "
            f"amount={req.amount}, balance: {balance_before} -> {balance_after}, "
            f"operator={current_user.username}"
        )

        return {
            "success": True,
            "message": f"{action}成功",
            "participant_id": participant.id,
            "participant_name": participant.name,
            "amount": req.amount,
            "balance_before": balance_before,
            "balance_after": balance_after,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Admin adjust balance failed: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"error_code": "INTERNAL_ERROR", "message": str(e)})


@router.post("/participants/issue-loan")
async def admin_issue_loan(
    req: AdminIssueLoanRequest,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    管理员为参与者发放贷款。

    流程：
    1. 计算手续费 = amount * fee_rate
    2. 实际到账 = amount - 手续费
    3. 写入 loan_issue 和 loan_fee 流水
    4. 更新账户余额和借款记录
    5. 写入 bank_loans 表

    仅 super_admin 和 event_admin 可执行。
    """
    try:
        from decimal import Decimal, ROUND_HALF_UP

        # 查找参与者
        participant = db.query(Participant).filter(Participant.id == req.participant_id).first()
        if not participant:
            return JSONResponse(status_code=404, content={"error_code": "NOT_FOUND", "message": "参与者不存在"})

        # 获取或创建账户
        account = db.query(AccountModel).filter(
            AccountModel.participant_id == req.participant_id,
            AccountModel.event_id == req.event_id
        ).first()
        if not account:
            account = AccountModel(
                participant_id=req.participant_id,
                event_id=req.event_id,
                balance=0,
                credit_borrowed=0,
                credit_fee_paid=0
            )
            db.add(account)
            db.flush()

        # 计算金额
        nominal = Decimal(str(req.amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        fee_amount = (nominal * Decimal(str(req.fee_rate))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        actual_grant = nominal - fee_amount

        balance_before = float(account.balance)

        # 写入 loan_issue 流水
        txn_issue = Transaction(
            uid=None,
            card_uid=participant.card_uid,
            event_id=req.event_id,
            participant_id=participant.id,
            account_id=account.id,
            type="loan_issue",
            amount=float(nominal),
            balance_before=balance_before,
            balance_after=balance_before + float(nominal),
            merchant_id=None,
            remark=req.remark or f"管理员发放贷款：本金 {nominal} 元",
            operator_id=str(current_user.id)
        )
        db.add(txn_issue)
        db.flush()

        # 写入 loan_fee 流水
        balance_after_issue = balance_before + float(nominal)
        txn_fee = Transaction(
            uid=None,
            card_uid=participant.card_uid,
            event_id=req.event_id,
            participant_id=participant.id,
            account_id=account.id,
            type="loan_fee",
            amount=float(fee_amount),
            balance_before=balance_after_issue,
            balance_after=balance_after_issue - float(fee_amount),
            merchant_id=None,
            remark=f"贷款手续费：{req.fee_rate*100:.1f}% = {fee_amount} 元",
            operator_id=str(current_user.id)
        )
        db.add(txn_fee)
        db.flush()

        # 更新账户
        balance_after = balance_before + float(actual_grant)
        account.balance = balance_after
        account.credit_borrowed = float(account.credit_borrowed or 0) + float(nominal)
        account.credit_fee_paid = float(account.credit_fee_paid or 0) + float(fee_amount)

        # 写入 bank_loans 表
        db.execute(
            text("""INSERT INTO bank_loans
                    (event_id, participant_id, operator_id, principal_amount,
                     fee_rate, fee_amount, disbursed_amount, remark, status)
                    VALUES (:eid, :pid, :oid, :principal, :rate, :fee, :disbursed, :remark, 'active')"""),
            {
                "eid": req.event_id,
                "pid": participant.id,
                "oid": current_user.id,
                "principal": float(nominal),
                "rate": req.fee_rate,
                "fee": float(fee_amount),
                "disbursed": float(actual_grant),
                "remark": req.remark or "管理员后台发放",
            }
        )

        db.commit()

        logger.info(
            f"Admin loan issued: participant={participant.name}(id={participant.id}), "
            f"nominal={nominal}, fee={fee_amount}, actual={actual_grant}, "
            f"balance: {balance_before} -> {balance_after}, operator={current_user.username}"
        )

        return {
            "success": True,
            "message": "贷款发放成功",
            "participant_id": participant.id,
            "participant_name": participant.name,
            "nominal_amount": float(nominal),
            "fee_rate": req.fee_rate,
            "fee_amount": float(fee_amount),
            "actual_grant": float(actual_grant),
            "balance_before": balance_before,
            "balance_after": balance_after,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Admin issue loan failed: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"error_code": "INTERNAL_ERROR", "message": str(e)})


# ============================================================================
# 管理员操作：退卡
# ============================================================================

class AdminReturnCardRequest(BaseModel):
    """管理员退卡请求"""
    event_id: int = Field(..., description="活动ID")
    participant_id: int = Field(..., description="参与者ID")
    refund_balance: bool = Field(True, description="是否退还余额（记录退款流水）")
    remark: str = Field("", max_length=255, description="备注说明")


@router.post("/participants/return-card")
async def admin_return_card(
    req: AdminReturnCardRequest,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    管理员退卡处理。

    流程：
    1. 验证参与者存在
    2. 检查是否有未清贷款（有则拒绝退卡）
    3. 如果 refund_balance=true，将余额退还（写入退款流水）
    4. 将账户余额清零
    5. 解除卡片与参与者的绑定（card_uid 置空或标记为已退卡）
    6. 交易流水保留不删除

    仅 super_admin 和 event_admin 可执行。
    """
    try:
        # 1. 查找参与者
        participant = db.query(Participant).filter(Participant.id == req.participant_id).first()
        if not participant:
            return JSONResponse(status_code=404, content={
                "error_code": "NOT_FOUND",
                "message": "参与者不存在"
            })

        # 2. 获取账户
        account = db.query(AccountModel).filter(
            AccountModel.participant_id == req.participant_id,
            AccountModel.event_id == req.event_id
        ).first()

        # 3. 检查未清贷款
        outstanding_loans = db.execute(
            text("""SELECT COUNT(*) as cnt, COALESCE(SUM(principal_amount), 0) as total
                    FROM bank_loans
                    WHERE participant_id = :pid AND event_id = :eid AND status = 'active'"""),
            {"pid": req.participant_id, "eid": req.event_id}
        ).mappings().first()

        if outstanding_loans and outstanding_loans["cnt"] > 0:
            return JSONResponse(status_code=400, content={
                "error_code": "LOAN_NOT_CLEARED",
                "message": f"该参与者有 {outstanding_loans['cnt']} 笔未清贷款（共 ¥{float(outstanding_loans['total']):.2f}），请先清除贷款后再退卡",
                "outstanding_count": outstanding_loans["cnt"],
                "outstanding_amount": float(outstanding_loans["total"]),
            })

        # 4. 处理余额退还
        balance_before = float(account.balance) if account else 0.0
        refunded_amount = 0.0

        if account and balance_before > 0 and req.refund_balance:
            # 写入退款流水
            txn = Transaction(
                uid=None,
                card_uid=participant.card_uid,
                event_id=req.event_id,
                participant_id=participant.id,
                account_id=account.id,
                type="correction",
                amount=balance_before,
                balance_before=balance_before,
                balance_after=0,
                merchant_id=None,
                remark=req.remark or "退卡退款：余额清零退还",
                operator_id=str(current_user.id)
            )
            db.add(txn)
            refunded_amount = balance_before

            # 清零余额
            account.balance = 0

        elif account and balance_before != 0:
            # 余额为负或不退还，也清零
            txn = Transaction(
                uid=None,
                card_uid=participant.card_uid,
                event_id=req.event_id,
                participant_id=participant.id,
                account_id=account.id,
                type="correction",
                amount=abs(balance_before),
                balance_before=balance_before,
                balance_after=0,
                merchant_id=None,
                remark=req.remark or "退卡：余额清零",
                operator_id=str(current_user.id)
            )
            db.add(txn)
            account.balance = 0

        # 5. 解除卡片绑定：将参与者状态设为 inactive，保留 card_uid 用于历史追溯
        old_card_uid = participant.card_uid
        participant.status = 'inactive'
        # 释放 card_uid 以便卡片可以重新绑定给其他人
        participant.card_uid = f"RETURNED_{old_card_uid}_{participant.id}"

        db.commit()

        logger.info(
            f"Admin return card: participant={participant.name}(id={participant.id}), "
            f"card_uid={old_card_uid}, refunded={refunded_amount:.2f}, "
            f"balance_before={balance_before:.2f}, operator={current_user.username}"
        )

        return {
            "success": True,
            "message": "退卡成功",
            "participant_id": participant.id,
            "participant_name": participant.name,
            "card_uid": old_card_uid,
            "balance_refunded": refunded_amount,
            "balance_before": balance_before,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Admin return card failed: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={
            "error_code": "INTERNAL_ERROR",
            "message": str(e)
        })
