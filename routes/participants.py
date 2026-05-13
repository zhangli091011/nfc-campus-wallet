"""
Participants routes for NFC Campus Event Quota System.

提供参与者管理相关的 API 端点。
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from core.database import get_db
from core.security import get_current_user
from services.participant_service import (
    ParticipantService,
    ParticipantNotFoundError,
    CardAlreadyBoundError,
    ParticipantBlockedError,
    InvalidCardUIDError
)
from schemas.participant import (
    ParticipantCreate,
    ParticipantUpdate,
    ParticipantResponse,
    ParticipantListResponse,
    CardBindRequest
)
from core.exceptions import BusinessException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/participants", response_model=ParticipantResponse, status_code=201)
async def create_participant(
    participant_data: ParticipantCreate,
    db: Session = Depends(get_db)
):
    """
    创建新参与者。
    
    Request Body:
        - name: 参与者姓名（必填，1-100字符）
        - card_uid: NFC卡片UID（必填，十六进制字符串，1-32字符）
        - class_name: 班级名称（可选，最大100字符）
        - student_no: 学号（可选，最大50字符）
        - status: 参与者状态（可选，默认为 'active'）
    
    Returns:
        ParticipantResponse: 创建的参与者信息
        
    Error Responses:
        400: 验证错误（如 card_uid 格式无效或已被绑定）
        500: 内部服务器错误
    
    Example:
        POST /participants
        {
            "name": "张三",
            "class_name": "高一(1)班",
            "student_no": "2024001",
            "card_uid": "A1B2C3D4",
            "status": "active"
        }
    """
    try:
        participant_service = ParticipantService(db)
        
        participant = participant_service.create_participant(
            name=participant_data.name,
            card_uid=participant_data.card_uid,
            class_name=participant_data.class_name,
            student_no=participant_data.student_no,
            status=participant_data.status.value
        )
        
        logger.info(
            f"Participant created successfully: id={participant.id}, "
            f"name='{participant.name}', card_uid='{participant.card_uid}'"
        )
        
        return ParticipantResponse.model_validate(participant)
    
    except (InvalidCardUIDError, CardAlreadyBoundError) as e:
        logger.warning(f"Participant creation validation failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except ValueError as e:
        logger.warning(f"Participant creation validation failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": str(e)
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in participant creation: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )


@router.get("/participants", response_model=ParticipantListResponse)
async def list_participants(
    status: Optional[str] = Query(None, description="Filter by participant status (active/inactive/blocked)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of participants to return"),
    offset: int = Query(0, ge=0, description="Number of participants to skip"),
    db: Session = Depends(get_db)
):
    """
    获取参与者列表，支持状态过滤和分页。
    
    Query Parameters:
        - status: 参与者状态过滤（可选）
        - limit: 返回记录数限制（默认100，最大1000）
        - offset: 偏移量（默认0）
    
    Returns:
        ParticipantListResponse: 参与者列表和总数
        
    Error Responses:
        500: 内部服务器错误
    
    Example:
        GET /participants?status=active&limit=10&offset=0
    """
    try:
        participant_service = ParticipantService(db)
        
        result = participant_service.list_participants(
            status=status,
            limit=limit,
            offset=offset
        )
        
        logger.info(
            f"Participants listed: count={len(result['participants'])}, "
            f"total={result['total_count']}, status={status}"
        )
        
        return ParticipantListResponse(
            participants=[ParticipantResponse.model_validate(p) for p in result['participants']],
            total_count=result['total_count']
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in participant listing: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )


@router.get("/participants/{participant_id}", response_model=ParticipantResponse)
async def get_participant(
    participant_id: int,
    db: Session = Depends(get_db)
):
    """
    获取参与者详情。
    
    Path Parameters:
        - participant_id: 参与者ID
    
    Returns:
        ParticipantResponse: 参与者详细信息
        
    Error Responses:
        400: 参与者不存在
        500: 内部服务器错误
    
    Example:
        GET /participants/1
    """
    try:
        participant_service = ParticipantService(db)
        
        participant = participant_service.get_participant(participant_id)
        
        logger.info(
            f"Participant retrieved: id={participant_id}, "
            f"name='{participant.name}'"
        )
        
        return ParticipantResponse.model_validate(participant)
    
    except ParticipantNotFoundError as e:
        logger.warning(f"Participant not found: {participant_id}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in participant retrieval: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )


@router.patch("/participants/{participant_id}", response_model=ParticipantResponse)
async def update_participant(
    participant_id: int,
    participant_data: ParticipantUpdate,
    db: Session = Depends(get_db)
):
    """
    更新参与者信息（部分更新）。
    
    Path Parameters:
        - participant_id: 参与者ID
    
    Request Body:
        - name: 参与者姓名（可选）
        - class_name: 班级名称（可选）
        - student_no: 学号（可选）
        - status: 参与者状态（可选）
    
    Returns:
        ParticipantResponse: 更新后的参与者信息
        
    Error Responses:
        400: 参与者不存在或验证错误
        500: 内部服务器错误
    
    Example:
        PATCH /participants/1
        {
            "name": "张三",
            "class_name": "高一(2)班",
            "status": "active"
        }
    """
    try:
        participant_service = ParticipantService(db)
        
        # 构建更新参数字典，只包含非 None 的字段
        update_data = {}
        if participant_data.name is not None:
            update_data['name'] = participant_data.name
        if participant_data.class_name is not None:
            update_data['class_name'] = participant_data.class_name
        if participant_data.student_no is not None:
            update_data['student_no'] = participant_data.student_no
        if participant_data.status is not None:
            update_data['status'] = participant_data.status.value
        
        participant = participant_service.update_participant(
            participant_id,
            **update_data
        )
        
        logger.info(
            f"Participant updated successfully: id={participant_id}, "
            f"updated_fields={list(update_data.keys())}"
        )
        
        return ParticipantResponse.model_validate(participant)
    
    except ParticipantNotFoundError as e:
        logger.warning(f"Participant not found for update: {participant_id}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except ValueError as e:
        logger.warning(f"Participant update validation failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": str(e)
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in participant update: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )


@router.post("/participants/bind-card", response_model=ParticipantResponse)
async def bind_card(
    bind_data: CardBindRequest,
    db: Session = Depends(get_db)
):
    """
    绑定卡片到参与者。
    
    Request Body:
        - participant_id: 参与者ID（必填）
        - card_uid: NFC卡片UID（必填，十六进制字符串）
    
    Returns:
        ParticipantResponse: 更新后的参与者信息
        
    Error Responses:
        400: 参与者不存在、card_uid 格式无效或已被绑定
        500: 内部服务器错误
    
    Example:
        POST /participants/bind-card
        {
            "participant_id": 1,
            "card_uid": "A1B2C3D4"
        }
    """
    try:
        participant_service = ParticipantService(db)
        
        participant = participant_service.bind_card(
            participant_id=bind_data.participant_id,
            card_uid=bind_data.card_uid
        )
        
        logger.info(
            f"Card bound successfully: participant_id={bind_data.participant_id}, "
            f"card_uid='{bind_data.card_uid}'"
        )
        
        return ParticipantResponse.model_validate(participant)
    
    except (ParticipantNotFoundError, InvalidCardUIDError, CardAlreadyBoundError) as e:
        logger.warning(f"Card binding failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in card binding: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )


@router.delete("/participants/clear-all")
async def clear_all_participants(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    清除所有参与者数据。

    ⚠️ 危险操作：将删除所有参与者及其关联的账户记录。
    交易记录保留用于审计。仅 super_admin 可执行。

    Returns:
        JSON: 删除的参与者数量
    """
    from models.participant import Participant
    from models.account import Account

    # 权限校验：仅 super_admin
    if current_user.role != 'super_admin':
        return JSONResponse(
            status_code=403,
            content={
                "error_code": "FORBIDDEN",
                "message": "仅超级管理员可清除所有参与者"
            }
        )

    try:
        # 先删除所有账户（外键依赖）
        accounts_deleted = db.query(Account).delete()
        # 再删除所有参与者
        participants_deleted = db.query(Participant).delete()
        db.commit()

        logger.info(
            f"All participants cleared by {current_user.username}: "
            f"{participants_deleted} participants, {accounts_deleted} accounts deleted"
        )

        return {
            "success": True,
            "message": f"已清除 {participants_deleted} 个参与者和 {accounts_deleted} 个账户",
            "participants_deleted": participants_deleted,
            "accounts_deleted": accounts_deleted,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to clear all participants: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": f"清除参与者失败: {str(e)}"
            }
        )


