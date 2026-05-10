"""
商户相关 DTO 模型 for NFC Campus E-Wallet System.

定义商户注册、登录、商铺信息管理相关的请求/响应模型。
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class MerchantRegisterRequest(BaseModel):
    """商户注册请求模型"""
    username: str = Field(..., min_length=3, max_length=50, description="登录用户名")
    password: str = Field(..., min_length=6, max_length=100, description="登录密码")
    booth_name: str = Field(..., min_length=1, max_length=100, description="商铺名称")
    class_name: str = Field(..., min_length=1, max_length=100, description="班级名称")
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        """验证用户名格式：只允许字母、数字、下划线"""
        if not v.replace("_", "").isalnum():
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "merchant_01",
                "password": "password123",
                "booth_name": "美食小铺",
                "class_name": "高一(3)班"
            }
        }


class MerchantLoginRequest(BaseModel):
    """商户登录请求模型"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, max_length=100, description="密码")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "merchant_01",
                "password": "password123"
            }
        }


class MerchantProductCreate(BaseModel):
    """商户添加商品请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="商品名称")
    price: float = Field(..., gt=0, description="商品定价（元）")
    cost_price: Optional[float] = Field(None, ge=0, description="成本价（元，可选）")
    stock: Optional[int] = Field(None, ge=0, description="库存数量（可选，不填表示无限）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "珍珠奶茶",
                "price": 8.00,
                "cost_price": 3.50,
                "stock": 50
            }
        }


class MerchantProductUpdate(BaseModel):
    """商户更新商品请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="商品名称")
    price: Optional[float] = Field(None, gt=0, description="商品定价（元）")
    cost_price: Optional[float] = Field(None, ge=0, description="成本价（元）")
    stock: Optional[int] = Field(None, ge=0, description="库存数量")
    enabled: Optional[bool] = Field(None, description="是否上架")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "珍珠奶茶（大杯）",
                "price": 10.00,
                "stock": 30,
                "enabled": True
            }
        }


class MerchantProductResponse(BaseModel):
    """商户商品响应模型"""
    id: int
    name: str
    price: float = Field(..., description="商品定价（元）")
    cost_price: Optional[float] = Field(None, description="成本价（元）")
    stock: Optional[int] = Field(None, description="库存数量")
    enabled: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "珍珠奶茶",
                "price": 8.00,
                "cost_price": 3.50,
                "stock": 50,
                "enabled": True,
                "created_at": "2026-05-10T08:00:00Z"
            }
        }


class MerchantBoothInfoResponse(BaseModel):
    """商户商铺信息响应模型"""
    booth_id: int
    booth_name: str
    class_name: str
    status: str
    event_id: int
    created_at: datetime
    products: List[MerchantProductResponse] = []
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "booth_id": 1,
                "booth_name": "美食小铺",
                "class_name": "高一(3)班",
                "status": "active",
                "event_id": 1,
                "created_at": "2026-05-10T08:00:00Z",
                "products": []
            }
        }


class MerchantBoothUpdateRequest(BaseModel):
    """商户更新商铺信息请求模型"""
    booth_name: Optional[str] = Field(None, min_length=1, max_length=100, description="商铺名称")
    class_name: Optional[str] = Field(None, min_length=1, max_length=100, description="班级名称")
    
    class Config:
        json_schema_extra = {
            "example": {
                "booth_name": "美食小铺（新名称）",
                "class_name": "高一(3)班"
            }
        }


class MerchantIncomeResponse(BaseModel):
    """商户收入统计响应模型"""
    booth_id: int
    booth_name: str
    total_income: float = Field(..., description="总收入（元）")
    total_transactions: int = Field(..., description="总交易笔数")
    today_income: float = Field(..., description="今日收入（元）")
    today_transactions: int = Field(..., description="今日交易笔数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "booth_id": 1,
                "booth_name": "美食小铺",
                "total_income": 1250.50,
                "total_transactions": 85,
                "today_income": 320.00,
                "today_transactions": 22
            }
        }


class MerchantTransactionItem(BaseModel):
    """商户交易记录项"""
    id: int
    type: str
    amount: float = Field(..., description="交易金额（元）")
    product_name: Optional[str] = Field(None, description="商品名称")
    remark: Optional[str] = None
    created_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 12345,
                "type": "pay",
                "amount": 8.00,
                "product_name": "珍珠奶茶",
                "remark": "购买奶茶",
                "created_at": "2026-05-10T10:30:00Z"
            }
        }


class MerchantTransactionHistoryResponse(BaseModel):
    """商户交易历史响应模型"""
    transactions: List[MerchantTransactionItem]
    total_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "transactions": [
                    {
                        "id": 12345,
                        "type": "pay",
                        "amount": 8.00,
                        "product_name": "珍珠奶茶",
                        "remark": None,
                        "created_at": "2026-05-10T10:30:00Z"
                    }
                ],
                "total_count": 1
            }
        }


class MerchantTokenResponse(BaseModel):
    """商户登录令牌响应模型"""
    access_token: str = Field(..., description="JWT 访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    merchant: "MerchantInfoResponse" = Field(..., description="商户信息")


class MerchantInfoResponse(BaseModel):
    """商户基本信息响应"""
    user_id: int
    username: str
    booth_id: int
    booth_name: str
    class_name: str
    status: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 10,
                "username": "merchant_01",
                "booth_id": 1,
                "booth_name": "美食小铺",
                "class_name": "高一(3)班",
                "status": "active"
            }
        }


# 解决前向引用
MerchantTokenResponse.model_rebuild()
