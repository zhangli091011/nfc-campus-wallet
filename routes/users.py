"""
Users routes for Booth Management System.

提供用户管理相关的 API 端点。
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from typing import Optional, List
import logging

from core.database import get_db
from core.security import get_current_user, RoleChecker
from services.user_service import UserService
from schemas.user import UserCreate, UserResponse
from models.user import User
from core.exceptions import (
    UserNotFoundError,
    ValidationError,
    ResourceNotFoundError
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin"])),
    db: Session = Depends(get_db)
):
    """
    创建新用户账户。
    
    仅 super_admin 可以创建用户。
    
    Request Body:
        - username: 用户名（必填，1-50字符，唯一）
        - password: 密码（必填，6-100字符）
        - role: 用户角色（必填：super_admin, event_admin, booth_cashier, issuer, reviewer）
        - booth_id: 关联摊位ID（booth_cashier 必填，其他角色不允许）
    
    Returns:
        UserResponse: 创建的用户信息
        
    Error Responses:
        400: 验证错误（用户名已存在、角色无效、booth_id 不匹配等）
        401: 未认证
        403: 权限不足（非 super_admin）
        500: 内部服务器错误
    
    Example:
        POST /users
        {
            "username": "cashier01",
            "password": "password123",
            "role": "booth_cashier",
            "booth_id": 1
        }
    
    Validates Requirements:
        - Requirement 3.1: Store user records with required fields
        - Requirement 3.2: Assign unique auto-incrementing id
        - Requirement 3.3: Enforce unique usernames
        - Requirement 3.4: Support valid role values
        - Requirement 3.6: booth_cashier must have valid booth_id
        - Requirement 3.7: Non-booth_cashier roles allow null booth_id
        - Requirement 3.9: Hash passwords using secure algorithm
    """
    try:
        user_service = UserService(db)
        
        user = user_service.create_user(
            username=user_data.username,
            password=user_data.password,
            role=user_data.role.value,
            booth_id=user_data.booth_id
        )
        
        logger.info(
            f"User created successfully: id={user.id}, username='{user.username}', "
            f"role='{user.role}', created_by={current_user.username}"
        )
        
        return UserResponse.model_validate(user)
    
    except ValidationError as e:
        logger.warning(f"User creation validation failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except ResourceNotFoundError as e:
        logger.warning(f"User creation failed - resource not found: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in user creation: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    role: Optional[str] = Query(None, description="Filter by role"),
    booth_id: Optional[int] = Query(None, description="Filter by booth ID"),
    status: Optional[str] = Query(None, description="Filter by status (active/inactive/blocked)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of users to return"),
    offset: int = Query(0, ge=0, description="Number of users to skip"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin"])),
    db: Session = Depends(get_db)
):
    """
    获取用户列表，支持角色、摊位和状态过滤。
    
    仅 super_admin 可以查看用户列表。
    
    Query Parameters:
        - role: 角色过滤（可选）
        - booth_id: 摊位ID过滤（可选）
        - status: 状态过滤（可选）
        - limit: 返回记录数限制（默认100，最大1000）
        - offset: 偏移量（默认0）
    
    Returns:
        List[UserResponse]: 用户列表
        
    Error Responses:
        401: 未认证
        403: 权限不足（非 super_admin）
        500: 内部服务器错误
    
    Example:
        GET /users?role=booth_cashier&status=active&limit=10&offset=0
    
    Validates Requirements:
        - Requirement 3.1: Query user records
    """
    try:
        user_service = UserService(db)
        
        users = user_service.list_users(
            role=role,
            booth_id=booth_id,
            status=status
        )
        
        # Apply pagination
        total_count = len(users)
        users = users[offset:offset + limit]
        
        logger.info(
            f"Users listed: count={len(users)}, total={total_count}, "
            f"role={role}, booth_id={booth_id}, status={status}, "
            f"requested_by={current_user.username}"
        )
        
        return [UserResponse.model_validate(user) for user in users]
    
    except Exception as e:
        logger.error(
            f"Unexpected error in user listing: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin"])),
    db: Session = Depends(get_db)
):
    """
    获取用户详情。
    
    仅 super_admin 可以查看用户详情。
    
    Path Parameters:
        - user_id: 用户ID
    
    Returns:
        UserResponse: 用户详细信息
        
    Error Responses:
        401: 未认证
        403: 权限不足（非 super_admin）
        404: 用户不存在
        500: 内部服务器错误
    
    Example:
        GET /users/1
    
    Validates Requirements:
        - Requirement 3.1: Query user records
    """
    try:
        user_service = UserService(db)
        
        user = user_service.get_user(user_id)
        
        logger.info(
            f"User retrieved: id={user_id}, username='{user.username}', "
            f"requested_by={current_user.username}"
        )
        
        return UserResponse.model_validate(user)
    
    except UserNotFoundError as e:
        logger.warning(f"User not found: {user_id}")
        return JSONResponse(
            status_code=404,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in user retrieval: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )


@router.patch("/users/{user_id}/booth", response_model=UserResponse)
async def update_user_booth(
    user_id: int,
    booth_id: Optional[int] = Query(None, description="New booth ID (null to unassign)"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin"])),
    db: Session = Depends(get_db)
):
    """
    更新用户关联的摊位。
    
    仅 super_admin 可以更新用户摊位。
    如果用户角色不是 booth_cashier，会自动将角色改为 booth_cashier。
    如果 booth_id 为 null，则取消摊位关联并将角色改为 event_admin。
    
    Path Parameters:
        - user_id: 用户ID
    
    Query Parameters:
        - booth_id: 新摊位ID（null 表示取消关联）
    
    Returns:
        UserResponse: 更新后的用户信息
    """
    try:
        user_service = UserService(db)
        user = user_service.get_user(user_id)
        
        if booth_id is not None:
            # 验证摊位存在
            from models.booth import Booth
            booth = db.query(Booth).filter(Booth.id == booth_id).first()
            if booth is None:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error_code": "BOOTH_NOT_FOUND",
                        "message": f"Booth with id {booth_id} not found"
                    }
                )
            user.booth_id = booth_id
            # bank_clerk 是特殊角色，分配摊位时不改变其角色
            if user.role != 'bank_clerk':
                user.role = 'booth_cashier'
        else:
            user.booth_id = None
            # 如果取消摊位关联且当前是 booth_cashier，改为 event_admin
            # bank_clerk 取消摊位关联时保持角色不变
            if user.role == 'booth_cashier':
                user.role = 'event_admin'
        
        db.commit()
        db.refresh(user)
        
        logger.info(
            f"User booth updated: id={user_id}, username='{user.username}', "
            f"booth_id={booth_id}, updated_by={current_user.username}"
        )
        
        return UserResponse.model_validate(user)
    
    except UserNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error_code": e.error_code, "message": e.message}
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in user booth update: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "An internal error occurred."}
        )


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role: str = Query(..., description="New role (super_admin/event_admin/booth_cashier/issuer/reviewer/bank_clerk)"),
    booth_id: Optional[int] = Query(None, description="Booth ID (required for booth_cashier)"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin"])),
    db: Session = Depends(get_db)
):
    """
    更新用户角色。
    
    仅 super_admin 可以更新用户角色。
    如果新角色是 booth_cashier，必须同时提供 booth_id。
    如果新角色不是 booth_cashier，booth_id 将被清除。
    
    Path Parameters:
        - user_id: 用户ID
    
    Query Parameters:
        - role: 新角色
        - booth_id: 摊位ID（booth_cashier 必填）
    
    Returns:
        UserResponse: 更新后的用户信息
    """
    try:
        valid_roles = ['super_admin', 'event_admin', 'booth_cashier', 'issuer', 'reviewer', 'bank_clerk', 'school_inspector']
        if role not in valid_roles:
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "INVALID_ROLE",
                    "message": f"Invalid role '{role}'. Must be one of: {', '.join(valid_roles)}"
                }
            )
        
        user_service = UserService(db)
        user = user_service.get_user(user_id)
        
        # 不允许修改自己的角色
        if user.id == current_user.id:
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "CANNOT_CHANGE_OWN_ROLE",
                    "message": "Cannot change your own role"
                }
            )
        
        # booth_cashier 需要 booth_id
        if role == 'booth_cashier':
            if booth_id is None:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error_code": "BOOTH_ID_REQUIRED",
                        "message": "booth_id is required for booth_cashier role"
                    }
                )
            from models.booth import Booth
            booth = db.query(Booth).filter(Booth.id == booth_id).first()
            if booth is None:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error_code": "BOOTH_NOT_FOUND",
                        "message": f"Booth with id {booth_id} not found"
                    }
                )
            user.booth_id = booth_id
        else:
            # 非 booth_cashier 角色清除 booth_id
            user.booth_id = None
        
        old_role = user.role
        user.role = role
        db.commit()
        db.refresh(user)
        
        logger.info(
            f"User role updated: id={user_id}, username='{user.username}', "
            f"old_role='{old_role}', new_role='{role}', updated_by={current_user.username}"
        )
        
        return UserResponse.model_validate(user)
    
    except UserNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error_code": e.error_code, "message": e.message}
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in user role update: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "An internal error occurred."}
        )


@router.patch("/users/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: int,
    status: str = Query(..., description="New status (active/inactive/blocked)"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin"])),
    db: Session = Depends(get_db)
):
    """
    更新用户状态。
    
    仅 super_admin 可以更新用户状态。
    
    Path Parameters:
        - user_id: 用户ID
    
    Query Parameters:
        - status: 新状态（active/inactive/blocked）
    
    Returns:
        UserResponse: 更新后的用户信息
        
    Error Responses:
        400: 验证错误（状态值无效）
        401: 未认证
        403: 权限不足（非 super_admin）
        404: 用户不存在
        500: 内部服务器错误
    
    Example:
        PATCH /users/1/status?status=inactive
    
    Validates Requirements:
        - Requirement 3.5: Support user status values
    """
    try:
        user_service = UserService(db)
        
        user = user_service.update_user_status(user_id, status)
        
        logger.info(
            f"User status updated: id={user_id}, username='{user.username}', "
            f"new_status='{status}', updated_by={current_user.username}"
        )
        
        return UserResponse.model_validate(user)
    
    except UserNotFoundError as e:
        logger.warning(f"User not found: {user_id}")
        return JSONResponse(
            status_code=404,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except ValidationError as e:
        logger.warning(f"User status update validation failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in user status update: {str(e)}",
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
# 批量创建收银员账号
# ============================================================================

from pydantic import BaseModel, Field
from typing import List
import random
import string
import secrets


class BatchCreateCashiersRequest(BaseModel):
    """批量创建收银员请求"""
    booth_ids: List[int] = Field(..., min_length=1, description="要分配的摊位ID列表")
    accounts_per_booth: int = Field(1, ge=1, le=10, description="每个摊位创建的账号数量")
    username_prefix: str = Field("cashier", max_length=20, description="用户名前缀")
    password_length: int = Field(8, ge=6, le=20, description="随机密码长度")


class CashierAccountInfo(BaseModel):
    """收银员账号信息"""
    user_id: int
    username: str
    password: str  # 原始密码（仅在创建时返回一次）
    booth_id: int
    booth_name: str


class BatchCreateCashiersResponse(BaseModel):
    """批量创建响应"""
    success: bool
    total_created: int
    accounts: List[CashierAccountInfo]
    errors: List[str] = []


def _generate_random_password(length: int = 8) -> str:
    """生成随机密码（包含字母和数字）"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _generate_username(prefix: str, booth_id: int, index: int, db: Session) -> str:
    """生成唯一用户名"""
    from models.user import User as UserModel
    # 格式：cashier_b<boothId>_<index>
    base = f"{prefix}_b{booth_id}"
    if index > 1:
        base = f"{base}_{index}"
    
    # 如果已存在，追加随机后缀
    existing = db.query(UserModel).filter(UserModel.username == base).first()
    if existing:
        suffix = ''.join(secrets.choice(string.digits) for _ in range(4))
        base = f"{base}_{suffix}"
    
    return base


