"""
Booth service for Booth Management System.

管理摊位的创建、查询、更新等操作。
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import logging

from models.booth import Booth
from models.event import Event
from core.exceptions import BusinessException

logger = logging.getLogger(__name__)


class BoothNotFoundError(BusinessException):
    """摊位不存在异常"""
    
    def __init__(self, booth_id: int):
        super().__init__(
            message=f"Booth with ID '{booth_id}' does not exist",
            error_code="BOOTH_NOT_FOUND"
        )
        self.booth_id = booth_id


class BoothInactiveError(BusinessException):
    """摊位未激活异常"""
    
    def __init__(self, booth_id: int):
        super().__init__(
            message=f"Booth '{booth_id}' is not active",
            error_code="BOOTH_INACTIVE"
        )
        self.booth_id = booth_id


class InvalidEventError(BusinessException):
    """无效活动异常"""
    
    def __init__(self, event_id: int):
        super().__init__(
            message=f"Event with ID '{event_id}' does not exist",
            error_code="INVALID_EVENT_ID"
        )
        self.event_id = event_id


class BoothNotInEventError(BusinessException):
    """摊位不属于活动异常"""
    
    def __init__(self, booth_id: int, event_id: int):
        super().__init__(
            message=f"Booth '{booth_id}' does not belong to event '{event_id}'",
            error_code="BOOTH_NOT_IN_EVENT"
        )
        self.booth_id = booth_id
        self.event_id = event_id


class BoothService:
    """
    摊位服务类。
    
    提供摊位管理相关操作。
    """
    
    def __init__(self, db_session: Session):
        """
        初始化摊位服务。
        
        Args:
            db_session: SQLAlchemy 数据库会话
        """
        self.db = db_session
    
    def create_booth(
        self,
        event_id: int,
        name: str,
        class_name: str,
        status: str = 'active'
    ) -> Booth:
        """
        创建新摊位。
        
        验证 event_id 存在后创建摊位。
        
        Args:
            event_id: 活动ID
            name: 摊位名称
            class_name: 班级名称
            status: 摊位状态（默认 'active'）
            
        Returns:
            Booth: 新创建的摊位对象
            
        Raises:
            InvalidEventError: 活动不存在
        """
        # 验证活动是否存在
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if event is None:
            logger.warning(f"Cannot create booth: event {event_id} does not exist")
            raise InvalidEventError(event_id)
        
        try:
            booth = Booth(
                event_id=event_id,
                name=name,
                class_name=class_name,
                status=status
            )
            
            self.db.add(booth)
            self.db.commit()
            self.db.refresh(booth)
            
            logger.info(
                f"Booth created: id={booth.id}, name='{name}', "
                f"class_name='{class_name}', event_id={event_id}"
            )
            return booth
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create booth: {str(e)}")
            raise
    
    def get_booth(self, booth_id: int) -> Booth:
        """
        获取摊位详情。
        
        Args:
            booth_id: 摊位ID
            
        Returns:
            Booth: 摊位对象
            
        Raises:
            BoothNotFoundError: 摊位不存在
        """
        booth = self.db.query(Booth).filter(Booth.id == booth_id).first()
        
        if booth is None:
            logger.warning(f"Booth not found: {booth_id}")
            raise BoothNotFoundError(booth_id)
        
        return booth
    
    def list_booths(
        self,
        event_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Booth]:
        """
        列出摊位。
        
        支持按 event_id 和 status 过滤。
        
        Args:
            event_id: 活动ID过滤（可选）
            status: 摊位状态过滤（可选）
            limit: 返回记录数限制
            offset: 偏移量
            
        Returns:
            List[Booth]: 摊位列表
        """
        query = self.db.query(Booth)
        
        if event_id is not None:
            query = query.filter(Booth.event_id == event_id)
        
        if status is not None:
            query = query.filter(Booth.status == status)
        
        booths = query.order_by(Booth.created_at.desc()).limit(limit).offset(offset).all()
        
        logger.info(f"Booths listed: count={len(booths)}, event_id={event_id}, status={status}")
        
        return booths
    
    def update_booth_status(
        self,
        booth_id: int,
        status: str
    ) -> Booth:
        """
        更新摊位状态。
        
        Args:
            booth_id: 摊位ID
            status: 新状态（'active', 'inactive', 'closed'）
            
        Returns:
            Booth: 更新后的摊位对象
            
        Raises:
            BoothNotFoundError: 摊位不存在
        """
        booth = self.get_booth(booth_id)
        
        booth.status = status
        
        try:
            self.db.commit()
            self.db.refresh(booth)
            
            logger.info(f"Booth status updated: id={booth_id}, status='{status}'")
            return booth
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to update booth status: {str(e)}")
            raise
    
    def validate_booth_belongs_to_event(
        self,
        booth_id: int,
        event_id: int
    ) -> Booth:
        """
        验证摊位属于指定活动。
        
        Args:
            booth_id: 摊位ID
            event_id: 活动ID
            
        Returns:
            Booth: 摊位对象
            
        Raises:
            BoothNotFoundError: 摊位不存在
            BoothNotInEventError: 摊位不属于指定活动
        """
        booth = self.get_booth(booth_id)
        
        if booth.event_id != event_id:
            logger.warning(
                f"Booth {booth_id} does not belong to event {event_id} "
                f"(actual event_id: {booth.event_id})"
            )
            raise BoothNotInEventError(booth_id, event_id)
        
        return booth
    
    def validate_booth_active(self, booth_id: int) -> Booth:
        """
        验证摊位是否激活。
        
        Args:
            booth_id: 摊位ID
            
        Returns:
            Booth: 摊位对象
            
        Raises:
            BoothNotFoundError: 摊位不存在
            BoothInactiveError: 摊位未激活
        """
        booth = self.get_booth(booth_id)
        
        if not booth.is_active():
            logger.warning(f"Booth {booth_id} is not active (status: {booth.status})")
            raise BoothInactiveError(booth_id)
        
        return booth
