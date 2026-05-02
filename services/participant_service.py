"""
Participant service for NFC Campus Event Quota System.

管理参与者的创建、查询、更新和卡片绑定等操作。
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Dict, Any
import logging
import re

from models.participant import Participant
from core.exceptions import BusinessException

logger = logging.getLogger(__name__)


class ParticipantNotFoundError(BusinessException):
    """参与者不存在异常"""
    
    def __init__(self, identifier: str):
        super().__init__(
            message=f"Participant with ID/card_uid '{identifier}' does not exist",
            error_code="PARTICIPANT_NOT_FOUND"
        )
        self.identifier = identifier


class CardAlreadyBoundError(BusinessException):
    """卡片已被绑定异常"""
    
    def __init__(self, card_uid: str):
        super().__init__(
            message=f"Card UID '{card_uid}' is already bound to another participant",
            error_code="CARD_ALREADY_BOUND"
        )
        self.card_uid = card_uid


class ParticipantBlockedError(BusinessException):
    """参与者已被封禁异常"""
    
    def __init__(self, participant_id: int):
        super().__init__(
            message=f"Participant '{participant_id}' is blocked",
            error_code="PARTICIPANT_BLOCKED"
        )
        self.participant_id = participant_id


class InvalidCardUIDError(BusinessException):
    """无效的卡片UID异常"""
    
    def __init__(self, card_uid: str):
        super().__init__(
            message=f"card_uid must be a hexadecimal string, got '{card_uid}'",
            error_code="VALIDATION_ERROR"
        )
        self.card_uid = card_uid


class ParticipantService:
    """
    参与者服务类。
    
    提供参与者管理相关操作，包括创建、查询、更新和卡片绑定。
    """
    
    def __init__(self, db_session: Session):
        """
        初始化参与者服务。
        
        Args:
            db_session: SQLAlchemy 数据库会话
        """
        self.db = db_session
    
    def _validate_card_uid_format(self, card_uid: str) -> str:
        """
        验证 card_uid 格式（十六进制字符串）。
        
        Args:
            card_uid: 卡片UID
            
        Returns:
            str: 大写的 card_uid
            
        Raises:
            InvalidCardUIDError: card_uid 格式无效
        """
        if not card_uid:
            raise InvalidCardUIDError(card_uid)
        
        # 验证是否为十六进制字符串
        if not re.match(r'^[0-9A-Fa-f]+$', card_uid):
            raise InvalidCardUIDError(card_uid)
        
        return card_uid.upper()
    
    def _check_card_uid_uniqueness(self, card_uid: str, exclude_participant_id: Optional[int] = None) -> None:
        """
        检查 card_uid 唯一性。
        
        Args:
            card_uid: 卡片UID
            exclude_participant_id: 排除的参与者ID（用于更新时）
            
        Raises:
            CardAlreadyBoundError: card_uid 已被绑定
        """
        query = self.db.query(Participant).filter(Participant.card_uid == card_uid)
        
        if exclude_participant_id is not None:
            query = query.filter(Participant.id != exclude_participant_id)
        
        existing = query.first()
        
        if existing:
            logger.warning(f"Card UID already bound: {card_uid} to participant {existing.id}")
            raise CardAlreadyBoundError(card_uid)
    
    def create_participant(
        self,
        name: str,
        card_uid: str,
        class_name: Optional[str] = None,
        student_no: Optional[str] = None,
        status: str = 'active'
    ) -> Participant:
        """
        创建新参与者。
        
        Args:
            name: 参与者姓名
            card_uid: NFC卡片UID
            class_name: 班级名称（可选）
            student_no: 学号（可选）
            status: 参与者状态（默认为 'active'）
            
        Returns:
            Participant: 新创建的参与者对象
            
        Raises:
            InvalidCardUIDError: card_uid 格式无效
            CardAlreadyBoundError: card_uid 已被绑定
        """
        # 验证 card_uid 格式
        card_uid = self._validate_card_uid_format(card_uid)
        
        # 检查 card_uid 唯一性
        self._check_card_uid_uniqueness(card_uid)
        
        try:
            participant = Participant(
                name=name,
                card_uid=card_uid,
                class_name=class_name,
                student_no=student_no,
                status=status
            )
            
            self.db.add(participant)
            self.db.commit()
            self.db.refresh(participant)
            
            logger.info(
                f"Participant created: id={participant.id}, name='{name}', "
                f"card_uid='{card_uid}'"
            )
            return participant
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create participant: {str(e)}")
            # 如果是唯一性约束错误，抛出更友好的异常
            if 'card_uid' in str(e):
                raise CardAlreadyBoundError(card_uid)
            raise
    
    def get_participant(self, participant_id: int) -> Participant:
        """
        获取参与者详情。
        
        Args:
            participant_id: 参与者ID
            
        Returns:
            Participant: 参与者对象
            
        Raises:
            ParticipantNotFoundError: 参与者不存在
        """
        participant = self.db.query(Participant).filter(
            Participant.id == participant_id
        ).first()
        
        if participant is None:
            logger.warning(f"Participant not found: {participant_id}")
            raise ParticipantNotFoundError(str(participant_id))
        
        return participant
    
    def get_participant_by_card(self, card_uid: str) -> Participant:
        """
        通过 card_uid 查询参与者。
        
        Args:
            card_uid: NFC卡片UID
            
        Returns:
            Participant: 参与者对象
            
        Raises:
            InvalidCardUIDError: card_uid 格式无效
            ParticipantNotFoundError: 参与者不存在
        """
        # 验证 card_uid 格式
        card_uid = self._validate_card_uid_format(card_uid)
        
        participant = self.db.query(Participant).filter(
            Participant.card_uid == card_uid
        ).first()
        
        if participant is None:
            logger.warning(f"Participant not found by card_uid: {card_uid}")
            raise ParticipantNotFoundError(card_uid)
        
        return participant
    
    def list_participants(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        获取参与者列表。
        
        Args:
            status: 参与者状态过滤（可选）
            limit: 返回记录数限制
            offset: 偏移量
            
        Returns:
            Dict: 包含参与者列表和总数
        """
        query = self.db.query(Participant)
        
        if status:
            query = query.filter(Participant.status == status)
        
        total_count = query.count()
        
        participants = query.order_by(
            Participant.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        logger.info(
            f"Participants listed: count={len(participants)}, total={total_count}, "
            f"status={status}"
        )
        
        return {
            'participants': participants,
            'total_count': total_count
        }
    
    def update_participant(
        self,
        participant_id: int,
        **kwargs
    ) -> Participant:
        """
        更新参与者信息。
        
        Args:
            participant_id: 参与者ID
            **kwargs: 要更新的字段
            
        Returns:
            Participant: 更新后的参与者对象
            
        Raises:
            ParticipantNotFoundError: 参与者不存在
            InvalidCardUIDError: card_uid 格式无效
            CardAlreadyBoundError: card_uid 已被绑定
        """
        participant = self.get_participant(participant_id)
        
        # 如果更新 card_uid，需要验证格式和唯一性
        if 'card_uid' in kwargs and kwargs['card_uid'] is not None:
            card_uid = self._validate_card_uid_format(kwargs['card_uid'])
            self._check_card_uid_uniqueness(card_uid, exclude_participant_id=participant_id)
            kwargs['card_uid'] = card_uid
        
        for key, value in kwargs.items():
            if value is not None and hasattr(participant, key):
                setattr(participant, key, value)
        
        try:
            self.db.commit()
            self.db.refresh(participant)
            
            logger.info(f"Participant updated: id={participant_id}")
            return participant
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to update participant: {str(e)}")
            # 如果是唯一性约束错误，抛出更友好的异常
            if 'card_uid' in str(e) and 'card_uid' in kwargs:
                raise CardAlreadyBoundError(kwargs['card_uid'])
            raise
    
    def bind_card(
        self,
        participant_id: int,
        card_uid: str
    ) -> Participant:
        """
        绑定卡片到参与者。
        
        Args:
            participant_id: 参与者ID
            card_uid: NFC卡片UID
            
        Returns:
            Participant: 更新后的参与者对象
            
        Raises:
            ParticipantNotFoundError: 参与者不存在
            InvalidCardUIDError: card_uid 格式无效
            CardAlreadyBoundError: card_uid 已被绑定
        """
        # 验证 card_uid 格式
        card_uid = self._validate_card_uid_format(card_uid)
        
        # 检查 card_uid 唯一性
        self._check_card_uid_uniqueness(card_uid, exclude_participant_id=participant_id)
        
        # 更新参与者的 card_uid
        participant = self.update_participant(participant_id, card_uid=card_uid)
        
        logger.info(
            f"Card bound to participant: participant_id={participant_id}, "
            f"card_uid='{card_uid}'"
        )
        
        return participant
