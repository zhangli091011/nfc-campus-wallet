"""
Random Discount Service for NFC Campus E-Wallet System.

随机立减服务：处理随机立减的配置管理和立减计算逻辑。
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, Dict, Any
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone, timedelta
import random
import logging

from models.random_discount import RandomDiscountSetting, RandomDiscountRecord
from core.exceptions import ResourceNotFoundError, ValidationError
from core.timezone import CST

logger = logging.getLogger(__name__)


class DiscountResult:
    """立减计算结果"""
    
    def __init__(
        self,
        applied: bool,
        discount_amount: float = 0.0,
        original_amount: float = 0.0,
        actual_amount: float = 0.0
    ):
        self.applied = applied
        self.discount_amount = discount_amount
        self.original_amount = original_amount
        self.actual_amount = actual_amount


class RandomDiscountService:
    """
    随机立减服务类。
    
    提供：
    1. 配置管理（创建/更新/查询配置）
    2. 立减计算（根据配置随机计算立减金额）
    3. 记录管理（记录立减详情）
    4. 统计查询（奖池使用情况等）
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    # ==================== 配置管理 ====================
    
    def get_setting(self, event_id: int) -> Optional[RandomDiscountSetting]:
        """获取活动的随机立减配置"""
        return self.db.query(RandomDiscountSetting).filter(
            RandomDiscountSetting.event_id == event_id
        ).first()
    
    def create_or_update_setting(
        self,
        event_id: int,
        enabled: bool = False,
        min_discount_amount: float = 0.01,
        max_discount_amount: float = 5.00,
        probability: int = 100,
        total_pool: float = 1000.00,
        max_discount_per_transaction: Optional[float] = None,
        min_payment_amount: float = 1.00,
        daily_limit_per_user: Optional[int] = None
    ) -> RandomDiscountSetting:
        """创建或更新随机立减配置"""
        
        # 验证参数
        if min_discount_amount < 0:
            raise ValidationError("最小立减金额不能为负数", error_code="INVALID_MIN_DISCOUNT")
        if max_discount_amount < min_discount_amount:
            raise ValidationError("最大立减金额不能小于最小立减金额", error_code="INVALID_DISCOUNT_RANGE")
        if probability < 1 or probability > 100:
            raise ValidationError("触发概率必须在1-100之间", error_code="INVALID_PROBABILITY")
        if total_pool <= 0:
            raise ValidationError("总奖池金额必须大于0", error_code="INVALID_POOL")
        if min_payment_amount < 0:
            raise ValidationError("最低消费金额不能为负数", error_code="INVALID_MIN_PAYMENT")
        
        setting = self.get_setting(event_id)
        
        if setting is None:
            # 创建新配置
            setting = RandomDiscountSetting(
                event_id=event_id,
                enabled=enabled,
                min_discount_amount=min_discount_amount,
                max_discount_amount=max_discount_amount,
                probability=probability,
                total_pool=total_pool,
                remaining_pool=total_pool,
                max_discount_per_transaction=max_discount_per_transaction,
                min_payment_amount=min_payment_amount,
                daily_limit_per_user=daily_limit_per_user
            )
            self.db.add(setting)
        else:
            # 更新配置
            setting.enabled = enabled
            setting.min_discount_amount = min_discount_amount
            setting.max_discount_amount = max_discount_amount
            setting.probability = probability
            setting.total_pool = total_pool
            setting.max_discount_per_transaction = max_discount_per_transaction
            setting.min_payment_amount = min_payment_amount
            setting.daily_limit_per_user = daily_limit_per_user
            # 如果总奖池增加，相应增加剩余奖池
            if total_pool > float(setting.remaining_pool or 0):
                pool_diff = Decimal(str(total_pool)) - (setting.remaining_pool or Decimal('0'))
                setting.remaining_pool = setting.remaining_pool + pool_diff if setting.remaining_pool else Decimal(str(total_pool))
        
        self.db.commit()
        self.db.refresh(setting)
        
        logger.info(
            f"Random discount setting {'created' if setting.id else 'updated'}: "
            f"event_id={event_id}, enabled={enabled}, range=[{min_discount_amount}, {max_discount_amount}], "
            f"probability={probability}%, pool={total_pool}"
        )
        
        return setting
    
    def reset_pool(self, event_id: int, new_pool: Optional[float] = None) -> RandomDiscountSetting:
        """重置奖池"""
        setting = self.get_setting(event_id)
        if setting is None:
            raise ResourceNotFoundError("未找到随机立减配置", error_code="DISCOUNT_SETTING_NOT_FOUND")
        
        if new_pool is not None:
            setting.total_pool = Decimal(str(new_pool))
            setting.remaining_pool = Decimal(str(new_pool))
        else:
            setting.remaining_pool = setting.total_pool
        
        self.db.commit()
        self.db.refresh(setting)
        
        logger.info(f"Random discount pool reset: event_id={event_id}, pool={setting.remaining_pool}")
        return setting
    
    # ==================== 立减计算 ====================
    
    def calculate_discount(
        self,
        event_id: int,
        participant_id: int,
        payment_amount: float
    ) -> DiscountResult:
        """
        计算随机立减金额。
        
        逻辑：
        1. 检查配置是否启用
        2. 检查支付金额是否达到门槛
        3. 检查奖池是否有余额
        4. 检查每日限制
        5. 按概率决定是否触发
        6. 随机计算立减金额
        
        Args:
            event_id: 活动ID
            participant_id: 参与者ID
            payment_amount: 支付金额（元）
            
        Returns:
            DiscountResult: 立减计算结果
        """
        setting = self.get_setting(event_id)
        
        # 1. 检查配置是否存在且启用
        if setting is None or not setting.enabled:
            return DiscountResult(applied=False, original_amount=payment_amount, actual_amount=payment_amount)
        
        # 2. 检查支付金额是否达到门槛
        if payment_amount < float(setting.min_payment_amount):
            return DiscountResult(applied=False, original_amount=payment_amount, actual_amount=payment_amount)
        
        # 3. 检查奖池是否有余额
        if float(setting.remaining_pool) <= 0:
            return DiscountResult(applied=False, original_amount=payment_amount, actual_amount=payment_amount)
        
        # 4. 检查每日限制
        if setting.daily_limit_per_user is not None:
            today_count = self._get_today_discount_count(event_id, participant_id)
            if today_count >= setting.daily_limit_per_user:
                return DiscountResult(applied=False, original_amount=payment_amount, actual_amount=payment_amount)
        
        # 5. 按概率决定是否触发
        if random.randint(1, 100) > setting.probability:
            return DiscountResult(applied=False, original_amount=payment_amount, actual_amount=payment_amount)
        
        # 6. 随机计算立减金额
        min_amount = float(setting.min_discount_amount)
        max_amount = float(setting.max_discount_amount)
        
        # 立减金额不能超过支付金额
        max_amount = min(max_amount, payment_amount)
        
        # 立减金额不能超过单笔限制
        if setting.max_discount_per_transaction is not None:
            max_amount = min(max_amount, float(setting.max_discount_per_transaction))
        
        # 立减金额不能超过剩余奖池
        max_amount = min(max_amount, float(setting.remaining_pool))
        
        if max_amount < min_amount:
            # 如果最大可用金额小于最小立减金额，不触发
            return DiscountResult(applied=False, original_amount=payment_amount, actual_amount=payment_amount)
        
        # 随机生成立减金额（精确到分）
        discount_cents = random.randint(int(min_amount * 100), int(max_amount * 100))
        discount_amount = discount_cents / 100.0
        
        # 确保立减后金额不为负
        actual_amount = payment_amount - discount_amount
        if actual_amount < 0:
            discount_amount = payment_amount
            actual_amount = 0
        
        return DiscountResult(
            applied=True,
            discount_amount=discount_amount,
            original_amount=payment_amount,
            actual_amount=actual_amount
        )
    
    def apply_discount(
        self,
        event_id: int,
        participant_id: int,
        transaction_id: int,
        discount_result: DiscountResult,
        booth_id: Optional[int] = None
    ) -> Optional[RandomDiscountRecord]:
        """
        应用立减结果：扣减奖池并记录。
        
        在交易成功后调用此方法记录立减信息。
        
        Args:
            event_id: 活动ID
            participant_id: 参与者ID
            transaction_id: 交易ID
            discount_result: 立减计算结果
            booth_id: 摊位ID（可选）
            
        Returns:
            RandomDiscountRecord: 立减记录，如果未应用则返回None
        """
        if not discount_result.applied:
            return None
        
        setting = self.get_setting(event_id)
        if setting is None:
            return None
        
        # 扣减奖池（使用行锁）
        discount_decimal = Decimal(str(discount_result.discount_amount)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        # 再次检查奖池余额（防止并发）
        if setting.remaining_pool < discount_decimal:
            logger.warning(
                f"Discount pool insufficient during apply: event_id={event_id}, "
                f"remaining={setting.remaining_pool}, discount={discount_decimal}"
            )
            return None
        
        setting.remaining_pool = setting.remaining_pool - discount_decimal
        
        # 创建记录
        record = RandomDiscountRecord(
            event_id=event_id,
            participant_id=participant_id,
            transaction_id=transaction_id,
            booth_id=booth_id,
            original_amount=Decimal(str(discount_result.original_amount)).quantize(Decimal('0.01')),
            discount_amount=discount_decimal,
            actual_amount=Decimal(str(discount_result.actual_amount)).quantize(Decimal('0.01'))
        )
        
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        
        logger.info(
            f"Random discount applied: event_id={event_id}, participant_id={participant_id}, "
            f"transaction_id={transaction_id}, discount={discount_result.discount_amount}, "
            f"original={discount_result.original_amount}, actual={discount_result.actual_amount}, "
            f"remaining_pool={setting.remaining_pool}"
        )
        
        return record
    
    # ==================== 统计查询 ====================
    
    def get_statistics(self, event_id: int) -> Dict[str, Any]:
        """获取随机立减统计信息"""
        setting = self.get_setting(event_id)
        if setting is None:
            return {
                "configured": False,
                "enabled": False,
                "total_pool": 0,
                "remaining_pool": 0,
                "used_pool": 0,
                "total_discount_count": 0,
                "total_discount_amount": 0,
                "today_discount_count": 0,
                "today_discount_amount": 0
            }
        
        # 总计统计
        total_stats = self.db.query(
            func.count(RandomDiscountRecord.id).label('count'),
            func.coalesce(func.sum(RandomDiscountRecord.discount_amount), 0).label('total_amount')
        ).filter(RandomDiscountRecord.event_id == event_id).first()
        
        # 今日统计
        today_start = datetime.now(CST).replace(hour=0, minute=0, second=0, microsecond=0)
        today_stats = self.db.query(
            func.count(RandomDiscountRecord.id).label('count'),
            func.coalesce(func.sum(RandomDiscountRecord.discount_amount), 0).label('total_amount')
        ).filter(
            and_(
                RandomDiscountRecord.event_id == event_id,
                RandomDiscountRecord.created_at >= today_start
            )
        ).first()
        
        return {
            "configured": True,
            "enabled": setting.enabled,
            "total_pool": float(setting.total_pool),
            "remaining_pool": float(setting.remaining_pool),
            "used_pool": float(setting.total_pool - setting.remaining_pool),
            "total_discount_count": total_stats.count if total_stats else 0,
            "total_discount_amount": float(total_stats.total_amount) if total_stats else 0,
            "today_discount_count": today_stats.count if today_stats else 0,
            "today_discount_amount": float(today_stats.total_amount) if today_stats else 0,
            "min_discount_amount": float(setting.min_discount_amount),
            "max_discount_amount": float(setting.max_discount_amount),
            "probability": setting.probability,
            "min_payment_amount": float(setting.min_payment_amount),
            "daily_limit_per_user": setting.daily_limit_per_user
        }
    
    def get_records(
        self,
        event_id: int,
        participant_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """获取立减记录列表"""
        query = self.db.query(RandomDiscountRecord).filter(
            RandomDiscountRecord.event_id == event_id
        )
        
        if participant_id is not None:
            query = query.filter(RandomDiscountRecord.participant_id == participant_id)
        
        total = query.count()
        records = query.order_by(RandomDiscountRecord.created_at.desc()).offset(offset).limit(limit).all()
        
        return {
            "records": [
                {
                    "id": r.id,
                    "participant_id": r.participant_id,
                    "transaction_id": r.transaction_id,
                    "booth_id": r.booth_id,
                    "original_amount": float(r.original_amount),
                    "discount_amount": float(r.discount_amount),
                    "actual_amount": float(r.actual_amount),
                    "created_at": r.created_at.isoformat() if r.created_at else None
                }
                for r in records
            ],
            "total_count": total
        }
    
    # ==================== 内部方法 ====================
    
    def _get_today_discount_count(self, event_id: int, participant_id: int) -> int:
        """获取参与者今日已享受的立减次数"""
        today_start = datetime.now(CST).replace(hour=0, minute=0, second=0, microsecond=0)
        
        count = self.db.query(func.count(RandomDiscountRecord.id)).filter(
            and_(
                RandomDiscountRecord.event_id == event_id,
                RandomDiscountRecord.participant_id == participant_id,
                RandomDiscountRecord.created_at >= today_start
            )
        ).scalar()
        
        return count or 0
