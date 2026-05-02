"""
Events routes for NFC Campus Event Quota System.

提供活动管理相关的 API 端点。
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from app.database import get_db
from services.event_service import EventService, EventNotFoundError, EventInactiveError
from schemas.event import EventCreate, EventUpdate, EventResponse, EventListResponse
from core.exceptions import BusinessException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/events", response_model=EventResponse, status_code=201)
async def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db)
):
    """
    创建新活动。
    
    Request Body:
        - name: 活动名称（必填，1-255字符）
        - start_time: 开始时间（必填，ISO 8601格式）
        - end_time: 结束时间（必填，ISO 8601格式，必须晚于开始时间）
        - status: 活动状态（可选，默认为 'draft'）
        - recharge_enabled: 是否允许充值（可选，默认为 true）
        - consume_enabled: 是否允许消费（可选，默认为 true）
        - expire_rule: 过期规则（可选，默认为 'event_end'）
    
    Returns:
        EventResponse: 创建的活动信息
        
    Error Responses:
        400: 验证错误（如结束时间早于开始时间）
        500: 内部服务器错误
    
    Example:
        POST /events
        {
            "name": "2024春季校园美食节",
            "start_time": "2024-03-01T08:00:00Z",
            "end_time": "2024-03-03T20:00:00Z",
            "status": "draft",
            "recharge_enabled": true,
            "consume_enabled": true,
            "expire_rule": "event_end"
        }
    """
    try:
        event_service = EventService(db)
        
        event = event_service.create_event(
            name=event_data.name,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            status=event_data.status.value,
            recharge_enabled=event_data.recharge_enabled,
            consume_enabled=event_data.consume_enabled,
            expire_rule=event_data.expire_rule.value
        )
        
        logger.info(
            f"Event created successfully: id={event.id}, name='{event.name}'"
        )
        
        return EventResponse.model_validate(event)
    
    except ValueError as e:
        logger.warning(f"Event creation validation failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": str(e)
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in event creation: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )


@router.get("/events", response_model=EventListResponse)
async def list_events(
    status: Optional[str] = Query(None, description="Filter by event status (draft/active/paused/ended)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    db: Session = Depends(get_db)
):
    """
    获取活动列表，支持状态过滤和分页。
    
    Query Parameters:
        - status: 活动状态过滤（可选）
        - limit: 返回记录数限制（默认100，最大1000）
        - offset: 偏移量（默认0）
    
    Returns:
        EventListResponse: 活动列表和总数
        
    Error Responses:
        500: 内部服务器错误
    
    Example:
        GET /events?status=active&limit=10&offset=0
    """
    try:
        event_service = EventService(db)
        
        result = event_service.list_events(
            status=status,
            limit=limit,
            offset=offset
        )
        
        logger.info(
            f"Events listed: count={len(result['events'])}, "
            f"total={result['total_count']}, status={status}"
        )
        
        return EventListResponse(
            events=[EventResponse.model_validate(event) for event in result['events']],
            total_count=result['total_count']
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in event listing: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    """
    获取活动详情。
    
    Path Parameters:
        - event_id: 活动ID
    
    Returns:
        EventResponse: 活动详细信息
        
    Error Responses:
        400: 活动不存在
        500: 内部服务器错误
    
    Example:
        GET /events/1
    """
    try:
        event_service = EventService(db)
        
        event = event_service.get_event(event_id)
        
        logger.info(f"Event retrieved: id={event_id}, name='{event.name}'")
        
        return EventResponse.model_validate(event)
    
    except EventNotFoundError as e:
        logger.warning(f"Event not found: {event_id}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in event retrieval: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )


@router.patch("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    db: Session = Depends(get_db)
):
    """
    更新活动信息（部分更新）。
    
    Path Parameters:
        - event_id: 活动ID
    
    Request Body:
        - name: 活动名称（可选）
        - start_time: 开始时间（可选）
        - end_time: 结束时间（可选）
        - status: 活动状态（可选）
        - recharge_enabled: 是否允许充值（可选）
        - consume_enabled: 是否允许消费（可选）
        - expire_rule: 过期规则（可选）
    
    Returns:
        EventResponse: 更新后的活动信息
        
    Error Responses:
        400: 活动不存在或验证错误
        500: 内部服务器错误
    
    Example:
        PATCH /events/1
        {
            "status": "active",
            "recharge_enabled": true
        }
    """
    try:
        event_service = EventService(db)
        
        # 构建更新参数字典，只包含非 None 的字段
        update_data = {}
        if event_data.name is not None:
            update_data['name'] = event_data.name
        if event_data.start_time is not None:
            update_data['start_time'] = event_data.start_time
        if event_data.end_time is not None:
            update_data['end_time'] = event_data.end_time
        if event_data.status is not None:
            update_data['status'] = event_data.status.value
        if event_data.recharge_enabled is not None:
            update_data['recharge_enabled'] = event_data.recharge_enabled
        if event_data.consume_enabled is not None:
            update_data['consume_enabled'] = event_data.consume_enabled
        if event_data.expire_rule is not None:
            update_data['expire_rule'] = event_data.expire_rule.value
        
        event = event_service.update_event(event_id, **update_data)
        
        logger.info(
            f"Event updated successfully: id={event_id}, "
            f"updated_fields={list(update_data.keys())}"
        )
        
        return EventResponse.model_validate(event)
    
    except EventNotFoundError as e:
        logger.warning(f"Event not found for update: {event_id}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except ValueError as e:
        logger.warning(f"Event update validation failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": str(e)
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in event update: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )
