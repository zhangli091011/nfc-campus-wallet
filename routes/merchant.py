"""
Merchant routes for NFC Campus E-Wallet System.

商户子路由：提供商户注册、登录、商铺信息管理、收入查看、交易记录等 API 端点。
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from core.database import get_db
from core.security import get_current_user, RoleChecker
from services.merchant_service import (
    MerchantService,
    UsernameExistsError,
    MerchantAuthError,
    MerchantNotFoundError,
    ProductNotFoundError
)
from schemas.merchant import (
    MerchantRegisterRequest,
    MerchantLoginRequest,
    MerchantProductCreate,
    MerchantProductUpdate,
    MerchantProductResponse,
    MerchantBoothInfoResponse,
    MerchantBoothUpdateRequest,
    MerchantIncomeResponse,
    MerchantTransactionHistoryResponse,
    MerchantTokenResponse,
)
from models.user import User
from core.exceptions import BusinessException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/merchant", tags=["merchant"])


# ============================================================================
# 商户注册与登录
# ============================================================================


@router.post("/register", response_model=MerchantTokenResponse, status_code=201)
async def merchant_register(
    request: MerchantRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    商户注册。
    
    创建商户账号并自动创建关联的商铺，注册成功后直接返回登录令牌。
    
    Request Body:
        - username: 登录用户名（3-50字符，字母数字下划线）
        - password: 登录密码（6-100字符）
        - booth_name: 商铺名称（1-100字符）
        - class_name: 班级名称（1-100字符）
    
    Returns:
        MerchantTokenResponse: JWT 令牌和商户信息
        
    Error Responses:
        400: 用户名已存在 / 没有激活的活动
        500: 内部服务器错误
    
    Example:
        POST /merchant/register
        {
            "username": "merchant_01",
            "password": "password123",
            "booth_name": "美食小铺",
            "class_name": "高一(3)班"
        }
    """
    try:
        merchant_service = MerchantService(db)
        
        result = merchant_service.register(
            username=request.username,
            password=request.password,
            booth_name=request.booth_name,
            class_name=request.class_name
        )
        
        logger.info(f"Merchant registered: username='{request.username}', booth='{request.booth_name}'")
        
        return result
    
    except UsernameExistsError as e:
        return JSONResponse(
            status_code=400,
            content={"error_code": e.error_code, "message": e.message}
        )
    
    except BusinessException as e:
        return JSONResponse(
            status_code=400,
            content={"error_code": e.error_code, "message": e.message}
        )
    
    except Exception as e:
        logger.error(f"Merchant registration error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "注册失败，请稍后重试"}
        )


@router.post("/login", response_model=MerchantTokenResponse)
async def merchant_login(
    request: MerchantLoginRequest,
    db: Session = Depends(get_db)
):
    """
    商户登录。
    
    验证商户凭据并返回 JWT 令牌。
    
    Request Body:
        - username: 用户名
        - password: 密码
    
    Returns:
        MerchantTokenResponse: JWT 令牌和商户信息
        
    Error Responses:
        401: 用户名或密码错误 / 账户被封禁
        500: 内部服务器错误
    
    Example:
        POST /merchant/login
        {
            "username": "merchant_01",
            "password": "password123"
        }
    """
    try:
        merchant_service = MerchantService(db)
        
        result = merchant_service.login(
            username=request.username,
            password=request.password
        )
        
        logger.info(f"Merchant logged in: username='{request.username}'")
        
        return result
    
    except MerchantAuthError as e:
        return JSONResponse(
            status_code=401,
            content={"error_code": e.error_code, "message": e.message}
        )
    
    except MerchantNotFoundError as e:
        return JSONResponse(
            status_code=401,
            content={"error_code": e.error_code, "message": e.message}
        )
    
    except Exception as e:
        logger.error(f"Merchant login error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "登录失败，请稍后重试"}
        )


# ============================================================================
# 找回密码
# ============================================================================

from pydantic import BaseModel as PydanticBaseModel


class MerchantRecoverPasswordRequest(PydanticBaseModel):
    """商户找回密码请求"""
    booth_id: int
    new_password: str


