"""
Event service for NFC Campus Event Quota System.

管理活动的创建、查询、更新等操作。
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict
from datetime import datetime, timezone
import logging

from models.event import Event
from core.exceptions import BusinessException

logger = logging.getLogger(__name__)


class EventNotFoundError(BusinessException):
    """活动不存在异常"""
    
    def __init__(self, event_id: int):
        super().__init__(
            message=f"Event with ID '{event_id}' does not exist",
            error_code="EVENT_NOT_FOUND"
        )
        self.event_id = event_id


class EventInactiveError(BusinessException):
    """活动未激活异常"""
    
    def __init__(self, event_id: int, reason: str):
        super().__init__(
            message=f"Event '{event_id}' is not active: {reason}",
            error_code="EVENT_INACTIVE"
        )
        self.event_id = event_id


class EventService:
    """
    活动服务类。
    
    提供活动管理相关操作。
    """
    
    def __init__(self, db_session: Session):
        """
        初始化活动服务。
        
        Args:
            db_session: SQLAlchemy 数据库会话
        """
        self.db = db_session
    
    def create_event(
        self,
        name: str,
        start_time: datetime,
        end_time: datetime,
        status: str = 'draft',
        recharge_enabled: bool = True,
        consume_enabled: bool = True,
        expire_rule: str = 'event_end'
    ) -> Event:
        """
        创建新活动。
        
        Args:
            name: 活动名称
            start_time: 开始时间
            end_time: 结束时间
            status: 活动状态
            recharge_enabled: 是否允许充值
            consume_enabled: 是否允许消费
            expire_rule: 过期规则
            
        Returns:
            Event: 新创建的活动对象
        """
        try:
            event = Event(
                name=name,
                start_time=start_time,
                end_time=end_time,
                status=status,
                recharge_enabled=recharge_enabled,
                consume_enabled=consume_enabled,
                expire_rule=expire_rule
            )
            
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            
            logger.info(f"Event created: id={event.id}, name='{name}'")
            return event
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create event: {str(e)}")
            raise
    
    def get_event(self, event_id: int) -> Event:
        """
        获取活动详情。
        
        Args:
            event_id: 活动ID
            
        Returns:
            Event: 活动对象
            
        Raises:
            EventNotFoundError: 活动不存在
        """
        event = self.db.query(Event).filter(Event.id == event_id).first()
        
        if event is None:
            logger.warning(f"Event not found: {event_id}")
            raise EventNotFoundError(event_id)
        
        return event
    
    def list_events(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict:
        """
        获取活动列表。
        
        Args:
            status: 活动状态过滤（可选）
            limit: 返回记录数限制
            offset: 偏移量
            
        Returns:
            Dict: 包含活动列表和总数
        """
        query = self.db.query(Event)
        
        if status:
            query = query.filter(Event.status == status)
        
        total_count = query.count()
        
        events = query.order_by(Event.created_at.desc()).limit(limit).offset(offset).all()
        
        logger.info(f"Events listed: count={len(events)}, total={total_count}")
        
        return {
            'events': events,
            'total_count': total_count
        }
    
    def update_event(
        self,
        event_id: int,
        **kwargs
    ) -> Event:
        """
        更新活动信息。
        
        Args:
            event_id: 活动ID
            **kwargs: 要更新的字段
            
        Returns:
            Event: 更新后的活动对象
            
        Raises:
            EventNotFoundError: 活动不存在
        """
        event = self.get_event(event_id)
        
        for key, value in kwargs.items():
            if value is not None and hasattr(event, key):
                setattr(event, key, value)
        
        try:
            self.db.commit()
            self.db.refresh(event)
            
            logger.info(f"Event updated: id={event_id}")
            return event
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to update event: {str(e)}")
            raise
    
    def validate_event_for_recharge(self, event_id: int) -> Event:
        """
        验证活动是否允许充值。
        
        Args:
            event_id: 活动ID
            
        Returns:
            Event: 活动对象
            
        Raises:
            EventNotFoundError: 活动不存在
            EventInactiveError: 活动不允许充值
        """
        event = self.get_event(event_id)
        
        if not event.can_recharge():
            if event.status != 'active':
                raise EventInactiveError(event_id, f"status is '{event.status}'")
            elif not event.is_within_time_range():
                raise EventInactiveError(event_id, "not within time range")
            elif not event.recharge_enabled:
                raise EventInactiveError(event_id, "recharge is disabled")
        
        return event
    
    def validate_event_for_consume(self, event_id: int) -> Event:
        """
        验证活动是否允许消费。
        
        Args:
            event_id: 活动ID
            
        Returns:
            Event: 活动对象
            
        Raises:
            EventNotFoundError: 活动不存在
            EventInactiveError: 活动不允许消费
        """
        event = self.get_event(event_id)
        
        if not event.can_consume():
            if event.status != 'active':
                raise EventInactiveError(event_id, f"status is '{event.status}'")
            elif not event.is_within_time_range():
                raise EventInactiveError(event_id, "not within time range")
            elif not event.consume_enabled:
                raise EventInactiveError(event_id, "consumption is disabled")
        
        return event
