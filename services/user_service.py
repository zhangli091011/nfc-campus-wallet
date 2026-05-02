"""
User service for Booth Management System.

管理系统用户账户操作，包括用户创建、查询、更新状态等。
支持基于角色的访问控制（RBAC）。
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import logging

from models.user import User
from models.booth import Booth
from core.security import hash_password
from core.exceptions import (
    UserNotFoundError,
    ValidationError,
    ResourceNotFoundError
)

logger = logging.getLogger(__name__)


class UserService:
    """
    用户服务类（摊位管理系统）。
    
    提供系统用户相关操作，支持多种角色和权限管理。
    
    Validates Requirements:
        - Requirement 3.1-3.9: 用户角色系统
    """
    
    def __init__(self, db_session: Session):
        """
        初始化用户服务。
        
        Args:
            db_session: SQLAlchemy 数据库会话
        """
        self.db = db_session
    
    def create_user(
        self,
        username: str,
        password: str,
        role: str,
        booth_id: Optional[int] = None
    ) -> User:
        """
        创建新用户账户。
        
        验证流程:
        1. 验证用户名唯一性
        2. 验证角色有效性
        3. 如果是 booth_cashier，验证 booth_id 必须提供且有效
        4. 如果不是 booth_cashier，booth_id 必须为 None
        5. 哈希密码
        6. 创建用户记录
        
        Args:
            username: 用户名（唯一）
            password: 明文密码（将被哈希）
            role: 用户角色 (super_admin, event_admin, booth_cashier, issuer, reviewer)
            booth_id: 关联摊位ID（仅 booth_cashier 需要）
            
        Returns:
            User: 新创建的用户对象
            
        Raises:
            ValidationError: 验证失败（用户名已存在、角色无效、booth_id 不匹配等）
            ResourceNotFoundError: booth_id 对应的摊位不存在
            
        Validates Requirements:
            - Requirement 3.1: Store user records with required fields
            - Requirement 3.2: Assign unique auto-incrementing id
            - Requirement 3.3: Enforce unique usernames
            - Requirement 3.4: Support valid role values
            - Requirement 3.5: Support user status values (default: active)
            - Requirement 3.6: booth_cashier must have valid booth_id
            - Requirement 3.7: Non-booth_cashier roles allow null booth_id
            - Requirement 3.9: Hash passwords using secure algorithm
        """
        # Validate username uniqueness
        existing_user = self.db.query(User).filter(User.username == username).first()
        if existing_user:
            logger.warning(f"User creation failed: Username '{username}' already exists")
            raise ValidationError(
                f"Username '{username}' already exists",
                error_code="USERNAME_EXISTS"
            )
        
        # Validate role
        valid_roles = ['super_admin', 'event_admin', 'booth_cashier', 'issuer', 'reviewer']
        if role not in valid_roles:
            logger.warning(f"User creation failed: Invalid role '{role}'")
            raise ValidationError(
                f"Invalid role '{role}'. Must be one of: {', '.join(valid_roles)}",
                error_code="INVALID_ROLE"
            )
        
        # Validate booth_id for booth_cashier role
        if role == 'booth_cashier':
            if booth_id is None:
                logger.warning(f"User creation failed: booth_cashier requires booth_id")
                raise ValidationError(
                    "booth_id is required for booth_cashier role",
                    error_code="BOOTH_ID_REQUIRED"
                )
            
            # Verify booth exists
            booth = self.db.query(Booth).filter(Booth.id == booth_id).first()
            if booth is None:
                logger.warning(f"User creation failed: Booth {booth_id} not found")
                raise ResourceNotFoundError(
                    f"Booth with id {booth_id} not found",
                    error_code="BOOTH_NOT_FOUND"
                )
        else:
            # Non-booth_cashier roles should not have booth_id
            if booth_id is not None:
                logger.warning(f"User creation failed: Role '{role}' should not have booth_id")
                raise ValidationError(
                    f"booth_id should only be set for booth_cashier role, not for '{role}'",
                    error_code="BOOTH_ID_NOT_ALLOWED"
                )
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user
        user = User(
            username=username,
            password_hash=password_hash,
            role=role,
            booth_id=booth_id,
            status='active'
        )
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            logger.info(
                f"User created: id={user.id}, username='{username}', "
                f"role='{role}', booth_id={booth_id}"
            )
            return user
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create user '{username}': {str(e)}")
            raise ValidationError(
                f"Failed to create user: {str(e)}",
                error_code="USER_CREATION_FAILED"
            )
    
    def get_user(self, user_id: int) -> User:
        """
        获取用户详情。
        
        Args:
            user_id: 用户ID
            
        Returns:
            User: 用户对象
            
        Raises:
            UserNotFoundError: 用户不存在
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if user is None:
            logger.warning(f"User not found: id={user_id}")
            raise UserNotFoundError(
                f"User with id {user_id} not found",
                error_code="USER_NOT_FOUND"
            )
        
        logger.debug(f"User retrieved: id={user_id}, username='{user.username}'")
        return user
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        根据用户名获取用户。
        
        Args:
            username: 用户名
            
        Returns:
            User: 用户对象，如果不存在返回 None
        """
        user = self.db.query(User).filter(User.username == username).first()
        
        if user:
            logger.debug(f"User found by username: '{username}', id={user.id}")
        else:
            logger.debug(f"User not found by username: '{username}'")
        
        return user
    
    def list_users(
        self,
        role: Optional[str] = None,
        booth_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[User]:
        """
        列出用户。
        
        支持按角色、摊位ID、状态过滤。
        
        Args:
            role: 过滤角色（可选）
            booth_id: 过滤摊位ID（可选）
            status: 过滤状态（可选）
            
        Returns:
            List[User]: 用户列表
        """
        query = self.db.query(User)
        
        # Apply filters
        if role:
            query = query.filter(User.role == role)
        
        if booth_id is not None:
            query = query.filter(User.booth_id == booth_id)
        
        if status:
            query = query.filter(User.status == status)
        
        users = query.all()
        
        logger.info(
            f"Users listed: count={len(users)}, "
            f"filters=(role={role}, booth_id={booth_id}, status={status})"
        )
        
        return users
    
    def update_user_status(self, user_id: int, status: str) -> User:
        """
        更新用户状态。
        
        Args:
            user_id: 用户ID
            status: 新状态 (active, inactive, blocked)
            
        Returns:
            User: 更新后的用户对象
            
        Raises:
            UserNotFoundError: 用户不存在
            ValidationError: 状态值无效
        """
        # Validate status
        valid_statuses = ['active', 'inactive', 'blocked']
        if status not in valid_statuses:
            logger.warning(f"Invalid status: '{status}'")
            raise ValidationError(
                f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}",
                error_code="INVALID_STATUS"
            )
        
        # Get user
        user = self.get_user(user_id)
        
        # Update status
        old_status = user.status
        user.status = status
        
        try:
            self.db.commit()
            self.db.refresh(user)
            logger.info(
                f"User status updated: id={user_id}, "
                f"username='{user.username}', "
                f"old_status='{old_status}', new_status='{status}'"
            )
            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update user status: {str(e)}")
            raise ValidationError(
                f"Failed to update user status: {str(e)}",
                error_code="STATUS_UPDATE_FAILED"
            )
    
    def user_exists(self, username: str) -> bool:
        """
        检查用户名是否存在。
        
        Args:
            username: 用户名
            
        Returns:
            bool: 用户名是否存在
        """
        count = self.db.query(User).filter(User.username == username).count()
        exists = count > 0
        logger.debug(f"User existence check: username='{username}', exists={exists}")
        return exists