@router.post("/users/batch-create-cashiers", response_model=BatchCreateCashiersResponse)
async def batch_create_cashiers(
    req: BatchCreateCashiersRequest,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin"])),
    db: Session = Depends(get_db)
):
    """
    批量创建摊位收银员账号。

    为指定的每个摊位创建N个收银员账号，自动生成用户名和随机密码。
    返回所有新账号的登录信息（明文密码仅返回一次，请妥善保存）。

    Request Body:
        - booth_ids: 摊位ID列表
        - accounts_per_booth: 每个摊位创建账号数（默认1）
        - username_prefix: 用户名前缀（默认"cashier"）
        - password_length: 随机密码长度（默认8）
    """
    from models.booth import Booth
    from services.user_service import UserService

    user_service = UserService(db)
    created_accounts = []
    errors = []

    # 验证所有摊位存在
    booths = db.query(Booth).filter(Booth.id.in_(req.booth_ids)).all()
    booth_map = {b.id: b for b in booths}
    missing = [bid for bid in req.booth_ids if bid not in booth_map]
    if missing:
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": f"摊位不存在: {missing}"
            }
        )

    # 批量创建
    for booth_id in req.booth_ids:
        booth = booth_map[booth_id]
        for i in range(1, req.accounts_per_booth + 1):
            try:
                username = _generate_username(req.username_prefix, booth_id, i, db)
                password = _generate_random_password(req.password_length)

                user = user_service.create_user(
                    username=username,
                    password=password,
                    role="booth_cashier",
                    booth_id=booth_id
                )

                created_accounts.append(CashierAccountInfo(
                    user_id=user.id,
                    username=username,
                    password=password,
                    booth_id=booth_id,
                    booth_name=booth.name,
                ))

                logger.info(
                    f"Batch created cashier: username={username}, booth_id={booth_id}, "
                    f"by={current_user.username}"
                )

            except Exception as e:
                error_msg = f"摊位 {booth.name}(ID={booth_id}) 第{i}个账号创建失败: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg, exc_info=True)

    return BatchCreateCashiersResponse(
        success=len(created_accounts) > 0,
        total_created=len(created_accounts),
        accounts=created_accounts,
        errors=errors,
    )
