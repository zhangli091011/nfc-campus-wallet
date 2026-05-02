"""
Account service for NFC Campus Event Quota System.

管理活动账户的创建、查询等操作。
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List, Dict, Any
import logging

from models.account import Account
from core.exceptions import BusinessException

logger = logging.getLogger(__name__)


class AccountNotFoundError(BusinessException):
    """账户不存在异常"""
    
    def __init__(self, participant_id: int, event_id: int):
        super().__init__(
            message=f"Account not found for participant '{participant_id}' in event '{event_id}'",
            error_code="ACCOUNT_NOT_FOUND"
        )
        self.participant_id = participant_id
        self.event_id = event_id


class DuplicateAccountError(BusinessException):
    """重复创建账户异常"""
    
    def __init__(self, participant_id: int, event_id: int):
        super().__init__(
            message=f"Account already exists for participant '{participant_id}' in event '{event_id}'",
            error_code="DUPLICATE_ACCOUNT"
        )
        self.participant_id = participant_id
        self.event_id = event_id


class AccountService:
    """
    账户服务类。
    
    提供活动账户管理相关操作，包括自动创建、查询余额等。
    """
    
    def __init__(self, db_session: Session):
        """
        初始化账户服务。
        
        Args:
            db_session: SQLAlchemy 数据库会话
        """
        self.db = db_session
    
    def get_or_create_account(
        self,
        participant_id: int,
        event_id: int
    ) -> Account:
        """
        获取或创建账户。
        
        如果账户不存在，自动创建一个初始余额为 0 的账户。
        
        Args:
            participant_id: 参与者ID
            event_id: 活动ID
            
        Returns:
            Account: 账户对象
        """
        # 先尝试查询现有账户
        account = self.db.query(Account).filter(
            Account.participant_id == participant_id,
            Account.event_id == event_id
        ).first()
        
        if account is not None:
            logger.debug(
                f"Account found: participant_id={participant_id}, "
                f"event_id={event_id}, balance={account.balance} cents"
            )
            return account
        
        # 账户不存在，创建新账户
        try:
            account = Account(
                participant_id=participant_id,
                event_id=event_id,
                balance=0
            )
            
            self.db.add(account)
            self.db.commit()
            self.db.refresh(account)
            
            logger.info(
                f"Account created: id={account.id}, participant_id={participant_id}, "
                f"event_id={event_id}, initial_balance=0"
            )
            return account
            
        except IntegrityError as e:
            self.db.rollback()
            # 可能是并发创建导致的唯一性约束冲突，重新查询
            account = self.db.query(Account).filter(
                Account.participant_id == participant_id,
                Account.event_id == event_id
            ).first()
            
            if account is not None:
                logger.info(
                    f"Account created by concurrent request: participant_id={participant_id}, "
                    f"event_id={event_id}"
                )
                return account
            
            # 如果仍然找不到，说明是其他类型的完整性错误
            logger.error(f"Failed to create account: {str(e)}")
            raise
    
    def get_account(
        self,
        participant_id: int,
        event_id: int
    ) -> Optional[Account]:
        """
        查询账户。
        
        Args:
            participant_id: 参与者ID
            event_id: 活动ID
            
        Returns:
            Optional[Account]: 账户对象，如果不存在则返回 None
        """
        account = self.db.query(Account).filter(
            Account.participant_id == participant_id,
            Account.event_id == event_id
        ).first()
        
        if account is None:
            logger.debug(
                f"Account not found: participant_id={participant_id}, "
                f"event_id={event_id}"
            )
        
        return account
    
    def get_account_balance(
        self,
        participant_id: int,
        event_id: int
    ) -> int:
        """
        查询账户余额。
        
        Args:
            participant_id: 参与者ID
            event_id: 活动ID
            
        Returns:
            int: 账户余额（分），如果账户不存在则返回 0
        """
        account = self.get_account(participant_id, event_id)
        
        if account is None:
            logger.debug(
                f"Account not found, returning balance 0: participant_id={participant_id}, "
                f"event_id={event_id}"
            )
            return 0
        
        logger.debug(
            f"Account balance: participant_id={participant_id}, "
            f"event_id={event_id}, balance={account.balance} cents"
        )
        return account.balance
    
    def list_participant_accounts(
        self,
        participant_id: int
    ) -> List[Account]:
        """
        查询参与者的所有账户。
        
        Args:
            participant_id: 参与者ID
            
        Returns:
            List[Account]: 账户列表
        """
        accounts = self.db.query(Account).filter(
            Account.participant_id == participant_id
        ).order_by(Account.created_at.desc()).all()
        
        logger.info(
            f"Participant accounts listed: participant_id={participant_id}, "
            f"count={len(accounts)}"
        )
        
        return accounts
    
    def list_event_accounts(
        self,
        event_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        查询活动的所有账户（支持分页）。
        
        Args:
            event_id: 活动ID
            limit: 返回记录数限制
            offset: 偏移量
            
        Returns:
            Dict[str, Any]: 包含账户列表和总数
        """
        query = self.db.query(Account).filter(Account.event_id == event_id)
        
        total_count = query.count()
        
        accounts = query.order_by(
            Account.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        logger.info(
            f"Event accounts listed: event_id={event_id}, "
            f"count={len(accounts)}, total={total_count}"
        )
        
        return {
            'accounts': accounts,
            'total_count': total_count
        }
