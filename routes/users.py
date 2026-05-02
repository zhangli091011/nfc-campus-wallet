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
