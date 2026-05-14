"""
Stock Market Service - Business logic for stock market simulation.

模拟股市服务 - 股票发行、购买、结算的业务逻辑
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Tuple
import logging

from models.stock import Stock, StockPurchase, BoothSettlement
from core.timezone import CST
from models.booth import Booth
from models.participant import Participant
from models.account import Account
from models.transaction import Transaction
from models.event import Event
from models.product import Product
from core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    InsufficientFundsError,
    BusinessLogicError
)

logger = logging.getLogger(__name__)


class StockService:
    """股票市场服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============ Stock Management ============
    
    def create_stock(
        self,
        booth_id: int,
        event_id: int,
        total_shares: int,
        initial_price: int = 1000
    ) -> Stock:
        """
        创建股票发行
        
        Args:
            booth_id: 摊位ID
            event_id: 活动ID
            total_shares: 总发行股数
            initial_price: 初始发行价（分），默认1000分=10元
            
        Returns:
            Stock: 创建的股票对象
            
        Raises:
            ResourceNotFoundError: 摊位或活动不存在
            ValidationError: 摊位已发行股票
        """
        # 验证摊位存在
        booth = self.db.query(Booth).filter(Booth.id == booth_id).first()
        if not booth:
            raise ResourceNotFoundError(f"摊位不存在: {booth_id}")
        
        # 验证摊位是否允许参与股票市场
        if not getattr(booth, 'stock_enabled', 1):
            raise ValidationError(f"摊位「{booth.name}」未开启股票参与权限")
        
        # 验证活动存在
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise ResourceNotFoundError(f"活动不存在: {event_id}")
        
        # 验证摊位属于该活动
        if booth.event_id != event_id:
            raise ValidationError(f"摊位 {booth_id} 不属于活动 {event_id}")
        
        # 检查摊位是否已发行股票
        existing = self.db.query(Stock).filter(Stock.booth_id == booth_id).first()
        if existing:
            raise ValidationError(f"摊位 {booth_id} 已发行股票")
        
        # 创建股票
        stock = Stock(
            booth_id=booth_id,
            event_id=event_id,
            initial_price=initial_price,
            total_shares=total_shares,
            sold_shares=0,
            status='active'
        )
        
        self.db.add(stock)
        self.db.commit()
        self.db.refresh(stock)
        
        logger.info(
            f"创建股票: booth_id={booth_id}, total_shares={total_shares}, "
            f"initial_price={initial_price}"
        )
        
        return stock
    
    def get_stock(self, stock_id: int) -> Stock:
        """获取股票信息"""
        stock = self.db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            raise ResourceNotFoundError(f"股票不存在: {stock_id}")
        return stock
    
    def get_stock_by_booth(self, booth_id: int) -> Optional[Stock]:
        """根据摊位ID获取股票"""
        return self.db.query(Stock).filter(Stock.booth_id == booth_id).first()
    
    def list_stocks(
        self,
        event_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Stock]:
        """
        查询股票列表
        
        Args:
            event_id: 活动ID过滤
            status: 状态过滤
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            List[Stock]: 股票列表
        """
        query = self.db.query(Stock)
        
        if event_id:
            query = query.filter(Stock.event_id == event_id)
        
        if status:
            query = query.filter(Stock.status == status)
        
        return query.order_by(Stock.id).limit(limit).offset(offset).all()
    
    def update_stock_status(self, stock_id: int, status: str) -> Stock:
        """更新股票状态"""
        stock = self.get_stock(stock_id)
        
        if status not in ['active', 'suspended', 'settled']:
            raise ValidationError(f"无效的股票状态: {status}")
        
        stock.status = status
        self.db.commit()
        self.db.refresh(stock)
        
        logger.info(f"更新股票状态: stock_id={stock_id}, status={status}")
        
        return stock
    
    # ============ Stock Purchase ============
    
    def purchase_stock(
        self,
        card_uid: str,
        stock_id: int,
        quantity: int
    ) -> Tuple[StockPurchase, Transaction]:
        """
        购买股票（NFC刷卡）
        
        Args:
            card_uid: NFC卡UID
            stock_id: 股票ID
            quantity: 购买股数
            
        Returns:
            Tuple[StockPurchase, Transaction]: 购买记录和交易记录
            
        Raises:
            ResourceNotFoundError: 参与者、股票或账户不存在
            ValidationError: 股票不可购买或库存不足
            InsufficientFundsError: 余额不足
        """
        # 1. 查询参与者
        participant = self.db.query(Participant).filter(
            Participant.card_uid == card_uid
        ).first()
        if not participant:
            raise ResourceNotFoundError(f"参与者不存在: {card_uid}")
        
        if not participant.is_active():
            raise ValidationError(f"参与者状态异常: {participant.status}")
        
        # 2. 查询股票
        stock = self.get_stock(stock_id)
        
        if not stock.is_available():
            raise ValidationError(f"股票不可购买: status={stock.status}")
        
        if not stock.can_purchase(quantity):
            raise ValidationError(
                f"股票库存不足: 剩余{stock.available_shares}股，请求{quantity}股"
            )
        
        # 3. 查询账户
        account = self.db.query(Account).filter(
            and_(
                Account.participant_id == participant.id,
                Account.event_id == stock.event_id
            )
        ).first()
        
        if not account:
            raise ResourceNotFoundError(
                f"账户不存在: participant_id={participant.id}, event_id={stock.event_id}"
            )
        
        # 4. 计算金额
        purchase_price = stock.initial_price  # 统一发行价
        total_amount = purchase_price * quantity
        
        # 5. 检查余额
        if account.balance < total_amount:
            raise InsufficientFundsError(
                f"余额不足: 当前余额{account.balance}分，需要{total_amount}分"
            )
        
        # 6. 扣除余额（事务一致性）
        balance_before = account.balance
        account.balance -= total_amount
        balance_after = account.balance
        
        # 7. 更新股票已售数量
        stock.sold_shares += quantity
        
        # 8. 创建交易记录
        transaction = Transaction(
            event_id=stock.event_id,
            participant_id=participant.id,
            account_id=account.id,
            card_uid=card_uid,
            type='pay',
            amount=total_amount,
            balance_before=balance_before,
            balance_after=balance_after,
            remark=f"购买股票: {stock.booth.name} x {quantity}股"
        )
        self.db.add(transaction)
        self.db.flush()  # 获取transaction.id
        
        # 9. 创建购买记录
        purchase = StockPurchase(
            stock_id=stock_id,
            participant_id=participant.id,
            event_id=stock.event_id,
            quantity=quantity,
            purchase_price=purchase_price,
            total_amount=total_amount,
            transaction_id=transaction.id,
            status='holding'
        )
        self.db.add(purchase)
        
        # 10. 提交事务
        self.db.commit()
        self.db.refresh(purchase)
        self.db.refresh(transaction)
        
        logger.info(
            f"购买股票成功: participant_id={participant.id}, stock_id={stock_id}, "
            f"quantity={quantity}, total_amount={total_amount}"
        )
        
        return purchase, transaction
    
    def get_participant_holdings(
        self,
        participant_id: int,
        event_id: Optional[int] = None
    ) -> List[StockPurchase]:
        """
        查询参与者持仓
        
        Args:
            participant_id: 参与者ID
            event_id: 活动ID过滤（可选）
            
        Returns:
            List[StockPurchase]: 持仓列表
        """
        query = self.db.query(StockPurchase).filter(
            StockPurchase.participant_id == participant_id
        )
        
        if event_id:
            query = query.filter(StockPurchase.event_id == event_id)
        
        return query.order_by(StockPurchase.created_at.desc()).all()
    
    # ============ Settlement ============
    
    def calculate_booth_performance(
        self,
        booth_id: int,
        event_id: int
    ) -> Dict:
        """
        计算摊位经营数据
        
        退款冲账联动：refund 类型流水会扣减营业额和净利润，
        从而影响经营分和最终股价。
        
        Args:
            booth_id: 摊位ID
            event_id: 活动ID
            
        Returns:
            Dict: {revenue: 营业额, profit: 净利润, order_count: 订单数}
        """
        # 查询摊位所有支付交易
        pay_transactions = self.db.query(Transaction).filter(
            and_(
                Transaction.booth_id == booth_id,
                Transaction.event_id == event_id,
                Transaction.type == 'pay'
            )
        ).all()
        
        # 查询摊位所有退款交易（红字冲账）
        refund_transactions = self.db.query(Transaction).filter(
            and_(
                Transaction.booth_id == booth_id,
                Transaction.event_id == event_id,
                Transaction.type == 'refund'
            )
        ).all()
        
        # 计算营业额（支付 - 退款）和有效订单数
        gross_revenue = sum(t.amount for t in pay_transactions)
        refund_total = sum(t.amount for t in refund_transactions)
        revenue = max(0, gross_revenue - refund_total)
        order_count = len(pay_transactions) - len(refund_transactions)
        order_count = max(0, order_count)
        
        # 计算净利润（需要产品成本信息）
        profit = 0
        for txn in pay_transactions:
            if txn.product_id:
                product = self.db.query(Product).filter(
                    Product.id == txn.product_id
                ).first()
                if product and product.cost_price is not None:
                    profit += (product.price - product.cost_price)
                else:
                    profit += txn.amount
            else:
                profit += txn.amount
        
        # 退款扣减利润
        for txn in refund_transactions:
            if txn.product_id:
                product = self.db.query(Product).filter(
                    Product.id == txn.product_id
                ).first()
                if product and product.cost_price is not None:
                    profit -= (product.price - product.cost_price)
                else:
                    profit -= txn.amount
            else:
                profit -= txn.amount
        
        profit = max(0, profit)
        
        return {
            'revenue': revenue,
            'profit': profit,
            'order_count': order_count
        }
    
    def trigger_settlement(
        self,
        event_id: int,
        fee_rate: float = 0.05
    ) -> Dict:
        """
        触发期末结算
        
        计算逻辑：
        1. 全局奖金池 = (全场买股总金额) * (1 - fee_rate)
        2. 摊位分 = 0.2 * 营业额 + 0.6 * 净利润 + 0.2 * 订单数
        3. 分红占比 = 该摊位分 / 全场总分
        4. 最终股价 = (奖金池 * 占比) / 该摊位售出股数
        
        Args:
            event_id: 活动ID
            fee_rate: 手续费率（默认5%）
            
        Returns:
            Dict: 结算结果
            
        Raises:
            ResourceNotFoundError: 活动不存在
            BusinessLogicError: 已结算或无股票数据
        """
        # 1. 验证活动
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise ResourceNotFoundError(f"活动不存在: {event_id}")
        
        # 2. 查询所有股票
        stocks = self.db.query(Stock).filter(
            Stock.event_id == event_id
        ).all()
        
        if not stocks:
            raise BusinessLogicError(f"活动 {event_id} 没有发行股票")
        
        # 检查是否已结算
        for stock in stocks:
            if stock.status == 'settled':
                raise BusinessLogicError(f"活动 {event_id} 已完成结算")
        
        # 3. 计算全局奖金池
        total_investment = self.db.query(
            func.sum(StockPurchase.total_amount)
        ).filter(
            StockPurchase.event_id == event_id
        ).scalar() or 0
        
        global_pool = int(total_investment * (1 - fee_rate))
        
        logger.info(
            f"结算开始: event_id={event_id}, total_investment={total_investment}, "
            f"fee_rate={fee_rate}, global_pool={global_pool}"
        )
        
        # 4. 计算每个摊位的经营分
        booth_scores = []
        for stock in stocks:
            perf = self.calculate_booth_performance(stock.booth_id, event_id)
            
            # 摊位分 = 0.2 * 营业额 + 0.6 * 净利润 + 0.2 * 订单数
            score = Decimal(
                0.2 * perf['revenue'] +
                0.6 * perf['profit'] +
                0.2 * perf['order_count']
            )
            
            booth_scores.append({
                'stock': stock,
                'revenue': perf['revenue'],
                'profit': perf['profit'],
                'order_count': perf['order_count'],
                'score': score
            })
        
        # 5. 计算总分
        total_score = sum(b['score'] for b in booth_scores)
        
        if total_score == 0:
            raise BusinessLogicError("全场摊位总分为0，无法结算")
        
        # 6. 计算每个摊位的最终股价并创建结算记录
        settlements = []
        for booth_data in booth_scores:
            stock = booth_data['stock']
            score = booth_data['score']
            
            # 分红占比
            ratio = score / total_score
            
            # 该摊位分得的奖金
            booth_pool = int(global_pool * ratio)
            
            # 最终每股价格
            if stock.sold_shares > 0:
                final_price = booth_pool // stock.sold_shares
            else:
                final_price = 0
            
            # 创建结算记录
            settlement = BoothSettlement(
                booth_id=stock.booth_id,
                stock_id=stock.id,
                event_id=event_id,
                revenue=booth_data['revenue'],
                profit=booth_data['profit'],
                order_count=booth_data['order_count'],
                score=score,
                global_pool=global_pool,
                total_score=total_score,
                ratio=ratio,
                final_price=final_price
            )
            self.db.add(settlement)
            
            # 更新股票状态
            stock.status = 'settled'
            
            settlements.append({
                'booth_id': stock.booth_id,
                'booth_name': stock.booth.name,
                'class_name': stock.booth.class_name,
                'revenue': booth_data['revenue'],
                'profit': booth_data['profit'],
                'order_count': booth_data['order_count'],
                'score': score,
                'ratio': ratio,
                'final_price': final_price,
                'sold_shares': stock.sold_shares
            })
        
        # 7. 更新所有购买记录的结算价格
        for booth_data in booth_scores:
            stock = booth_data['stock']
            settlement = next(
                s for s in settlements if s['booth_id'] == stock.booth_id
            )
            final_price = settlement['final_price']
            
            # 查询该股票的所有购买记录
            purchases = self.db.query(StockPurchase).filter(
                StockPurchase.stock_id == stock.id
            ).all()
            
            for purchase in purchases:
                purchase.settlement_price = final_price
                purchase.settlement_amount = final_price * purchase.quantity
                purchase.status = 'settled'
                purchase.settled_at = datetime.now(CST)
        
        # 8. 提交事务
        self.db.commit()
        
        logger.info(
            f"结算完成: event_id={event_id}, booth_count={len(settlements)}, "
            f"global_pool={global_pool}"
        )
        
        return {
            'success': True,
            'event_id': event_id,
            'global_pool': global_pool,
            'total_score': total_score,
            'fee_rate': fee_rate,
            'booth_count': len(settlements),
            'booths': settlements,
            'settled_at': datetime.now(CST)
        }
    
    def get_settlement(self, booth_id: int) -> Optional[BoothSettlement]:
        """获取摊位结算记录"""
        return self.db.query(BoothSettlement).filter(
            BoothSettlement.booth_id == booth_id
        ).first()
    
    def list_settlements(self, event_id: int) -> List[BoothSettlement]:
        """查询活动的所有结算记录"""
        return self.db.query(BoothSettlement).filter(
            BoothSettlement.event_id == event_id
        ).order_by(BoothSettlement.score.desc()).all()
    
    # ============ Statistics ============
    
    def get_market_stats(self, event_id: int) -> Dict:
        """
        获取股市统计数据
        
        Args:
            event_id: 活动ID
            
        Returns:
            Dict: 统计数据
        """
        # 总投资金额
        total_investment = self.db.query(
            func.sum(StockPurchase.total_amount)
        ).filter(
            StockPurchase.event_id == event_id
        ).scalar() or 0
        
        # 股票数量
        stock_counts = self.db.query(
            func.count(Stock.id),
            func.count(Stock.id).filter(Stock.status == 'active')
        ).filter(
            Stock.event_id == event_id
        ).first()
        
        total_stocks = stock_counts[0] if stock_counts else 0
        active_stocks = stock_counts[1] if stock_counts else 0
        
        # 购买记录数
        total_purchases = self.db.query(
            func.count(StockPurchase.id)
        ).filter(
            StockPurchase.event_id == event_id
        ).scalar() or 0
        
        # 投资人数
        total_investors = self.db.query(
            func.count(func.distinct(StockPurchase.participant_id))
        ).filter(
            StockPurchase.event_id == event_id
        ).scalar() or 0
        
        # 是否已结算
        is_settled = self.db.query(Stock).filter(
            and_(
                Stock.event_id == event_id,
                Stock.status == 'settled'
            )
        ).first() is not None
        
        # 计算奖金池（假设5%手续费）
        fee_rate = 0.05
        global_pool = int(total_investment * (1 - fee_rate))
        fee_collected = total_investment - global_pool
        
        return {
            'event_id': event_id,
            'total_investment': total_investment,
            'global_pool': global_pool,
            'fee_collected': fee_collected,
            'total_stocks': total_stocks,
            'active_stocks': active_stocks,
            'total_purchases': total_purchases,
            'total_investors': total_investors,
            'is_settled': is_settled
        }