@router.get("/participants/by-card/{card_uid}", response_model=ParticipantResponse)
async def get_participant_by_card(
    card_uid: str,
    db: Session = Depends(get_db)
):
    """
    通过卡片UID查询参与者。
    
    Path Parameters:
        - card_uid: NFC卡片UID（十六进制字符串）
    
    Returns:
        ParticipantResponse: 参与者详细信息
        
    Error Responses:
        400: 参与者不存在或 card_uid 格式无效
        500: 内部服务器错误
    
    Example:
        GET /participants/by-card/A1B2C3D4
    """
    try:
        participant_service = ParticipantService(db)
        
        participant = participant_service.get_participant_by_card(card_uid)
        
        logger.info(
            f"Participant retrieved by card: card_uid='{card_uid}', "
            f"id={participant.id}, name='{participant.name}'"
        )
        
        return ParticipantResponse.model_validate(participant)
    
    except (ParticipantNotFoundError, InvalidCardUIDError) as e:
        logger.warning(f"Participant not found by card: {card_uid}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in participant retrieval by card: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )



@router.get("/participants/card-detail/{card_uid}")
async def get_card_detail(
    card_uid: str,
    event_id: Optional[int] = Query(None, description="活动ID（可选，不传则返回所有活动的数据）"),
    db: Session = Depends(get_db)
):
    """
    通过卡片UID查询持卡人完整明细信息。

    返回：参与者基本信息 + 账户余额 + 贷款信息 + 最近交易流水

    Path Parameters:
        - card_uid: NFC卡片UID

    Query Parameters:
        - event_id: 活动ID（可选）

    Returns:
        {
            "participant": {...},
            "account": {...},
            "loans": {...},
            "transactions": [...]
        }
    """
    from models.account import Account
    from models.transaction import Transaction as TransactionModel
    from sqlalchemy import text

    try:
        participant_service = ParticipantService(db)

        # 查找参与者
        try:
            participant = participant_service.get_participant_by_card(card_uid)
        except (ParticipantNotFoundError, InvalidCardUIDError) as e:
            return JSONResponse(
                status_code=400,
                content={"error_code": e.error_code, "message": e.message}
            )

        # 基本信息
        participant_data = {
            "id": participant.id,
            "name": participant.name,
            "card_uid": participant.card_uid,
            "class_name": participant.class_name,
            "student_no": participant.student_no,
            "status": participant.status,
            "created_at": participant.created_at.isoformat() if participant.created_at else None,
        }

        # 账户信息
        account_query = db.query(Account).filter(Account.participant_id == participant.id)
        if event_id:
            account_query = account_query.filter(Account.event_id == event_id)
        account = account_query.first()

        account_data = None
        if account:
            account_data = {
                "event_id": account.event_id,
                "balance": float(account.balance) if account.balance is not None else 0.0,
                "credit_borrowed": float(account.credit_borrowed) if account.credit_borrowed is not None else 0.0,
                "credit_fee_paid": float(account.credit_fee_paid) if account.credit_fee_paid is not None else 0.0,
            }

        # 贷款信息
        loan_filter = {"pid": participant.id}
        loan_sql = """SELECT COUNT(*) as cnt, COALESCE(SUM(principal_amount), 0) as total
                      FROM bank_loans
                      WHERE participant_id = :pid AND status = 'active'"""
        if event_id:
            loan_sql += " AND event_id = :eid"
            loan_filter["eid"] = event_id

        try:
            loan_result = db.execute(text(loan_sql), loan_filter).mappings().first()
            loans_data = {
                "active_count": int(loan_result["cnt"]) if loan_result else 0,
                "total_debt": float(loan_result["total"]) if loan_result else 0.0,
            }
        except Exception:
            loans_data = {"active_count": 0, "total_debt": 0.0}

        # 最近交易流水（最多50条）
        txn_query = db.query(TransactionModel).filter(
            TransactionModel.participant_id == participant.id
        )
        if event_id:
            txn_query = txn_query.filter(TransactionModel.event_id == event_id)
        txn_query = txn_query.order_by(TransactionModel.created_at.desc()).limit(50)
        transactions = txn_query.all()

        transactions_data = []
        for txn in transactions:
            transactions_data.append({
                "id": txn.id,
                "type": txn.type,
                "amount": float(txn.amount),
                "balance_before": float(txn.balance_before) if txn.balance_before is not None else 0.0,
                "balance_after": float(txn.balance_after) if txn.balance_after is not None else 0.0,
                "remark": txn.remark,
                "booth_id": txn.booth_id,
                "created_at": txn.created_at.isoformat() if txn.created_at else None,
            })

        # 股票持仓信息
        stock_holdings_data = []
        if event_id:
            try:
                stock_rows = db.execute(
                    text("""SELECT sh.booth_id, b.name as booth_name, sh.shares, sh.total_cost
                            FROM stock_holdings sh
                            LEFT JOIN booths b ON sh.booth_id = b.id
                            WHERE sh.participant_id = :pid AND sh.event_id = :eid AND sh.shares > 0"""),
                    {"pid": participant.id, "eid": event_id}
                ).mappings().all()
                for row in stock_rows:
                    stock_holdings_data.append({
                        "booth_id": row["booth_id"],
                        "booth_name": row["booth_name"],
                        "shares": int(row["shares"]),
                        "total_cost": float(row["total_cost"]) if row["total_cost"] else 0.0,
                    })
            except Exception:
                pass  # stock_holdings 表可能不存在

        logger.info(
            f"Card detail retrieved: card_uid={card_uid}, participant={participant.name}, "
            f"txn_count={len(transactions_data)}"
        )

        return {
            "participant": participant_data,
            "account": account_data,
            "loans": loans_data,
            "stock_holdings": stock_holdings_data,
            "transactions": transactions_data,
        }

    except Exception as e:
        logger.error(f"Unexpected error in card detail: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": str(e)}
        )


@router.delete("/participants/{participant_id}", status_code=204)
async def delete_participant(
    participant_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    删除参与者。

    仅 super_admin 可执行此操作。
    会级联删除关联的账户记录。关联的交易记录不会被删除（保留审计）。

    Path Parameters:
        - participant_id: 参与者ID
    """
    from models.participant import Participant
    from models.account import Account

    # 权限校验：仅 super_admin
    if current_user.role != 'super_admin':
        return JSONResponse(
            status_code=403,
            content={
                "error_code": "FORBIDDEN",
                "message": "仅超级管理员可删除参与者"
            }
        )

    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if participant is None:
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "PARTICIPANT_NOT_FOUND",
                "message": f"参与者 {participant_id} 不存在"
            }
        )

    # 删除关联账户
    db.query(Account).filter(Account.participant_id == participant_id).delete()

    db.delete(participant)
    db.commit()

    logger.info(f"Participant deleted by {current_user.username}: id={participant_id}, name={participant.name}")
    return None