@router.get("/booths-public")
async def get_merchant_booths_public(
    db: Session = Depends(get_db)
):
    """
    获取所有商户摊位列表（公开接口，用于找回密码时选择摊位）。
    
    无需认证。返回摊位ID、名称、班级、关联用户名。
    
    Returns:
        摊位列表
    """
    from models.booth import Booth
    from models.user import User as UserModel
    
    booths = db.query(Booth).filter(Booth.status == 'active').order_by(Booth.id).all()
    
    result = []
    for booth in booths:
        # 查找关联的商户用户
        merchant_user = db.query(UserModel).filter(
            UserModel.booth_id == booth.id,
            UserModel.role == 'merchant'
        ).first()
        
        result.append({
            "booth_id": booth.id,
            "booth_name": booth.name,
            "class_name": booth.class_name or "",
            "username": merchant_user.username if merchant_user else None,
        })
    
    return {"booths": result, "total": len(result)}


@router.post("/recover-password")
async def merchant_recover_password(
    request: MerchantRecoverPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    商户找回密码。
    
    通过摊位ID定位商户，直接重置密码。
    
    Request Body:
        - booth_id: 摊位ID
        - new_password: 新密码（6-100字符）
    
    Returns:
        成功消息
        
    Error Responses:
        400: 验证失败
        500: 内部服务器错误
    """
    try:
        merchant_service = MerchantService(db)
        result = merchant_service.recover_password_by_booth(
            booth_id=request.booth_id,
            new_password=request.new_password
        )
        return result
    
    except MerchantAuthError as e:
        return JSONResponse(
            status_code=400,
            content={"error_code": e.error_code, "message": e.message}
        )
    
    except Exception as e:
        logger.error(f"Merchant recover password error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "密码重置失败，请稍后重试"}
        )


# ============================================================================
# 商铺信息管理
# ============================================================================


@router.get("/booth", response_model=MerchantBoothInfoResponse)
async def get_merchant_booth(
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["merchant"])),
    db: Session = Depends(get_db)
):
    """
    获取当前商户的商铺信息（含商品列表）。
    
    需要商户角色认证。
    
    Returns:
        MerchantBoothInfoResponse: 商铺信息和商品列表
        
    Error Responses:
        401: 未认证
        403: 权限不足（非商户角色）
        404: 商铺不存在
    """
    try:
        merchant_service = MerchantService(db)
        result = merchant_service.get_booth_info(current_user)
        return result
    
    except MerchantNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error_code": e.error_code, "message": e.message}
        )
    
    except Exception as e:
        logger.error(f"Get merchant booth error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "获取商铺信息失败"}
        )


@router.put("/booth", response_model=MerchantBoothInfoResponse)
async def update_merchant_booth(
    request: MerchantBoothUpdateRequest,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["merchant"])),
    db: Session = Depends(get_db)
):
    """
    更新商铺信息（商铺名称、班级）。
    
    需要商户角色认证。
    
    Request Body:
        - booth_name: 新商铺名称（可选）
        - class_name: 新班级名称（可选）
    
    Returns:
        更新后的商铺信息
    """
    try:
        merchant_service = MerchantService(db)
        result = merchant_service.update_booth_info(
            user=current_user,
            booth_name=request.booth_name,
            class_name=request.class_name
        )
        return result
    
    except MerchantNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error_code": e.error_code, "message": e.message}
        )
    
    except Exception as e:
        logger.error(f"Update merchant booth error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "更新商铺信息失败"}
        )


# ============================================================================
# 商品管理
# ============================================================================


@router.post("/products", response_model=MerchantProductResponse, status_code=201)
async def add_merchant_product(
    request: MerchantProductCreate,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["merchant"])),
    db: Session = Depends(get_db)
):
    """
    添加商品到商铺。
    
    需要商户角色认证。
    
    Request Body:
        - name: 商品名称
        - price: 商品定价（元）
        - cost_price: 成本价（元，可选）
        - stock: 库存数量（可选，不填表示无限）
    
    Returns:
        MerchantProductResponse: 创建的商品信息
    """
    try:
        merchant_service = MerchantService(db)
        result = merchant_service.add_product(
            user=current_user,
            name=request.name,
            price=request.price,
            cost_price=request.cost_price,
            stock=request.stock
        )
        return result
    
    except MerchantNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error_code": e.error_code, "message": e.message}
        )
    
    except Exception as e:
        logger.error(f"Add merchant product error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "添加商品失败"}
        )


@router.put("/products/{product_id}", response_model=MerchantProductResponse)
async def update_merchant_product(
    product_id: int,
    request: MerchantProductUpdate,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["merchant"])),
    db: Session = Depends(get_db)
):
    """
    更新商品信息。
    
    需要商户角色认证，只能更新自己商铺的商品。
    
    Path Parameters:
        - product_id: 商品ID
    
    Request Body:
        - name: 商品名称（可选）
        - price: 商品定价（元，可选）
        - cost_price: 成本价（元，可选）
        - stock: 库存数量（可选）
        - enabled: 是否上架（可选）
    
    Returns:
        MerchantProductResponse: 更新后的商品信息
    """
    try:
        merchant_service = MerchantService(db)
        result = merchant_service.update_product(
            user=current_user,
            product_id=product_id,
            name=request.name,
            price=request.price,
            cost_price=request.cost_price,
            stock=request.stock,
            enabled=request.enabled
        )
        return result
    
    except ProductNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error_code": e.error_code, "message": e.message}
        )
    
    except Exception as e:
        logger.error(f"Update merchant product error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "更新商品失败"}
        )


@router.delete("/products/{product_id}", status_code=204)
async def delete_merchant_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["merchant"])),
    db: Session = Depends(get_db)
):
    """
    删除商品。
    
    需要商户角色认证，只能删除自己商铺的商品。
    
    Path Parameters:
        - product_id: 商品ID
    """
    try:
        merchant_service = MerchantService(db)
        merchant_service.delete_product(user=current_user, product_id=product_id)
        return None
    
    except ProductNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error_code": e.error_code, "message": e.message}
        )
    
    except Exception as e:
        logger.error(f"Delete merchant product error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "删除商品失败"}
        )


# ============================================================================
# 收入与交易记录
# ============================================================================


@router.get("/income", response_model=MerchantIncomeResponse)
async def get_merchant_income(
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["merchant"])),
    db: Session = Depends(get_db)
):
    """
    获取商户收入统计。
    
    返回总收入、总交易笔数、今日收入、今日交易笔数。
    
    需要商户角色认证。
    
    Returns:
        MerchantIncomeResponse: 收入统计信息
    """
    try:
        merchant_service = MerchantService(db)
        result = merchant_service.get_income_stats(current_user)
        return result
    
    except MerchantNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error_code": e.error_code, "message": e.message}
        )
    
    except Exception as e:
        logger.error(f"Get merchant income error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "获取收入统计失败"}
        )


@router.get("/transactions", response_model=MerchantTransactionHistoryResponse)
async def get_merchant_transactions(
    limit: int = Query(50, ge=1, le=500, description="返回记录数限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["merchant"])),
    db: Session = Depends(get_db)
):
    """
    获取商户交易记录。
    
    支持分页和日期过滤。
    
    需要商户角色认证。
    
    Query Parameters:
        - limit: 返回记录数限制（默认50，最大500）
        - offset: 偏移量（默认0）
        - start_date: 开始日期过滤（可选，格式：YYYY-MM-DD）
        - end_date: 结束日期过滤（可选，格式：YYYY-MM-DD）
    
    Returns:
        MerchantTransactionHistoryResponse: 交易记录列表和总数
    """
    try:
        merchant_service = MerchantService(db)
        result = merchant_service.get_transactions(
            user=current_user,
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date
        )
        return result
    
    except MerchantNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error_code": e.error_code, "message": e.message}
        )
    
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error_code": "INVALID_DATE_FORMAT", "message": "日期格式错误，请使用 YYYY-MM-DD"}
        )
    
    except Exception as e:
        logger.error(f"Get merchant transactions error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "获取交易记录失败"}
        )
