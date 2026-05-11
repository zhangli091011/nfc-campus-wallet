"""
Authentication routes for Booth Management System.

提供用户认证相关的 API 端点。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
import logging

from core.database import get_db
from core.security import get_current_user
from services.auth_service import AuthService, AuthenticationError
from schemas.user import UserLogin, TokenResponse, UserResponse, SetStaffNameRequest, SetStaffNameResponse
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    用户登录，返回 JWT 访问令牌。
    
    Request Body:
        - username: 用户名（必填）
        - password: 密码（必填）
    
    Returns:
        TokenResponse: JWT 令牌和用户信息
        
    Error Responses:
        401: 认证失败（用户名或密码错误、用户被封禁）
        500: 内部服务器错误
    
    Example:
        POST /auth/login
        {
            "username": "admin",
            "password": "password123"
        }
        
        Response:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "user": {
                "id": 1,
                "username": "admin",
                "role": "super_admin",
                "booth_id": null,
                "status": "active",
                "created_at": "2024-02-01T10:00:00Z"
            }
        }
    
    Validates Requirements:
        - Requirement 4.1: POST /auth/login returns JWT token for valid credentials
        - Requirement 4.2: POST /auth/login returns 401 for invalid credentials
        - Requirement 4.3: Include user_id, username, and role in JWT token payload
    """
    try:
        auth_service = AuthService(db)
        
        result = auth_service.login(
            username=credentials.username,
            password=credentials.password
        )
        
        logger.info(
            f"User logged in successfully: username='{credentials.username}', "
            f"role='{result['user']['role']}'"
        )
        
        return TokenResponse(
            access_token=result['access_token'],
            token_type=result['token_type'],
            user=UserResponse.model_validate(result['user'])
        )
    
    except AuthenticationError as e:
        logger.warning(
            f"Login failed: username='{credentials.username}', reason={e.message}"
        )
        return JSONResponse(
            status_code=401,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in login: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前认证用户的信息。
    
    需要在 Authorization header 中提供有效的 JWT 令牌。
    
    Headers:
        - Authorization: Bearer <jwt_token>
    
    Returns:
        UserResponse: 当前用户信息
        
    Error Responses:
        401: 未认证（令牌缺失、无效或过期）
        403: 用户被封禁或未激活
        500: 内部服务器错误
    
    Example:
        GET /auth/me
        Headers: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        
        Response:
        {
            "id": 1,
            "username": "admin",
            "role": "super_admin",
            "booth_id": null,
            "status": "active",
            "created_at": "2024-02-01T10:00:00Z"
        }
    
    Validates Requirements:
        - Requirement 4.6: GET /auth/me returns current user information
        - Requirement 4.7: Invalid or expired JWT token returns 401 error
        - Requirement 12.7: Extract user information from JWT token
    """
    try:
        logger.info(
            f"Current user info retrieved: username='{current_user.username}', "
            f"role='{current_user.role}'"
        )
        
        return UserResponse.model_validate(current_user)
    
    except Exception as e:
        logger.error(
            f"Unexpected error in get current user: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )


@router.post("/auth/set-staff-name", response_model=SetStaffNameResponse)
async def set_staff_name(
    request: SetStaffNameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    设置工作人员姓名（首次登录后调用）。
    
    工作人员首次登录后，需要输入真实姓名。
    姓名设置后将用于显示和记录。
    
    Headers:
        - Authorization: Bearer <jwt_token>
    
    Request Body:
        - staff_name: 工作人员真实姓名（1-50字符）
    
    Returns:
        SetStaffNameResponse: 设置成功的确认信息
        
    Error Responses:
        401: 未认证
        400: 姓名无效
        500: 内部服务器错误
    """
    try:
        staff_name = request.staff_name.strip()
        
        if not staff_name:
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "INVALID_STAFF_NAME",
                    "message": "工作人员姓名不能为空"
                }
            )
        
        # Update staff_name in database
        current_user.staff_name = staff_name
        db.commit()
        db.refresh(current_user)
        
        logger.info(
            f"Staff name set: user_id={current_user.id}, "
            f"username='{current_user.username}', staff_name='{staff_name}'"
        )
        
        return SetStaffNameResponse(
            message="Staff name set successfully",
            staff_name=staff_name
        )
    
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error setting staff name: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )
