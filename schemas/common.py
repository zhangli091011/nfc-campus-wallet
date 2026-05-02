"""
通用 DTO 模型 for NFC Campus E-Wallet System.

定义通用的请求/响应模型。
"""

from pydantic import BaseModel
from typing import Optional, Any


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error_code: str
    message: str
    field: Optional[str] = None
    value: Optional[Any] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "USER_NOT_FOUND",
                "message": "User with UID 'A1B2C3D4' does not exist"
            }
        }


class SuccessResponse(BaseModel):
    """成功响应基类"""
    success: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True
            }
        }
