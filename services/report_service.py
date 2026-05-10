"""
Report service for NFC Campus E-Wallet System.

Provides business logic for generating reports, leaderboards, and analytics.
All statistics are based on transaction ledger (append-only mode).
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from models.transaction import Transaction, TransactionType
from models.booth import Booth
from models.product import Product
from models.participant import Participant
from models.account import Account
from models.event import Event
from models.user import User
from schemas.report import (
    SummaryReportResponse,
    BoothReportItem,
    BoothReportResponse,
    ProductReportItem,
    ProductReportResponse,
    LeaderboardItem,
    LeaderboardResponse,
    ProductLeaderboardItem,
    ProductLeaderboardResponse,
    AuditLogItem,
    AuditLogResponse
)

logger = logging.getLogger(__name__)


def _to_int(value) -> int:
    """Convert Decimal/None to int safely."""
    if value is None:
        return 0
    return int(value)


class ReportService:
    """报表服务类"""
    
    def __init__(self, db: Session):
        """
        Initialize report service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    # ========================================================================
    # Summary Report
    # ========================================================================
    
    def get_summary_report(self, event_id: Optional[int] = None) -> SummaryReportResponse:
        """
        获取总览统计报表。
        
        统计基于交易流水（transactions 表），不依赖简单的 balance 字段。
        
        Args:
            event_id: 活动ID（可选，不填则统计所有活动）
        
        Returns:
            SummaryReportResponse: 总览统计数据
        """
        # 构建基础查询条件
        query_filter = []
        if event_id:
            query_filter.append(Transaction.event_id == event_id)
        
        # 总发放额度（issue 类型交易）
        total_issued_cents = _to_int(self.db.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).filter(
            Transaction.type == TransactionType.issue.value,
            *query_filter
        ).scalar())
        
        # 总充值额（recharge 类型交易）
        total_recharged_cents = _to_int(self.db.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).filter(
            Transaction.type == TransactionType.recharge.value,
            *query_filter
        ).scalar())
        
        # 总消费额（pay 类型交易）
        total_consumed_cents = _to_int(self.db.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).filter(
            Transaction.type == TransactionType.pay.value,
            *query_filter
        ).scalar())
        
        # 总退款额（refund 类型交易）
        total_refunded_cents = _to_int(self.db.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).filter(
            Transaction.type == TransactionType.refund.value,
            *query_filter
        ).scalar())
        
        # 净消费额 = 总消费 - 总退款
        net_consumed_cents = total_consumed_cents - total_refunded_cents
        
        # 总交易笔数
        total_transactions = self.db.query(
            func.count(Transaction.id)
        ).filter(*query_filter).scalar()
        
        # 参与者数量（去重）
        if event_id:
            participant_count = self.db.query(
                func.count(func.distinct(Account.participant_id))
            ).filter(Account.event_id == event_id).scalar()
        else:
            participant_count = self.db.query(
                func.count(Participant.id)
            ).scalar()
        
        # 摊位数量
        booth_query = self.db.query(func.count(Booth.id))
        if event_id:
            booth_query = booth_query.filter(Booth.event_id == event_id)
        booth_count = booth_query.scalar()
        
        return SummaryReportResponse(
            total_issued=float(total_issued_cents),
            total_recharged=float(total_recharged_cents),
            total_consumed=float(total_consumed_cents),
            total_refunded=float(total_refunded_cents),
            net_consumed=float(net_consumed_cents),
            total_transactions=total_transactions,
            participant_count=participant_count,
            booth_count=booth_count
        )
    
    # ========================================================================
    # Booth Report
    # ========================================================================
    
    def get_booth_report(self, event_id: Optional[int] = None) -> BoothReportResponse:
        """
        获取摊位维度报表。
        
        统计每个摊位的营业额、退款、净收入、销量、成本、利润和利润率。
        
        Args:
            event_id: 活动ID（可选）
        
        Returns:
            BoothReportResponse: 摊位报表数据
        """
        # 构建摊位查询
        booth_query = self.db.query(Booth)
        if event_id:
            booth_query = booth_query.filter(Booth.event_id == event_id)
        
        booths = booth_query.all()
        booth_items = []
        
        for booth in booths:
            # 营业额（pay 类型交易）
            revenue_cents = _to_int(self.db.query(
                func.coalesce(func.sum(Transaction.amount), 0)
            ).filter(
                Transaction.booth_id == booth.id,
                Transaction.type == TransactionType.pay.value
            ).scalar())
            
            # 退款额（refund 类型交易）
            refund_cents = _to_int(self.db.query(
                func.coalesce(func.sum(Transaction.amount), 0)
            ).filter(
                Transaction.booth_id == booth.id,
                Transaction.type == TransactionType.refund.value
            ).scalar())
            
            # 净收入 = 营业额 - 退款
            net_revenue_cents = revenue_cents - refund_cents
            
            # 销量（pay 类型交易笔数）
            sales_count = _to_int(self.db.query(
                func.count(Transaction.id)
            ).filter(
                Transaction.booth_id == booth.id,
                Transaction.type == TransactionType.pay.value
            ).scalar())
            
            # 总成本（基于商品成本价和销量）
            # 查询该摊位所有商品的销售记录，计算总成本
            cost_query = self.db.query(
                func.coalesce(func.sum(Product.cost_price), 0)
            ).join(
                Transaction,
                Transaction.product_id == Product.id
            ).filter(
                Transaction.booth_id == booth.id,
                Transaction.type == TransactionType.pay.value,
                Product.cost_price.isnot(None)
            )
            
            total_cost_cents = _to_int(cost_query.scalar()) or 0
            
            # 利润 = 净收入 - 成本
            profit_cents = net_revenue_cents - total_cost_cents
            
            # 利润率 = 利润 / 净收入 * 100（如果净收入为0则为None）
            profit_margin = None
            if net_revenue_cents > 0:
                profit_margin = (profit_cents / net_revenue_cents) * 100.0
            
            booth_items.append(BoothReportItem(
                booth_id=booth.id,
                booth_name=booth.name,
                class_name=booth.class_name,
                revenue=float(revenue_cents),
                refund_amount=float(refund_cents),
                net_revenue=float(net_revenue_cents),
                sales_count=sales_count,
                total_cost=float(total_cost_cents),
                profit=float(profit_cents),
                profit_margin=round(profit_margin, 2) if profit_margin is not None else None
            ))
        
        return BoothReportResponse(
            booths=booth_items,
            total_count=len(booth_items)
        )
    
    # ========================================================================
    # Product Report
    # ========================================================================
    
    def get_product_report(
        self,
        event_id: Optional[int] = None,
        booth_id: Optional[int] = None
    ) -> ProductReportResponse:
        """
        获取商品维度报表。
        
        统计每个商品的销量、收入、成本、利润和利润率。
        
        Args:
            event_id: 活动ID（可选）
            booth_id: 摊位ID（可选）
        
        Returns:
            ProductReportResponse: 商品报表数据
        """
        # 构建商品查询
        product_query = self.db.query(Product).join(Booth)
        
        if event_id:
            product_query = product_query.filter(Booth.event_id == event_id)
        if booth_id:
            product_query = product_query.filter(Product.booth_id == booth_id)
        
        products = product_query.all()
        product_items = []
        
        for product in products:
            # 销量（pay 类型交易笔数）
            sales_quantity = _to_int(self.db.query(
                func.count(Transaction.id)
            ).filter(
                Transaction.product_id == product.id,
                Transaction.type == TransactionType.pay.value
            ).scalar())
            
            # 收入（pay 类型交易金额）
            revenue_cents = _to_int(self.db.query(
                func.coalesce(func.sum(Transaction.amount), 0)
            ).filter(
                Transaction.product_id == product.id,
                Transaction.type == TransactionType.pay.value
            ).scalar())
            
            # 总成本 = 成本价 * 销量
            total_cost_cents = 0
            if product.cost_price is not None:
                total_cost_cents = product.cost_price * sales_quantity
            
            # 利润 = 收入 - 成本
            profit_cents = revenue_cents - total_cost_cents
            
            # 利润率 = 利润 / 收入 * 100
            profit_margin = None
            if revenue_cents > 0:
                profit_margin = (profit_cents / revenue_cents) * 100.0
            
            product_items.append(ProductReportItem(
                product_id=product.id,
                product_name=product.name,
                booth_id=product.booth_id,
                booth_name=product.booth.name,
                sales_quantity=sales_quantity,
                revenue=float(revenue_cents),
                total_cost=float(total_cost_cents),
                profit=float(profit_cents),
                profit_margin=round(profit_margin, 2) if profit_margin is not None else None
            ))
        
        return ProductReportResponse(
            products=product_items,
            total_count=len(product_items)
        )
    
    # ========================================================================
    # Leaderboards
    # ========================================================================
    
    def get_revenue_leaderboard(
        self,
        event_id: Optional[int] = None,
        limit: int = 10
    ) -> LeaderboardResponse:
        """
        获取营业额排行榜（TOP N）。
        
        Args:
            event_id: 活动ID（可选）
            limit: 返回数量限制
        
        Returns:
            LeaderboardResponse: 营业额排行榜
        """
        # 构建查询：按摊位分组，计算营业额
        query = self.db.query(
            Booth.id.label('booth_id'),
            Booth.name.label('booth_name'),
            Booth.class_name.label('class_name'),
            func.coalesce(func.sum(Transaction.amount), 0).label('revenue')
        ).outerjoin(
            Transaction,
            and_(
                Transaction.booth_id == Booth.id,
                Transaction.type == TransactionType.pay.value
            )
        ).group_by(
            Booth.id, Booth.name, Booth.class_name
        )
        
        if event_id:
            query = query.filter(Booth.event_id == event_id)
        
        # 按营业额降序排序
        query = query.order_by(desc('revenue')).limit(limit)
        
        results = query.all()
        
        leaderboard = [
            LeaderboardItem(
                rank=idx + 1,
                booth_id=row.booth_id,
                booth_name=row.booth_name,
                class_name=row.class_name,
                value=float(_to_int(row.revenue))
            )
            for idx, row in enumerate(results)
        ]
        
        return LeaderboardResponse(
            leaderboard=leaderboard,
            metric="营业额（元）",
            total_count=len(leaderboard)
        )
    
    def get_profit_leaderboard(
        self,
        event_id: Optional[int] = None,
        limit: int = 10
    ) -> LeaderboardResponse:
        """
        获取利润排行榜（TOP N）。
        
        Args:
            event_id: 活动ID（可选）
            limit: 返回数量限制
        
        Returns:
            LeaderboardResponse: 利润排行榜
        """
        # 获取摊位报表数据
        booth_report = self.get_booth_report(event_id)
        
        # 按利润排序
        sorted_booths = sorted(
            booth_report.booths,
            key=lambda x: x.profit,
            reverse=True
        )[:limit]
        
        leaderboard = [
            LeaderboardItem(
                rank=idx + 1,
                booth_id=booth.booth_id,
                booth_name=booth.booth_name,
                class_name=booth.class_name,
                value=booth.profit
            )
            for idx, booth in enumerate(sorted_booths)
        ]
        
        return LeaderboardResponse(
            leaderboard=leaderboard,
            metric="利润（元）",
            total_count=len(leaderboard)
        )
    
    def get_roi_leaderboard(
        self,
        event_id: Optional[int] = None,
        limit: int = 10
    ) -> LeaderboardResponse:
        """
        获取利润率排行榜（TOP N）。
        
        Args:
            event_id: 活动ID（可选）
            limit: 返回数量限制
        
        Returns:
            LeaderboardResponse: 利润率排行榜
        """
        # 获取摊位报表数据
        booth_report = self.get_booth_report(event_id)
        
        # 过滤掉利润率为 None 的摊位，按利润率排序
        booths_with_margin = [
            booth for booth in booth_report.booths
            if booth.profit_margin is not None
        ]
        
        sorted_booths = sorted(
            booths_with_margin,
            key=lambda x: x.profit_margin,
            reverse=True
        )[:limit]
        
        leaderboard = [
            LeaderboardItem(
                rank=idx + 1,
                booth_id=booth.booth_id,
                booth_name=booth.booth_name,
                class_name=booth.class_name,
                value=booth.profit_margin
            )
            for idx, booth in enumerate(sorted_booths)
        ]
        
        return LeaderboardResponse(
            leaderboard=leaderboard,
            metric="利润率（%）",
            total_count=len(leaderboard)
        )
    
    def get_product_leaderboard(
        self,
        metric: str = "sales",
        event_id: Optional[int] = None,
        limit: int = 10
    ) -> ProductLeaderboardResponse:
        """
        获取商品排行榜（TOP N）。
        
        Args:
            metric: 排序指标（sales=销量, revenue=收入, profit=利润）
            event_id: 活动ID（可选）
            limit: 返回数量限制
        
        Returns:
            ProductLeaderboardResponse: 商品排行榜
        """
        # 获取商品报表数据
        product_report = self.get_product_report(event_id)
        
        # 根据指标排序
        if metric == "sales":
            sorted_products = sorted(
                product_report.products,
                key=lambda x: x.sales_quantity,
                reverse=True
            )[:limit]
            metric_name = "销量（件）"
            value_field = "sales_quantity"
        elif metric == "revenue":
            sorted_products = sorted(
                product_report.products,
                key=lambda x: x.revenue,
                reverse=True
            )[:limit]
            metric_name = "收入（元）"
            value_field = "revenue"
        elif metric == "profit":
            sorted_products = sorted(
                product_report.products,
                key=lambda x: x.profit,
                reverse=True
            )[:limit]
            metric_name = "利润（元）"
            value_field = "profit"
        else:
            raise ValueError(f"Invalid metric: {metric}")
        
        leaderboard = [
            ProductLeaderboardItem(
                rank=idx + 1,
                product_id=product.product_id,
                product_name=product.product_name,
                booth_id=product.booth_id,
                booth_name=product.booth_name,
                value=getattr(product, value_field)
            )
            for idx, product in enumerate(sorted_products)
        ]
        
        return ProductLeaderboardResponse(
            leaderboard=leaderboard,
            metric=metric_name,
            total_count=len(leaderboard)
        )
    
    # ========================================================================
    # Audit Logs
    # ========================================================================
    
    def get_audit_logs(
        self,
        event_id: Optional[int] = None,
        flag_type: str = "all",
        limit: int = 100
    ) -> AuditLogResponse:
        """
        获取异常审计日志。
        
        标记规则：
        - high_frequency_refund: 高频退款（同一操作员在1小时内退款超过5次）
        - large_adjustment: 大额更正（adjust 类型且金额 > 1000元）
        - suspicious_operation: 可疑操作（深夜交易：22:00-06:00）
        
        Args:
            event_id: 活动ID（可选）
            flag_type: 标记类型（all/high_frequency_refund/large_adjustment/suspicious_operation）
            limit: 返回数量限制
        
        Returns:
            AuditLogResponse: 异常审计日志
        """
        logs = []
        
        # 1. 高频退款检测
        if flag_type in ["all", "high_frequency_refund"]:
            # 查询最近1小时内的退款交易，按操作员分组
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            refund_query = self.db.query(
                Transaction.booth_operator_id,
                func.count(Transaction.id).label('refund_count')
            ).filter(
                Transaction.type == TransactionType.refund.value,
                Transaction.created_at >= one_hour_ago,
                Transaction.booth_operator_id.isnot(None)
            )
            
            if event_id:
                refund_query = refund_query.filter(Transaction.event_id == event_id)
            
            refund_stats = refund_query.group_by(
                Transaction.booth_operator_id
            ).having(
                func.count(Transaction.id) > 5
            ).all()
            
            # 获取这些操作员的退款记录
            for stat in refund_stats:
                operator_id = stat.refund_count
                
                transactions = self.db.query(Transaction).filter(
                    Transaction.booth_operator_id == stat.booth_operator_id,
                    Transaction.type == TransactionType.refund.value,
                    Transaction.created_at >= one_hour_ago
                ).order_by(desc(Transaction.created_at)).limit(limit).all()
                
                for txn in transactions:
                    logs.append(self._create_audit_log_item(
                        txn,
                        "高频退款（1小时内超过5次）"
                    ))
        
        # 2. 大额更正检测
        if flag_type in ["all", "large_adjustment"]:
            adjust_query = self.db.query(Transaction).filter(
                Transaction.type == TransactionType.adjust.value,
                Transaction.amount > 100000  # 1000元 = 100000分
            )
            
            if event_id:
                adjust_query = adjust_query.filter(Transaction.event_id == event_id)
            
            adjustments = adjust_query.order_by(
                desc(Transaction.created_at)
            ).limit(limit).all()
            
            for txn in adjustments:
                logs.append(self._create_audit_log_item(
                    txn,
                    "大额更正（金额超过1000元）"
                ))
        
        # 3. 可疑操作检测（深夜交易）
        if flag_type in ["all", "suspicious_operation"]:
            # 查询深夜时段（22:00-06:00）的交易
            suspicious_query = self.db.query(Transaction).filter(
                or_(
                    func.extract('hour', Transaction.created_at) >= 22,
                    func.extract('hour', Transaction.created_at) < 6
                ),
                Transaction.type.in_([
                    TransactionType.pay.value,
                    TransactionType.refund.value,
                    TransactionType.adjust.value
                ])
            )
            
            if event_id:
                suspicious_query = suspicious_query.filter(Transaction.event_id == event_id)
            
            suspicious_txns = suspicious_query.order_by(
                desc(Transaction.created_at)
            ).limit(limit).all()
            
            for txn in suspicious_txns:
                logs.append(self._create_audit_log_item(
                    txn,
                    "可疑操作（深夜交易：22:00-06:00）"
                ))
        
        # 按时间倒序排序，限制返回数量
        logs.sort(key=lambda x: x.created_at, reverse=True)
        logs = logs[:limit]
        
        return AuditLogResponse(
            logs=logs,
            total_count=len(logs)
        )
    
    def _create_audit_log_item(
        self,
        transaction: Transaction,
        flag_reason: str
    ) -> AuditLogItem:
        """
        创建审计日志项。
        
        Args:
            transaction: 交易记录
            flag_reason: 标记原因
        
        Returns:
            AuditLogItem: 审计日志项
        """
        # 获取参与者姓名（未实名用户显示卡号）
        participant_name = None
        if transaction.participant:
            participant_name = transaction.participant.display_name
        
        # 获取摊位名称
        booth_name = None
        if transaction.booth:
            booth_name = transaction.booth.name
        
        # 获取操作员用户名
        operator_username = None
        if transaction.booth_operator_id:
            operator = self.db.query(User).filter(
                User.id == transaction.booth_operator_id
            ).first()
            if operator:
                operator_username = operator.username
        
        return AuditLogItem(
            transaction_id=transaction.id,
            transaction_type=transaction.type,
            amount=float(transaction.amount),
            participant_name=participant_name,
            booth_name=booth_name,
            operator_username=operator_username,
            remark=transaction.remark,
            created_at=transaction.created_at,
            flag_reason=flag_reason
        )
