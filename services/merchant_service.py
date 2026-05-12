"""
Merchant service for NFC Campus E-Wallet System.

商户服务：处理商户注册、商铺管理、收入统计、交易记录等业务逻辑。
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import logging

from models.user import User
from models.booth import Booth
from models.product import Product
from models.transaction import Transaction
from core.security import hash_password, verify_password, create_access_token
from core.config import get_settings
from core.exceptions import BusinessException

logger = logging.getLogger(__name__)


class MerchantRegistrationError(BusinessException):
    """商户注册异常"""
    pass


class UsernameExistsError(MerchantRegistrationError):
    """用户名已存在"""
    
    def __init__(self, username: str):
        super().__init__(
            message=f"用户名'{username}' 已被注册",
            error_code="USERNAME_EXISTS"
        )
        self.username = username


class MerchantAuthError(BusinessException):
    """商户认证异常"""
    
    def __init__(self, message: str = "用户名或密码错误"):
        super().__init__(
            message=message,
            error_code="MERCHANT_AUTH_FAILED"
        )


class MerchantNotFoundError(BusinessException):
    """商户不存在"""
    
    def __init__(self, message: str = "商户信息不存在"):
        super().__init__(
            message=message,
            error_code="MERCHANT_NOT_FOUND"
        )


class MerchantInactiveError(BusinessException):
    """商户未激活"""
    
    def __init__(self, merchant_id: str = ""):
        super().__init__(
            message=f"Merchant '{merchant_id}' is not active" if merchant_id else "商户未激活",
            error_code="MERCHANT_INACTIVE"
        )


class ProductNotFoundError(BusinessException):
    """商品不存在"""
    
    def __init__(self, product_id: int):
        super().__init__(
            message=f"商品 ID '{product_id}' 不存在或不属于该商铺",
            error_code="PRODUCT_NOT_FOUND"
        )
        self.product_id = product_id


class MerchantService:
    """
    商户服务类。
    
    提供商户注册、登录、商铺管理、收入统计等操作。
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.settings = get_settings()
    
    def validate_merchant(self, merchant_id: str) -> None:
        """
        验证商户是否存在且激活（兼容旧版支付路由）。
        
        Args:
            merchant_id: 商户标识
            
        Raises:
            MerchantNotFoundError: 商户不存在
            MerchantInactiveError: 商户未激活
        """
        # merchant_id 可能是 booth_id 或 username
        user = self.db.query(User).filter(
            User.username == merchant_id
        ).first()
        
        if user is None:
            # 尝试用 booth_id 查找
            try:
                booth_id = int(merchant_id)
                booth = self.db.query(Booth).filter(Booth.id == booth_id).first()
                if booth is None:
                    raise MerchantNotFoundError(f"Merchant '{merchant_id}' not found")
                if booth.status != 'active':
                    raise MerchantInactiveError(merchant_id)
                return
            except (ValueError, TypeError):
                raise MerchantNotFoundError(f"Merchant '{merchant_id}' not found")
        
        if user.status != 'active':
            raise MerchantInactiveError(merchant_id)
    
    def register(
        self,
        username: str,
        password: str,
        booth_name: str,
        class_name: str
    ) -> Dict[str, Any]:
        """
        商户注册：创建用户账号 + 创建商铺。
        
        Args:
            username: 登录用户名
            password: 登录密码
            booth_name: 商铺名称
            class_name: 班级名称
            
        Returns:
            包含 access_token 和商户信息的字典
            
        Raises:
            UsernameExistsError: 用户名已存在
        """
        # 检查用户名是否已存在
        existing_user = self.db.query(User).filter(User.username == username).first()
        if existing_user:
            raise UsernameExistsError(username)
        
        # 获取当前激活的活动
        from services.event_service import EventService
        event_service = EventService(self.db)
        active_event = event_service.get_active_event()
        
        if active_event is None:
            raise BusinessException(
                message="当前没有激活的活动，无法注册商户",
                error_code="NO_ACTIVE_EVENT"
            )
        
        # 创建商铺
        booth = Booth(
            event_id=active_event.id,
            name=booth_name,
            class_name=class_name,
            status='active'
        )
        self.db.add(booth)
        self.db.flush()  # 获取 booth.id
        
        # 创建商户用户（使用 merchant 角色）
        password_hash = hash_password(password)
        user = User(
            username=username,
            password_hash=password_hash,
            role='merchant',
            booth_id=booth.id,
            status='active'
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        self.db.refresh(booth)
        
        # 生成 JWT token
        access_token = create_access_token(
            user=user,
            jwt_secret_key=self.settings.jwt_secret_key,
            jwt_algorithm=self.settings.jwt_algorithm,
            jwt_expiration_minutes=self.settings.jwt_expiration_minutes
        )
        
        logger.info(
            f"Merchant registered: user_id={user.id}, username='{username}', "
            f"booth_id={booth.id}, booth_name='{booth_name}'"
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "merchant": {
                "user_id": user.id,
                "username": user.username,
                "booth_id": booth.id,
                "booth_name": booth.name,
                "class_name": booth.class_name,
                "status": user.status
            }
        }
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        商户登录。
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            包含 access_token 和商户信息的字典
            
        Raises:
            MerchantAuthError: 认证失败
        """
        user = self.db.query(User).filter(
            User.username == username,
            User.role == 'merchant'
        ).first()
        
        if user is None:
            raise MerchantAuthError()
        
        if not verify_password(password, user.password_hash):
            raise MerchantAuthError()
        
        if user.status == 'blocked':
            raise MerchantAuthError("账户已被封禁")
        
        if user.status == 'inactive':
            raise MerchantAuthError("账户已被停用")
        
        # 获取商铺信息
        booth = self.db.query(Booth).filter(Booth.id == user.booth_id).first()
        if booth is None:
            raise MerchantNotFoundError()
        
        # 生成 JWT token
        access_token = create_access_token(
            user=user,
            jwt_secret_key=self.settings.jwt_secret_key,
            jwt_algorithm=self.settings.jwt_algorithm,
            jwt_expiration_minutes=self.settings.jwt_expiration_minutes
        )
        
        logger.info(f"Merchant logged in: user_id={user.id}, username='{username}'")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "merchant": {
                "user_id": user.id,
                "username": user.username,
                "booth_id": booth.id,
                "booth_name": booth.name,
                "class_name": booth.class_name,
                "status": user.status
            }
        }
    
    def get_booth_info(self, user: User) -> Dict[str, Any]:
        """
        获取商户的商铺信息（含商品列表）。
        
        Args:
            user: 当前登录的商户用户
            
        Returns:
            商铺信息字典
        """
        booth = self.db.query(Booth).filter(Booth.id == user.booth_id).first()
        if booth is None:
            raise MerchantNotFoundError()
        
        # 获取商品列表
        products = self.db.query(Product).filter(
            Product.booth_id == booth.id
        ).order_by(Product.created_at.desc()).all()
        
        product_list = []
        for p in products:
            product_list.append({
                "id": p.id,
                "name": p.name,
                "price": float(p.price),
                "cost_price": float(p.cost_price) if p.cost_price else None,
                "stock": p.stock,
                "enabled": p.enabled,
                "created_at": p.created_at
            })
        
        return {
            "booth_id": booth.id,
            "booth_name": booth.name,
            "class_name": booth.class_name,
            "status": booth.status,
            "event_id": booth.event_id,
            "created_at": booth.created_at,
            "products": product_list
        }
    
    def update_booth_info(
        self,
        user: User,
        booth_name: Optional[str] = None,
        class_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新商铺信息。
        
        Args:
            user: 当前登录的商户用户
            booth_name: 新商铺名称（可选）
            class_name: 新班级名称（可选）
            
        Returns:
            更新后的商铺信息
        """
        booth = self.db.query(Booth).filter(Booth.id == user.booth_id).first()
        if booth is None:
            raise MerchantNotFoundError()
        
        if booth_name:
            booth.name = booth_name
        if class_name:
            booth.class_name = class_name
        
        self.db.commit()
        self.db.refresh(booth)
        
        logger.info(f"Merchant booth updated: booth_id={booth.id}, user={user.username}")
        
        return {
            "booth_id": booth.id,
            "booth_name": booth.name,
            "class_name": booth.class_name,
            "status": booth.status,
            "event_id": booth.event_id,
            "created_at": booth.created_at
        }
    
    def add_product(
        self,
        user: User,
        name: str,
        price: float,
        cost_price: Optional[float] = None,
        stock: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        添加商品。
        
        Args:
            user: 当前登录的商户用户
            name: 商品名称
            price: 商品定价（元）
            cost_price: 成本价（元，可选）
            stock: 库存数量（可选）
            
        Returns:
            创建的商品信息
        """
        booth = self.db.query(Booth).filter(Booth.id == user.booth_id).first()
        if booth is None:
            raise MerchantNotFoundError()
        
        # 价格转换为分
        price_cents = int(price * 100)
        cost_price_cents = int(cost_price * 100) if cost_price is not None else None
        
        product = Product(
            booth_id=booth.id,
            name=name,
            price=price_cents,
            cost_price=cost_price_cents,
            stock=stock,
            enabled=True
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        
        logger.info(
            f"Merchant product added: product_id={product.id}, name='{name}', "
            f"price={price}, booth_id={booth.id}"
        )
        
        return {
            "id": product.id,
            "name": product.name,
            "price": float(product.price),
            "cost_price": float(product.cost_price) if product.cost_price else None,
            "stock": product.stock,
            "enabled": product.enabled,
            "created_at": product.created_at
        }
    
    def update_product(
        self,
        user: User,
        product_id: int,
        name: Optional[str] = None,
        price: Optional[float] = None,
        cost_price: Optional[float] = None,
        stock: Optional[int] = None,
        enabled: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        更新商品信息。
        
        Args:
            user: 当前登录的商户用户
            product_id: 商品ID
            name: 商品名称（可选）
            price: 商品定价（元，可选）
            cost_price: 成本价（元，可选）
            stock: 库存数量（可选）
            enabled: 是否上架（可选）
            
        Returns:
            更新后的商品信息
        """
        product = self.db.query(Product).filter(
            Product.id == product_id,
            Product.booth_id == user.booth_id
        ).first()
        
        if product is None:
            raise ProductNotFoundError(product_id)
        
        if name is not None:
            product.name = name
        if price is not None:
            product.price = int(price * 100)
        if cost_price is not None:
            product.cost_price = int(cost_price * 100)
        if stock is not None:
            product.stock = stock
        if enabled is not None:
            product.enabled = enabled
        
        self.db.commit()
        self.db.refresh(product)
        
        logger.info(f"Merchant product updated: product_id={product_id}, user={user.username}")
        
        return {
            "id": product.id,
            "name": product.name,
            "price": float(product.price),
            "cost_price": float(product.cost_price) if product.cost_price else None,
            "stock": product.stock,
            "enabled": product.enabled,
            "created_at": product.created_at
        }
    
    def delete_product(self, user: User, product_id: int) -> None:
        """
        删除商品。
        
        Args:
            user: 当前登录的商户用户
            product_id: 商品ID
        """
        product = self.db.query(Product).filter(
            Product.id == product_id,
            Product.booth_id == user.booth_id
        ).first()
        
        if product is None:
            raise ProductNotFoundError(product_id)
        
        self.db.delete(product)
        self.db.commit()
        
        logger.info(f"Merchant product deleted: product_id={product_id}, user={user.username}")
    
    def get_income_stats(self, user: User) -> Dict[str, Any]:
        """
        获取商户收入统计。
        
        Args:
            user: 当前登录的商户用户
            
        Returns:
            收入统计信息
        """
        booth = self.db.query(Booth).filter(Booth.id == user.booth_id).first()
        if booth is None:
            raise MerchantNotFoundError()
        
        # 总收入和总交易数
        total_stats = self.db.query(
            func.coalesce(func.sum(Transaction.amount), 0).label('total_income'),
            func.count(Transaction.id).label('total_count')
        ).filter(
            Transaction.booth_id == booth.id,
            Transaction.type == 'pay'
        ).first()
        
        # 今日收入和今日交易数
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        
        today_stats = self.db.query(
            func.coalesce(func.sum(Transaction.amount), 0).label('today_income'),
            func.count(Transaction.id).label('today_count')
        ).filter(
            Transaction.booth_id == booth.id,
            Transaction.type == 'pay',
            Transaction.created_at >= today_start
        ).first()
        
        # amount 在数据库中以元为单位存储
        total_income = float(total_stats.total_income or 0)
        today_income = float(today_stats.today_income or 0)
        
        return {
            "booth_id": booth.id,
            "booth_name": booth.name,
            "total_income": total_income,
            "total_transactions": total_stats.total_count or 0,
            "today_income": today_income,
            "today_transactions": today_stats.today_count or 0
        }
    
    def get_transactions(
        self,
        user: User,
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取商户交易记录。
        
        Args:
            user: 当前登录的商户用户
            limit: 返回记录数限制
            offset: 偏移量
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
            
        Returns:
            交易记录列表和总数
        """
        booth = self.db.query(Booth).filter(Booth.id == user.booth_id).first()
        if booth is None:
            raise MerchantNotFoundError()
        
        # 构建查询
        query = self.db.query(Transaction).filter(
            Transaction.booth_id == booth.id
        )
        
        # 日期过滤
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            query = query.filter(Transaction.created_at >= start_dt)
        
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, tzinfo=timezone.utc
            )
            query = query.filter(Transaction.created_at <= end_dt)
        
        # 总数
        total_count = query.count()
        
        # 分页查询
        transactions = query.order_by(
            Transaction.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        # 构建响应
        transaction_list = []
        for txn in transactions:
            # 获取商品名称
            product_name = None
            if txn.product_id:
                product = self.db.query(Product).filter(Product.id == txn.product_id).first()
                if product:
                    product_name = product.name
            
            transaction_list.append({
                "id": txn.id,
                "type": txn.type,
                "amount": float(txn.amount),  # 已经是元
                "product_name": product_name,
                "remark": txn.remark,
                "created_at": txn.created_at.isoformat() if txn.created_at else None
            })
        
        return {
            "transactions": transaction_list,
            "total_count": total_count
        }
