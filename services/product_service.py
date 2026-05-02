"""
Product service for Booth Management System.

管理商品的创建、查询、更新等操作。
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import logging

from models.product import Product
from models.booth import Booth
from core.exceptions import BusinessException

logger = logging.getLogger(__name__)


class ProductNotFoundError(BusinessException):
    """商品不存在异常"""
    
    def __init__(self, product_id: int):
        super().__init__(
            message=f"Product with ID '{product_id}' does not exist",
            error_code="PRODUCT_NOT_FOUND"
        )
        self.product_id = product_id


class InvalidBoothError(BusinessException):
    """无效摊位异常"""
    
    def __init__(self, booth_id: int):
        super().__init__(
            message=f"Booth with ID '{booth_id}' does not exist",
            error_code="INVALID_BOOTH_ID"
        )
        self.booth_id = booth_id


class ProductNotInBoothError(BusinessException):
    """商品不属于摊位异常"""
    
    def __init__(self, product_id: int, booth_id: int):
        super().__init__(
            message=f"Product '{product_id}' does not belong to booth '{booth_id}'",
            error_code="PRODUCT_NOT_IN_BOOTH"
        )
        self.product_id = product_id
        self.booth_id = booth_id


class NegativePriceError(BusinessException):
    """价格为负数异常"""
    
    def __init__(self, field_name: str, value: int):
        super().__init__(
            message=f"{field_name} cannot be negative (value: {value})",
            error_code="NEGATIVE_PRICE"
        )
        self.field_name = field_name
        self.value = value


class NegativeStockError(BusinessException):
    """库存为负数异常"""
    
    def __init__(self, value: int):
        super().__init__(
            message=f"Stock cannot be negative (value: {value})",
            error_code="NEGATIVE_STOCK"
        )
        self.value = value


class ProductService:
    """
    商品服务类。
    
    提供商品管理相关操作。
    """
    
    def __init__(self, db_session: Session):
        """
        初始化商品服务。
        
        Args:
            db_session: SQLAlchemy 数据库会话
        """
        self.db = db_session
    
    def create_product(
        self,
        booth_id: int,
        name: str,
        price: int,
        cost_price: Optional[int] = None,
        stock: Optional[int] = None,
        enabled: bool = True
    ) -> Product:
        """
        创建新商品。
        
        验证 booth_id 存在，验证价格和库存非负。
        
        Args:
            booth_id: 摊位ID
            name: 商品名称
            price: 售价（分）
            cost_price: 成本价（分，可选）
            stock: 库存数量（可选，null 表示无限）
            enabled: 是否启用（默认 True）
            
        Returns:
            Product: 新创建的商品对象
            
        Raises:
            InvalidBoothError: 摊位不存在
            NegativePriceError: 价格为负数
            NegativeStockError: 库存为负数
        """
        # 验证摊位是否存在
        booth = self.db.query(Booth).filter(Booth.id == booth_id).first()
        if booth is None:
            logger.warning(f"Cannot create product: booth {booth_id} does not exist")
            raise InvalidBoothError(booth_id)
        
        # 验证价格非负
        if price < 0:
            logger.warning(f"Cannot create product: price is negative ({price})")
            raise NegativePriceError("price", price)
        
        # 验证成本价非负（如果提供）
        if cost_price is not None and cost_price < 0:
            logger.warning(f"Cannot create product: cost_price is negative ({cost_price})")
            raise NegativePriceError("cost_price", cost_price)
        
        # 验证库存非负（如果提供）
        if stock is not None and stock < 0:
            logger.warning(f"Cannot create product: stock is negative ({stock})")
            raise NegativeStockError(stock)
        
        try:
            product = Product(
                booth_id=booth_id,
                name=name,
                price=price,
                cost_price=cost_price,
                stock=stock,
                enabled=enabled
            )
            
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
            
            logger.info(
                f"Product created: id={product.id}, name='{name}', "
                f"price={price}, booth_id={booth_id}"
            )
            return product
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create product: {str(e)}")
            raise
    
    def get_product(self, product_id: int) -> Product:
        """
        获取商品详情。
        
        Args:
            product_id: 商品ID
            
        Returns:
            Product: 商品对象
            
        Raises:
            ProductNotFoundError: 商品不存在
        """
        product = self.db.query(Product).filter(Product.id == product_id).first()
        
        if product is None:
            logger.warning(f"Product not found: {product_id}")
            raise ProductNotFoundError(product_id)
        
        return product
    
    def list_products(
        self,
        booth_id: Optional[int] = None,
        enabled: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Product]:
        """
        列出商品。
        
        支持按 booth_id 和 enabled 过滤。
        
        Args:
            booth_id: 摊位ID过滤（可选）
            enabled: 启用状态过滤（可选）
            limit: 返回记录数限制
            offset: 偏移量
            
        Returns:
            List[Product]: 商品列表
        """
        query = self.db.query(Product)
        
        if booth_id is not None:
            query = query.filter(Product.booth_id == booth_id)
        
        if enabled is not None:
            query = query.filter(Product.enabled == enabled)
        
        products = query.order_by(Product.created_at.desc()).limit(limit).offset(offset).all()
        
        logger.info(
            f"Products listed: count={len(products)}, booth_id={booth_id}, "
            f"enabled={enabled}"
        )
        
        return products
    
    def update_product(
        self,
        product_id: int,
        name: Optional[str] = None,
        price: Optional[int] = None,
        cost_price: Optional[int] = None,
        stock: Optional[int] = None,
        enabled: Optional[bool] = None
    ) -> Product:
        """
        更新商品信息。
        
        验证价格和库存非负。
        
        Args:
            product_id: 商品ID
            name: 商品名称（可选）
            price: 售价（分，可选）
            cost_price: 成本价（分，可选）
            stock: 库存数量（可选）
            enabled: 是否启用（可选）
            
        Returns:
            Product: 更新后的商品对象
            
        Raises:
            ProductNotFoundError: 商品不存在
            NegativePriceError: 价格为负数
            NegativeStockError: 库存为负数
        """
        product = self.get_product(product_id)
        
        # 验证价格非负（如果提供）
        if price is not None and price < 0:
            logger.warning(f"Cannot update product: price is negative ({price})")
            raise NegativePriceError("price", price)
        
        # 验证成本价非负（如果提供）
        if cost_price is not None and cost_price < 0:
            logger.warning(f"Cannot update product: cost_price is negative ({cost_price})")
            raise NegativePriceError("cost_price", cost_price)
        
        # 验证库存非负（如果提供）
        if stock is not None and stock < 0:
            logger.warning(f"Cannot update product: stock is negative ({stock})")
            raise NegativeStockError(stock)
        
        # 更新字段
        if name is not None:
            product.name = name
        if price is not None:
            product.price = price
        if cost_price is not None:
            product.cost_price = cost_price
        if stock is not None:
            product.stock = stock
        if enabled is not None:
            product.enabled = enabled
        
        try:
            self.db.commit()
            self.db.refresh(product)
            
            logger.info(f"Product updated: id={product_id}")
            return product
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to update product: {str(e)}")
            raise
    
    def validate_product_belongs_to_booth(
        self,
        product_id: int,
        booth_id: int
    ) -> Product:
        """
        验证商品属于指定摊位。
        
        Args:
            product_id: 商品ID
            booth_id: 摊位ID
            
        Returns:
            Product: 商品对象
            
        Raises:
            ProductNotFoundError: 商品不存在
            ProductNotInBoothError: 商品不属于指定摊位
        """
        product = self.get_product(product_id)
        
        if product.booth_id != booth_id:
            logger.warning(
                f"Product {product_id} does not belong to booth {booth_id} "
                f"(actual booth_id: {product.booth_id})"
            )
            raise ProductNotInBoothError(product_id, booth_id)
        
        return product
