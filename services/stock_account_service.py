"""
Stock Market Service - Business logic for stock trading.

股票交易服务 - 直接从主账户扣款购买股票（含悲观锁）。
所有金额以"元"为单位 (Decimal)。
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Tuple
import logging

from models.stock_account import StockOrder
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

# 固定股价：10元/股
DEFAULT_STOCK_PRICE = Decimal('10.00')


class StockAccountService:
    """股票交易服务类（使用主账户）"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============ Stock Buy (with Pessimistic Lock) ============
    
    def buy_stock(
        self,
        card_uid: str,
        event_id: int,
        booth_id: int,
        shares: int
    ) -> Tuple[StockOrder, Account]:
        """
        购买股票（使用悲观锁防止并发超卖）
        直接从主账户余额扣款。
        
        Args:
            card_uid: NFC卡UID
            event_id: 活动ID
            booth_id: 摊位ID
            shares: 购买股数
            
        Returns:
            Tuple[StockOrder, Account]: 股票订单、主账户
            
        Raises:
            ResourceNotFoundError: 参与者、摊位或账户不存在
            ValidationError: 摊位不属于该活动
            InsufficientFundsError: 账户余额不足
        """
        # 1. 查询参与者
        participant = self.db.query(Participant).filter(
            Participant.card_uid == card_uid
        ).first()
        if not participant:
            raise ResourceNotFoundError(f"参与者不存在: {card_uid}")
        
        if not participant.is_active():
            raise ValidationError(f"参与者状态异常: {participant.status}")
        
        # 实名认证校验（投资操作需要实名）
        if not participant.is_verified:
            raise ValidationError(f"参与者 {participant.name} 未完成实名认证（需填写班级或学号），无法进行投资操作")
        
        # 2. 查询摊位
        booth = self.db.query(Booth).filter(Booth.id == booth_id).first()
        if not booth:
            raise ResourceNotFoundError(f"摊位不存在: {booth_id}")
        
        if booth.event_id != event_id:
            raise ValidationError(f"摊位 {booth_id} 不属于活动 {event_id}")
        
        if not booth.is_active():
            raise ValidationError(f"摊位状态异常: {booth.status}")
        
        # 3. 开启事务并使用悲观锁
        try:
            # 锁定主账户（悲观锁）
            account = self.db.query(Account).filter(
                and_(
                    Account.participant_id == participant.id,
                    Account.event_id == event_id
                )
            ).with_for_update().first()
            
            if not account:
                raise ResourceNotFoundError(
                    f"账户不存在: participant_id={participant.id}, event_id={event_id}"
                )
            
            # 4. 计算金额（固定单价10元/股）
            buy_price = DEFAULT_STOCK_PRICE
            total_amount = buy_price * shares
            
            # 5. 检查余额
            if account.balance < total_amount:
                raise InsufficientFundsError(
                    f"账户余额不足: 当前{account.balance}元，需要{total_amount}元"
                )
            
            # 6. 记录交易前余额
            balance_before = account.balance
            
            # 7. 扣除余额
            account.balance -= total_amount
            balance_after = account.balance
            
            # 8. 写入交易流水
            txn = Transaction(
                uid=None,
                card_uid=card_uid,
                event_id=event_id,
                participant_id=participant.id,
                account_id=account.id,
                type="stock_buy",
                amount=total_amount,
                balance_before=balance_before,
                balance_after=balance_after,
                booth_id=booth_id,
                remark=f"购买{booth.name}股票{shares}股，单价{buy_price}元"
            )
            self.db.add(txn)
            self.db.flush()
            
            # 9. 创建股票订单
            order = StockOrder(
                event_id=event_id,
                participant_id=participant.id,
                account_id=account.id,
                card_uid=card_uid,
                booth_id=booth_id,
                shares=shares,
                buy_price=buy_price,
                total_amount=total_amount,
                status='holding'
            )
            self.db.add(order)
            
            # 10. 提交事务
            self.db.commit()
            self.db.refresh(order)
            self.db.refresh(account)
            
            logger.info(
                f"购买股票成功: participant_id={participant.id}, booth_id={booth_id}, "
                f"shares={shares}, total_amount={total_amount}元, "
                f"balance: {balance_before}→{balance_after}元"
            )
            
            return order, account
        
        except (ResourceNotFoundError, ValidationError, InsufficientFundsError):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"购买股票失败: {e}", exc_info=True)
            raise
    
    # ============ Stock Sell (with Pessimistic Lock) ============
    
    def sell_stock(
        self,
        card_uid: str,
        event_id: int,
        booth_id: int,
        shares: int
    ) -> Tuple[int, Account]:
        """
        抛售股票（以当前股价结算，资金返回主账户）
        
        Args:
            card_uid: NFC卡UID
            event_id: 活动ID
            booth_id: 摊位ID
            shares: 抛售股数
            
        Returns:
            Tuple[int, Account]: 实际卖出股数、主账户
            
        Raises:
            ResourceNotFoundError: 参与者、摊位或账户不存在
            ValidationError: 无持仓或已结算
            BusinessLogicError: 持仓不足
        """
        # 1. 查询参与者
        participant = self.db.query(Participant).filter(
            Participant.card_uid == card_uid
        ).first()
        if not participant:
            raise ResourceNotFoundError(f"参与者不存在: {card_uid}")
        
        if not participant.is_active():
            raise ValidationError(f"参与者状态异常: {participant.status}")
        
        # 实名认证校验（投资操作需要实名）
        if not participant.is_verified:
            raise ValidationError(f"参与者 {participant.name} 未完成实名认证（需填写班级或学号），无法进行投资操作")
        
        # 2. 查询摊位
        booth = self.db.query(Booth).filter(Booth.id == booth_id).first()
        if not booth:
            raise ResourceNotFoundError(f"摊位不存在: {booth_id}")
        
        if booth.event_id != event_id:
            raise ValidationError(f"摊位 {booth_id} 不属于活动 {event_id}")
        
        # 3. 查询该参与者在该摊位的持仓订单（状态为 holding）
        holding_orders = self.db.query(StockOrder).filter(
            and_(
                StockOrder.participant_id == participant.id,
                StockOrder.event_id == event_id,
                StockOrder.booth_id == booth_id,
                StockOrder.status == 'holding'
            )
        ).order_by(StockOrder.created_at.asc()).all()
        
        if not holding_orders:
            raise ValidationError(f"无持仓: 该参与者在摊位 {booth.name} 没有持仓股票")
        
        # 计算总持仓
        total_holding = sum(o.shares for o in holding_orders)
        if total_holding < shares:
            raise BusinessLogicError(
                f"持仓不足: 当前持有{total_holding}股，请求卖出{shares}股"
            )
        
        # 4. 开启事务并使用悲观锁
        try:
            # 锁定主账户（悲观锁）
            account = self.db.query(Account).filter(
                and_(
                    Account.participant_id == participant.id,
                    Account.event_id == event_id
                )
            ).with_for_update().first()
            
            if not account:
                raise ResourceNotFoundError(
                    f"账户不存在: participant_id={participant.id}, event_id={event_id}"
                )
            
            # 5. 以当前股价卖出
            sell_price = DEFAULT_STOCK_PRICE
            total_amount = sell_price * shares
            
            # 6. 按 FIFO 顺序消减持仓订单
            remaining_to_sell = shares
            for order in holding_orders:
                if remaining_to_sell <= 0:
                    break
                if order.shares <= remaining_to_sell:
                    # 整单卖出 - 标记为 sold
                    remaining_to_sell -= order.shares
                    order.status = 'sold'
                    order.settlement_price = sell_price
                    order.settlement_amount = sell_price * order.shares
                    order.settled_at = datetime.now(timezone.utc)
                else:
                    # 部分卖出 - 拆单
                    sold_shares = remaining_to_sell
                    remaining_shares = order.shares - sold_shares
                    
                    # 原订单改为已卖出部分
                    order.shares = sold_shares
                    order.total_amount = order.buy_price * sold_shares
                    order.status = 'sold'
                    order.settlement_price = sell_price
                    order.settlement_amount = sell_price * sold_shares
                    order.settled_at = datetime.now(timezone.utc)
                    
                    # 创建新订单保留剩余持仓
                    new_order = StockOrder(
                        event_id=event_id,
                        participant_id=participant.id,
                        account_id=account.id,
                        card_uid=card_uid,
                        booth_id=booth_id,
                        shares=remaining_shares,
                        buy_price=order.buy_price,
                        total_amount=order.buy_price * remaining_shares,
                        status='holding'
                    )
                    self.db.add(new_order)
                    remaining_to_sell = 0
            
            # 7. 资金返回主账户
            balance_before = account.balance
            account.balance += total_amount
            balance_after = account.balance
            
            # 8. 写入交易流水
            txn = Transaction(
                uid=None,
                card_uid=card_uid,
                event_id=event_id,
                participant_id=participant.id,
                account_id=account.id,
                type="stock_sell",
                amount=total_amount,
                balance_before=balance_before,
                balance_after=balance_after,
                booth_id=booth_id,
                remark=f"抛售{booth.name}股票{shares}股，单价{sell_price}元，到账{total_amount}元"
            )
            self.db.add(txn)
            
            # 9. 提交事务
            self.db.commit()
            self.db.refresh(account)
            
            logger.info(
                f"抛售股票成功: participant_id={participant.id}, booth_id={booth_id}, "
                f"shares={shares}, total_amount={total_amount}元, "
                f"balance: {balance_before}→{balance_after}元"
            )
            
            return shares, account
        
        except (ResourceNotFoundError, ValidationError, BusinessLogicError):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"抛售股票失败: {e}", exc_info=True)
            raise
    
    def get_participant_holdings(
        self,
        card_uid: str,
        event_id: int
    ) -> List[Dict]:
        """
        查询参与者的持仓汇总（按摊位聚合）
        
        Returns:
            List[Dict]: 每个摊位的持仓信息
        """
        participant = self.db.query(Participant).filter(
            Participant.card_uid == card_uid
        ).first()
        if not participant:
            raise ResourceNotFoundError(f"参与者不存在: {card_uid}")
        
        holding_orders = self.db.query(StockOrder).filter(
            and_(
                StockOrder.participant_id == participant.id,
                StockOrder.event_id == event_id,
                StockOrder.status == 'holding'
            )
        ).all()
        
        # 按摊位聚合
        booth_holdings: Dict[int, Dict] = {}
        for order in holding_orders:
            bid = order.booth_id
            if bid not in booth_holdings:
                booth = self.db.query(Booth).filter(Booth.id == bid).first()
                booth_holdings[bid] = {
                    'booth_id': bid,
                    'booth_name': booth.name if booth else '未知',
                    'class_name': booth.class_name if booth else '',
                    'shares': 0,
                    'total_cost': Decimal('0'),
                    'current_price': float(DEFAULT_STOCK_PRICE),
                }
            booth_holdings[bid]['shares'] += order.shares
            booth_holdings[bid]['total_cost'] += order.total_amount
        
        result = []
        for bh in booth_holdings.values():
            bh['total_cost'] = float(bh['total_cost'])
            bh['market_value'] = bh['shares'] * bh['current_price']
            result.append(bh)
        
        return result

    def get_participant_orders(
        self,
        participant_id: int,
        event_id: Optional[int] = None
    ) -> List[StockOrder]:
        """查询参与者的股票订单"""
        query = self.db.query(StockOrder).filter(
            StockOrder.participant_id == participant_id
        )
        
        if event_id:
            query = query.filter(StockOrder.event_id == event_id)
        
        return query.order_by(StockOrder.created_at.desc()).all()
    
    # ============ Settlement ============
    
    def calculate_booth_performance(
        self,
        booth_id: int,
        event_id: int
    ) -> Dict:
        """
        计算摊位经营数据（金额已为元）
        
        退款冲账联动：refund 类型流水会扣减营业额和净利润。
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
        
        # 计算营业额（支付 - 退款），金额已为元
        gross_revenue = sum(float(t.amount) for t in pay_transactions)
        refund_total = sum(float(t.amount) for t in refund_transactions)
        revenue = max(Decimal('0'), Decimal(str(gross_revenue - refund_total)))
        order_count = max(0, len(pay_transactions) - len(refund_transactions))
        
        # 计算净利润
        profit = Decimal('0')
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
        
        profit = max(Decimal('0'), profit)
        
        return {
            'revenue': revenue,
            'profit': profit,
            'order_count': order_count
        }
    
    def settle_stock_market(
        self,
        event_id: int,
        fee_rate: float = 0.05
    ) -> Dict:
        """
        期末一键结算（使用事务保证一致性）
        
        计算逻辑：
        1. 全局奖金池 = (全场买股总金额) * (1 - fee_rate)
        2. 摊位分 = 0.2 * 营业额 + 0.6 * 净利润 + 0.2 * 订单数
        3. 分红占比 = 该摊位分 / 全场总分
        4. 最终股价 = (奖金池 * 占比) / 该摊位售出股数
        
        所有金额以"元"为单位。
        """
        # 1. 验证活动
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise ResourceNotFoundError(f"活动不存在: {event_id}")
        
        # 2. 查询所有订单
        orders = self.db.query(StockOrder).filter(
            StockOrder.event_id == event_id
        ).all()
        
        if not orders:
            raise BusinessLogicError(f"活动 {event_id} 没有股票订单")
        
        # 检查是否已结算
        if any(order.status == 'settled' for order in orders):
            raise BusinessLogicError(f"活动 {event_id} 已完成结算")
        
        # 3. 计算全局奖金池（元）
        total_investment = sum(float(order.total_amount) for order in orders)
        fee_rate_decimal = Decimal(str(fee_rate))
        global_pool = Decimal(str(total_investment)) * (1 - fee_rate_decimal)
        fee_collected = Decimal(str(total_investment)) - global_pool
        
        logger.info(
            f"结算开始: event_id={event_id}, total_investment={total_investment}元, "
            f"fee_rate={fee_rate}, global_pool={global_pool}元"
        )
        
        # 4. 按摊位聚合订单
        booth_orders: Dict[int, list] = {}
        for order in orders:
            if order.booth_id not in booth_orders:
                booth_orders[order.booth_id] = []
            booth_orders[order.booth_id].append(order)
        
        # 5. 计算每个摊位的经营分
        booth_scores = []
        for booth_id, booth_order_list in booth_orders.items():
            booth = self.db.query(Booth).filter(Booth.id == booth_id).first()
            if not booth:
                continue
            
            perf = self.calculate_booth_performance(booth_id, event_id)
            
            # 摊位分 = 0.2 * 营业额 + 0.6 * 净利润 + 0.2 * 订单数
            score = (
                Decimal('0.2') * perf['revenue'] +
                Decimal('0.6') * perf['profit'] +
                Decimal('0.2') * perf['order_count']
            )
            
            sold_shares = sum(o.shares for o in booth_order_list)
            booth_investment = sum(float(o.total_amount) for o in booth_order_list)
            
            booth_scores.append({
                'booth': booth,
                'orders': booth_order_list,
                'revenue': perf['revenue'],
                'profit': perf['profit'],
                'order_count': perf['order_count'],
                'score': score,
                'sold_shares': sold_shares,
                'booth_investment': Decimal(str(booth_investment))
            })
        
        # 6. 计算总分
        total_score = sum(b['score'] for b in booth_scores)
        
        if total_score == 0:
            raise BusinessLogicError("全场摊位总分为0，无法结算")
        
        # 7. 计算每个摊位的最终股价并更新订单
        booth_results = []
        try:
            for booth_data in booth_scores:
                booth = booth_data['booth']
                score = booth_data['score']
                sold_shares = booth_data['sold_shares']
                
                # 分红占比
                ratio = score / total_score
                
                # 该摊位分得的奖金（元）
                booth_pool = global_pool * ratio
                
                # 最终每股价格（元）
                if sold_shares > 0:
                    final_price = (booth_pool / sold_shares).quantize(Decimal('0.01'))
                else:
                    final_price = Decimal('0.00')
                
                # 更新该摊位的所有订单
                for order in booth_data['orders']:
                    order.settlement_price = final_price
                    order.settlement_amount = final_price * order.shares
                    order.status = 'settled'
                    order.settled_at = datetime.now(timezone.utc)
                
                booth_results.append({
                    'booth_id': booth.id,
                    'booth_name': booth.name,
                    'class_name': booth.class_name,
                    'revenue': float(booth_data['revenue']),
                    'profit': float(booth_data['profit']),
                    'order_count': booth_data['order_count'],
                    'score': score,
                    'ratio': ratio,
                    'sold_shares': sold_shares,
                    'total_investment': float(booth_data['booth_investment']),
                    'final_price': float(final_price)
                })
            
            # 8. 提交事务
            self.db.commit()
            
            # 按分数降序排序
            booth_results.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(
                f"结算完成: event_id={event_id}, booth_count={len(booth_results)}, "
                f"global_pool={global_pool}元"
            )
            
            return {
                'success': True,
                'event_id': event_id,
                'global_pool': float(global_pool),
                'total_investment': total_investment,
                'fee_collected': float(fee_collected),
                'total_score': total_score,
                'booth_count': len(booth_results),
                'booths': booth_results,
                'settled_at': datetime.now(timezone.utc)
            }
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"结算失败: {e}", exc_info=True)
            raise
    
    # ============ Statistics ============
    
    def get_market_stats(self, event_id: int) -> Dict:
        """获取股市统计数据（金额为元）"""
        orders = self.db.query(StockOrder).filter(
            StockOrder.event_id == event_id
        ).all()
        
        # 买入订单统计
        buy_orders = [o for o in orders if o.status in ('holding', 'settled')]
        total_investment = sum(float(o.total_amount) for o in buy_orders)
        fee_rate = Decimal('0.05')
        global_pool = Decimal(str(total_investment)) * (1 - fee_rate)
        fee_collected = Decimal(str(total_investment)) * fee_rate
        
        total_investors = len(set(o.participant_id for o in buy_orders))
        total_booths = len(set(o.booth_id for o in buy_orders))
        is_settled = any(o.status == 'settled' for o in orders)
        
        # 抛售订单统计
        sold_orders = [o for o in orders if o.status == 'sold']
        total_sold_orders = len(sold_orders)
        total_sold_shares = sum(o.shares for o in sold_orders)
        total_sold_amount = sum(float(o.settlement_amount) for o in sold_orders if o.settlement_amount)
        
        return {
            'event_id': event_id,
            'total_investment': total_investment,
            'total_investment_yuan': total_investment,
            'global_pool': float(global_pool),
            'global_pool_yuan': float(global_pool),
            'fee_collected': float(fee_collected),
            'fee_collected_yuan': float(fee_collected),
            'total_orders': len(buy_orders),
            'total_investors': total_investors,
            'total_booths': total_booths,
            'is_settled': is_settled,
            'total_sold_orders': total_sold_orders,
            'total_sold_shares': total_sold_shares,
            'total_sold_amount': total_sold_amount,
        }
    
    def get_booth_stock_stats(self, booth_id: int, event_id: int) -> Dict:
        """获取摊位股票统计"""
        booth = self.db.query(Booth).filter(Booth.id == booth_id).first()
        if not booth:
            raise ResourceNotFoundError(f"摊位不存在: {booth_id}")
        
        orders = self.db.query(StockOrder).filter(
            and_(
                StockOrder.booth_id == booth_id,
                StockOrder.event_id == event_id
            )
        ).all()
        
        sold_shares = sum(o.shares for o in orders)
        total_investment = sum(float(o.total_amount) for o in orders)
        investor_count = len(set(o.participant_id for o in orders))
        is_settled = any(o.status == 'settled' for o in orders)
        
        result = {
            'booth_id': booth_id,
            'booth_name': booth.name,
            'class_name': booth.class_name,
            'sold_shares': sold_shares,
            'total_investment': total_investment,
            'total_investment_yuan': total_investment,
            'investor_count': investor_count,
            'current_price': float(DEFAULT_STOCK_PRICE),
            'is_settled': is_settled,
            'final_price': None,
            'final_price_yuan': None
        }
        
        if is_settled and orders:
            settled_order = next((o for o in orders if o.settlement_price), None)
            if settled_order:
                result['final_price'] = float(settled_order.settlement_price)
                result['final_price_yuan'] = float(settled_order.settlement_price)
        
        return result
