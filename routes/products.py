"""
Products routes for Booth Management System.

提供商品管理相关的 API 端点。
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from typing import Optional, List
import logging

from core.database import get_db
from core.security import get_current_user, RoleChecker
from services.product_service import (
    ProductService,
    ProductNotFoundError,
    InvalidBoothError,
    ProductNotInBoothError,
    NegativePriceError,
    NegativeStockError
)
from schemas.product import ProductCreate, ProductUpdate, ProductResponse
from models.user import User
from core.exceptions import BusinessException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/products", response_model=ProductResponse, status_code=201)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    创建新商品。
    
    需要 event_admin 或 super_admin 角色。
    
    Request Body:
        - booth_id: 摊位ID（必填）
        - name: 商品名称（必填，1-100字符）
        - price: 售价（必填，非负整数，单位：分）
        - cost_price: 成本价（可选，非负整数，单位：分）
        - stock: 库存数量（可选，非负整数或null表示无限）
    
    Returns:
        ProductResponse: 创建的商品信息
        
    Error Responses:
        400: 验证错误（如摊位不存在、价格为负数）
        401: 未认证
        403: 权限不足
        500: 内部服务器错误
    
    Example:
        POST /products
        {
            "booth_id": 1,
            "name": "奶茶",
            "price": 500,
            "cost_price": 300,
            "stock": 100
        }
    
    Validates Requirements:
        - Requirement 9.1: POST /products creates a new product
        - Requirement 9.5: Validate booth_id exists before creating product
        - Requirement 9.6: Validate price and cost_price are non-negative
        - Requirement 9.7: Validate stock is non-negative if provided
        - Requirement 9.8: Require authentication for product management endpoints
    """
    try:
        product_service = ProductService(db)
        
        product = product_service.create_product(
            booth_id=product_data.booth_id,
            name=product_data.name,
            price=product_data.price,
            cost_price=product_data.cost_price,
            stock=product_data.stock
        )
        
        logger.info(
            f"Product created successfully: id={product.id}, name='{product.name}', "
            f"price={product.price}, booth_id={product.booth_id}, created_by={current_user.username}"
        )
        
        return ProductResponse.model_validate(product)
    
    except InvalidBoothError as e:
        logger.warning(f"Product creation failed - invalid booth: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except (NegativePriceError, NegativeStockError) as e:
        logger.warning(f"Product creation validation failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except ValueError as e:
        logger.warning(f"Product creation validation failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": str(e)
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in product creation: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )


@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    booth_id: Optional[int] = Query(None, description="Filter by booth ID"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of products to return"),
    offset: int = Query(0, ge=0, description="Number of products to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取商品列表，支持摊位和启用状态过滤。
    
    权限验证：
    - super_admin 和 event_admin 可以查看所有商品
    - booth_cashier 只能查看自己摊位的商品
    
    Query Parameters:
        - booth_id: 摊位ID过滤（可选）
        - enabled: 启用状态过滤（可选）
        - limit: 返回记录数限制（默认100，最大1000）
        - offset: 偏移量（默认0）
    
    Returns:
        List[ProductResponse]: 商品列表
        
    Error Responses:
        401: 未认证
        403: 权限不足
        500: 内部服务器错误
    
    Example:
        GET /products?booth_id=1&enabled=true&limit=10&offset=0
    
    Validates Requirements:
        - Requirement 9.2: GET /products returns list of products with optional filtering
        - Requirement 9.8: Require authentication for product management endpoints
        - Requirement 5.1: booth_cashier can only view products from their assigned booth
    """
    try:
        product_service = ProductService(db)
        
        # Permission validation for booth_cashier
        # booth_cashier can only view products from their assigned booth
        if current_user.role == 'booth_cashier':
            # If booth_id is provided and doesn't match user's booth, deny access
            if booth_id is not None and booth_id != current_user.booth_id:
                logger.warning(
                    f"Product access denied: booth_cashier {current_user.username} "
                    f"attempted to access booth {booth_id} products (assigned booth: {current_user.booth_id})"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. You can only access products from booth {current_user.booth_id}. Requested booth: {booth_id}"
                )
            
            # Force booth_id to user's assigned booth
            booth_id = current_user.booth_id
            logger.info(
                f"Products listed for booth_cashier: booth_id={booth_id}, "
                f"requested_by={current_user.username}"
            )
        
        # super_admin and event_admin can view all products
        elif current_user.role in ('super_admin', 'event_admin'):
            logger.info(
                f"Products listed: booth_id={booth_id}, enabled={enabled}, "
                f"requested_by={current_user.username} (role={current_user.role})"
            )
        
        # Other roles (issuer, reviewer) cannot access product data
        else:
            logger.warning(
                f"Product access denied: role '{current_user.role}' cannot access product data "
                f"(user={current_user.username})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Role '{current_user.role}' cannot access product data"
            )
        
        products = product_service.list_products(
            booth_id=booth_id,
            enabled=enabled,
            limit=limit,
            offset=offset
        )
        
        logger.info(
            f"Products retrieved: count={len(products)}, booth_id={booth_id}, "
            f"enabled={enabled}"
        )
        
        return [ProductResponse.model_validate(product) for product in products]
    
    except HTTPException:
        # Re-raise HTTPException (403 errors from permission validation)
        raise
    
    except Exception as e:
        logger.error(
            f"Unexpected error in product listing: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )


@router.patch("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    更新商品信息。
    
    需要 event_admin 或 super_admin 角色。
    
    Path Parameters:
        - product_id: 商品ID
    
    Request Body:
        - name: 商品名称（可选，1-100字符）
        - price: 售价（可选，非负整数，单位：分）
        - cost_price: 成本价（可选，非负整数，单位：分）
        - stock: 库存数量（可选，非负整数）
        - enabled: 是否启用（可选）
    
    Returns:
        ProductResponse: 更新后的商品信息
        
    Error Responses:
        400: 验证错误（如价格为负数）
        401: 未认证
        403: 权限不足
        404: 商品不存在
        500: 内部服务器错误
    
    Example:
        PATCH /products/1
        {
            "price": 600,
            "stock": 80,
            "enabled": true
        }
    
    Validates Requirements:
        - Requirement 9.3: PATCH /products/{id} updates product
        - Requirement 9.4: Product not found returns 404 error
        - Requirement 9.6: Validate price and cost_price are non-negative
        - Requirement 9.7: Validate stock is non-negative if provided
        - Requirement 9.8: Require authentication for product management endpoints
    """
    try:
        product_service = ProductService(db)
        
        product = product_service.update_product(
            product_id=product_id,
            name=product_data.name,
            price=product_data.price,
            cost_price=product_data.cost_price,
            stock=product_data.stock,
            enabled=product_data.enabled
        )
        
        logger.info(
            f"Product updated successfully: id={product_id}, "
            f"updated_by={current_user.username}"
        )
        
        return ProductResponse.model_validate(product)
    
    except ProductNotFoundError as e:
        logger.warning(f"Product not found: {product_id}")
        return JSONResponse(
            status_code=404,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except (NegativePriceError, NegativeStockError) as e:
        logger.warning(f"Product update validation failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    
    except ValueError as e:
        logger.warning(f"Product update validation failed: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": str(e)
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error in product update: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        )
