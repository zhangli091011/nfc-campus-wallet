"""
Participants routes for NFC Campus Event Quota System.

提供参与者管理相关的 API 端点。
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from app.database import get_db
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
