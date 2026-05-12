"""
Cash Reconciliation service for NFC Campus Event System.

现金对账服务：管理摊位现金对账操作。
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict
from datetime import datetime
import logging

from models.cash_reconciliation import CashReconciliation
from models.booth import Booth
from models.event import Event
from core.exceptions import ResourceNotFoundError, ValidationError

logger = logging.getLogger(__name__)


class CashReconciliationService:
    """
    现金对账服务类。
    
    提供现金对账相关操作。
    """
    
    def __init__(self, db_session: Session):
        """
        初始化现金对账服务。
        
        Args:
            db_session: SQLAlchemy 数据库会话
        """
        self.db = db_session
    
    def create_reconciliation(
        self,
        booth_id: int,
        event_id: int,
        expected_cash_yuan: float,
        actual_cash_yuan: float,
        reviewer_id: int,
        reason: Optional[str] = None
    ) -> CashReconciliation:
        """
        创建现金对账记录。
        
        Args:
            booth_id: 摊位ID
            event_id: 活动ID
            expected_cash_yuan: 预期现金金额（元）
            actual_cash_yuan: 实际现金金额（元）
            reviewer_id: 审核人ID
            reason: 差额原因说明
            
        Returns:
            CashReconciliation: 新创建的对账记录
            
        Raises:
            ResourceNotFoundError: 摊位或活动不存在
            ValidationError: 摊位不属于指定活动
        """
        try:
            # 验证摊位存在
            booth = self.db.query(Booth).filter(Booth.id == booth_id).first()
            if booth is None:
                raise ResourceNotFoundError(
                    f"Booth with id {booth_id} not found",
                    error_code="BOOTH_NOT_FOUND"
                )
            
            # 验证活动存在
            event = self.db.query(Event).filter(Event.id == event_id).first()
            if event is None:
                raise ResourceNotFoundError(
                    f"Event with id {event_id} not found",
                    error_code="EVENT_NOT_FOUND"
                )
            
            # 验证摊位属于活动
            if booth.event_id != event_id:
                raise ValidationError(
                    f"Booth {booth_id} does not belong to event {event_id}",
                    error_code="BOOTH_NOT_IN_EVENT"
                )
            
            # 金额直接使用元为单位
            expected_cash = expected_cash_yuan
            actual_cash = actual_cash_yuan
            diff_amount = actual_cash - expected_cash
            
            # 创建对账记录
            reconciliation = CashReconciliation(
                booth_id=booth_id,
                event_id=event_id,
                expected_cash=expected_cash,
                actual_cash=actual_cash,
                diff_amount=diff_amount,
                reason=reason,
                reviewer_id=reviewer_id
            )
            
            self.db.add(reconciliation)
            self.db.commit()
            self.db.refresh(reconciliation)
            
            logger.info(
                f"Cash reconciliation created: id={reconciliation.id}, "
                f"booth_id={booth_id}, diff={diff_amount} cents"
            )
            
            return reconciliation
            
        except (ResourceNotFoundError, ValidationError):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create cash reconciliation: {str(e)}")
            raise
    
    def get_reconciliation(self, reconciliation_id: int) -> CashReconciliation:
        """
        获取对账记录详情。
        
        Args:
            reconciliation_id: 对账记录ID
            
        Returns:
            CashReconciliation: 对账记录对象
            
        Raises:
            ResourceNotFoundError: 对账记录不存在
        """
        reconciliation = self.db.query(CashReconciliation).filter(
            CashReconciliation.id == reconciliation_id
        ).first()
        
        if reconciliation is None:
            raise ResourceNotFoundError(
                f"Cash reconciliation with id {reconciliation_id} not found",
                error_code="RECONCILIATION_NOT_FOUND"
            )
        
        return reconciliation
    
    def list_reconciliations(
        self,
        booth_id: Optional[int] = None,
        event_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict:
        """
        获取对账记录列表。
        
        Args:
            booth_id: 摊位ID过滤（可选）
            event_id: 活动ID过滤（可选）
            limit: 返回记录数限制
            offset: 偏移量
            
        Returns:
            Dict: 包含对账记录列表和总数
        """
        query = self.db.query(CashReconciliation)
        
        if booth_id is not None:
            query = query.filter(CashReconciliation.booth_id == booth_id)
        
        if event_id is not None:
            query = query.filter(CashReconciliation.event_id == event_id)
        
        total_count = query.count()
        
        reconciliations = query.order_by(
            CashReconciliation.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        logger.info(
            f"Cash reconciliations listed: count={len(reconciliations)}, "
            f"total={total_count}"
        )
        
        return {
            'reconciliations': reconciliations,
            'total_count': total_count
        }
