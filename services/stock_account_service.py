"""
Stock Market Service - Business logic for stock trading.

全局奖金池动态定价模型（Pari-mutuel 6维度版 + 做市商卖出机制 + 虚拟流动性）：
- 浮动买入价 = 当前动态股价（实时变化）
- 做市商卖出价 = 当前动态股价 × 折扣系数（默认0.9，即90%）
- 所有学生买股票的钱汇总成全局资金池
- 官方扣除手续费（5%）
- 摊位根据6维度经营表现计算综合分：
  · 营业额 20% — 总收入
  · 净利润 25% — 收入减成本
  · 人流量 15% — 订单数
  · 客单价 15% — 平均每单金额（产品竞争力）
  · 投资人数 10% — 市场信心指标
  · 增长率 15% — 近期vs历史表现趋势
- 摊位分到的资金 = 池子 × (摊位分 / 总分)
- 最终股价 = (摊位真实资金 + 虚拟资金) / (当前持仓股数 + 虚拟股数)

关键设计：
- 虚拟流动性（Virtual Liquidity）：每个摊位有50股虚拟底仓 + 对应初始价资金
  · 降低单笔交易对价格的冲击（买入不会暴跌，卖出不会暴涨）
  · 无交易时价格自然回归初始价
  · 交易量越大，真实资金池主导越强，虚拟部分影响越弱
- 卖出（抛售）使用做市商折扣机制，卖出价 = 动态股价 × 0.9
- sold 订单从股数分母中移除，卖出行为不影响剩余持仓者的股价
- 资金池分子仍包含所有历史买入金额（holding + sold），保证池子不缩水
- 零和博弈：学生赚的钱来自其他学生亏的钱，官方稳赚手续费 + 做市商价差
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Tuple
import logging

from models.stock_account import StockOrder
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

# 初始发行价
INITIAL_STOCK_PRICE = Decimal('5.00')

# 官方手续费率 (5%)
OFFICIAL_FEE_RATE = Decimal('0.05')

# 做市商卖出折扣系数（卖出价 = 当前动态股价 × SELL_DISCOUNT_FACTOR）
# 0.9 表示卖出价为买入价的90%，10%为做市商价差（防止频繁套利）
SELL_DISCOUNT_FACTOR = Decimal('0.90')

# 虚拟流动性股数（每个摊位的虚拟底仓）
# 作用：稀释单笔交易对股价的冲击，值越大价格越稳定
# 相当于做市商为每个摊位预先提供的流动性
# 设为 50 表示：即使只有 1 人买了 1 股，分母也是 51 而非 1，避免极端波动
VIRTUAL_LIQUIDITY_SHARES = 50

# 综合分权重配置（6维度评分）
SCORE_WEIGHTS = {
    'revenue': Decimal('0.20'),        # 营业额 20%
    'profit': Decimal('0.25'),         # 净利润 25%
    'traffic': Decimal('0.15'),        # 人流量 15%
    'avg_ticket': Decimal('0.15'),     # 客单价 15%（高客单价=产品有竞争力）
    'investor_count': Decimal('0.10'), # 投资人数 10%（市场信心指标）
    'growth': Decimal('0.15'),         # 增长率 15%（近期表现趋势）
}


class StockAccountService:
    """股票交易服务类（全局彩池模式）"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 全局资金池计算 ====================
    
    def calculate_global_pool(self, event_id: int) -> Dict:
        """
        计算全局资金池
        
        Pool = (Σ Q_i × P_0) × (1 - F)
        Q_i = 摊位i的总买入股数
        P_0 = 初始发行价
        F = 官方手续费率
        """
        # 获取所有订单
        orders = self.db.query(StockOrder).filter(
            StockOrder.event_id == event_id,
            StockOrder.status.in_(['holding', 'settled', 'sold'])
        ).all()
        
        # 计算总投入（买入金额）
        total_investment = sum(float(o.total_amount) for o in orders)
        
        # 官方手续费
        fee = total_investment * float(OFFICIAL_FEE_RATE)
        
        # 净池（给学生的分红池）
        net_pool = total_investment - fee
        
        return {
            'total_investment': total_investment,
            'fee': fee,
            'net_pool': net_pool,
            'order_count': len(orders),
            'investor_count': len(set(o.participant_id for o in orders)),
        }
    
    # ==================== 摊位综合分计算 ====================
    
    def calculate_booth_score(self, booth_id: int, event_id: int) -> Dict:
        """
        计算摊位综合经营分（6维度）
        
        S_i = Σ(weight_k × norm_k) for k in [revenue, profit, traffic, avg_ticket, investor_count, growth]
        """
        # 确保批量缓存已加载
        if not getattr(self, '_booth_data_cache', None):
            all_booths = self.db.query(Booth).filter(Booth.event_id == event_id).all()
            if not all_booths:
                all_booths = self.db.query(Booth).filter(Booth.status == 'active').all()
            booth_ids = [b.id for b in all_booths]
            self._batch_load_booth_data(booth_ids, event_id)
        
        cache = getattr(self, '_booth_data_cache', {})
        data = cache.get(booth_id, {'revenue': 0, 'profit': 0, 'traffic': 0, 'avg_ticket': 0, 'investor_count': 0, 'growth': 0})
        
        # 计算全场总和（用于归一化）
        totals = {}
        for key in SCORE_WEIGHTS:
            totals[key] = sum(d.get(key, 0) for d in cache.values()) or 1
        
        # 归一化 + 加权
        score = 0.0
        for key, weight in SCORE_WEIGHTS.items():
            norm = data.get(key, 0) / totals[key] if totals[key] > 0 else 0
            score += float(weight) * norm
        
        return {
            'revenue': data.get('revenue', 0),
            'profit': data.get('profit', 0),
            'traffic': data.get('traffic', 0),
            'avg_ticket': data.get('avg_ticket', 0),
            'investor_count': data.get('investor_count', 0),
            'growth': data.get('growth', 0),
            'score': score,
        }
    
    def _get_booth_revenue(self, booth_id: int, event_id: int) -> float:
        """获取摊位总收入（优先使用批量缓存）"""
        cache = getattr(self, '_booth_data_cache', None)
        if cache and booth_id in cache:
            return cache[booth_id]['revenue']
        from models.transaction import Transaction
        result = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.event_id == event_id,
            Transaction.booth_id == booth_id,
            Transaction.type.in_(['pay', 'cash_payment']),
            Transaction.amount > 0
        ).scalar()
        return float(result) if result else 0.0
    
    def _get_booth_profit(self, booth_id: int, event_id: int) -> float:
        """获取摊位利润（优先使用批量缓存）"""
        cache = getattr(self, '_booth_data_cache', None)
        if cache and booth_id in cache:
            return cache[booth_id]['profit']
        revenue = self._get_booth_revenue(booth_id, event_id)
        try:
            from models.cost_evidence import CostEvidence
            cost_records = self.db.query(CostEvidence).filter(
                CostEvidence.booth_id == booth_id,
                CostEvidence.status == 'approved'
            ).all()
            if cost_records:
                total_cost = sum(float(c.amount) for c in cost_records)
                return max(0, revenue - total_cost)
        except Exception:
            pass
        return revenue * 0.70
    
    def _get_booth_traffic(self, booth_id: int, event_id: int) -> int:
        """获取摊位人流（优先使用批量缓存）"""
        cache = getattr(self, '_booth_data_cache', None)
        if cache and booth_id in cache:
            return cache[booth_id]['traffic']
        from models.transaction import Transaction
        return self.db.query(Transaction).filter(
            Transaction.event_id == event_id,
            Transaction.booth_id == booth_id,
            Transaction.type.in_(['pay', 'cash_payment'])
        ).count()
    
    def _batch_load_booth_data(self, booth_ids: List[int], event_id: int):
        """
        批量加载所有摊位的经营数据（6维度）
        结果缓存到 self._booth_data_cache 供后续方法使用
        
        维度：revenue, profit, traffic, avg_ticket, investor_count, growth
        """
        from models.transaction import Transaction
        
        # 一次查询：按摊位聚合收入和人流
        rows = self.db.query(
            Transaction.booth_id,
            func.sum(Transaction.amount).label('revenue'),
            func.count(Transaction.id).label('traffic')
        ).filter(
            Transaction.event_id == event_id,
            Transaction.booth_id.in_(booth_ids),
            Transaction.type.in_(['pay', 'cash_payment']),
            Transaction.amount > 0
        ).group_by(Transaction.booth_id).all()
        
        cache: Dict[int, Dict] = {
            bid: {
                'revenue': 0.0, 'profit': 0.0, 'traffic': 0,
                'avg_ticket': 0.0, 'investor_count': 0, 'growth': 0.0
            } for bid in booth_ids
        }
        for row in rows:
            revenue = float(row[1]) if row[1] else 0.0
            traffic = int(row[2]) if row[2] else 0
            cache[row[0]]['revenue'] = revenue
            cache[row[0]]['traffic'] = traffic
            # 客单价 = 总收入 / 订单数
            cache[row[0]]['avg_ticket'] = revenue / traffic if traffic > 0 else 0.0
        
        # 批量获取成本
        cost_map: Dict[int, float] = {}
        try:
            from models.cost_evidence import CostEvidence
            cost_rows = self.db.query(
                CostEvidence.booth_id,
                func.sum(CostEvidence.amount)
            ).filter(
                CostEvidence.booth_id.in_(booth_ids),
                CostEvidence.status == 'approved'
            ).group_by(CostEvidence.booth_id).all()
            cost_map = {r[0]: float(r[1]) for r in cost_rows if r[1]}
        except Exception:
            pass
        
        # 计算利润
        for bid in booth_ids:
            revenue = cache[bid]['revenue']
            if bid in cost_map:
                cache[bid]['profit'] = max(0.0, revenue - cost_map[bid])
            else:
                cache[bid]['profit'] = revenue * 0.70
        
        # 批量获取投资人数（每个摊位有多少不同的投资者）
        investor_rows = self.db.query(
            StockOrder.booth_id,
            func.count(func.distinct(StockOrder.participant_id))
        ).filter(
            StockOrder.event_id == event_id,
            StockOrder.booth_id.in_(booth_ids),
            StockOrder.status.in_(['holding', 'sold'])
        ).group_by(StockOrder.booth_id).all()
        
        for row in investor_rows:
            cache[row[0]]['investor_count'] = int(row[1]) if row[1] else 0
        
        # 计算增长率：最近30分钟的交易额 vs 之前的交易额
        from core.timezone import CST
        now = datetime.now(CST)
        recent_cutoff = now - timedelta(minutes=30)
        
        recent_rows = self.db.query(
            Transaction.booth_id,
            func.sum(Transaction.amount).label('recent_revenue')
        ).filter(
            Transaction.event_id == event_id,
            Transaction.booth_id.in_(booth_ids),
            Transaction.type.in_(['pay', 'cash_payment']),
            Transaction.amount > 0,
            Transaction.created_at >= recent_cutoff
        ).group_by(Transaction.booth_id).all()
        
        for row in recent_rows:
            bid = row[0]
            recent_rev = float(row[1]) if row[1] else 0.0
            total_rev = cache[bid]['revenue']
            older_rev = total_rev - recent_rev
            # 增长率 = 近期收入 / 历史收入（>1表示加速增长）
            if older_rev > 0:
                cache[bid]['growth'] = recent_rev / older_rev
            elif recent_rev > 0:
                cache[bid]['growth'] = 2.0  # 从0到有收入，视为高增长
            else:
                cache[bid]['growth'] = 0.0
        
        self._booth_data_cache = cache
    
    # ==================== 全局彩池定价 ====================
    
    def calculate_all_booth_prices(self, event_id: int) -> Dict:
        """
        计算所有摊位的最终股价（完整版，含详细数据）
        
        使用 Pari-mutuel 彩池模型：
        Final Price_i = (Pool × Ratio_i) / Q_i
        Ratio_i = S_i / ΣS_j
        """
        # 1. 获取所有活跃摊位
        booths = self.db.query(Booth).filter(
            Booth.event_id == event_id,
            Booth.status == 'active'
        ).all()
        if not booths:
            booths = self.db.query(Booth).filter(
                Booth.status == 'active'
            ).all()
        
        if not booths:
            return {'pool_info': {'total_investment': 0, 'fee': 0, 'net_pool': 0}, 'booths': []}
        
        # 2. 计算全局资金池
        pool_info = self.calculate_global_pool(event_id)
        net_pool = pool_info['net_pool']
        
        # 3. 获取动态价格（使用核心引擎）
        prices = self._calculate_pari_mutuel_prices(event_id)
        
        # 4. 获取每个摊位的详细数据（仅 holding 订单计入当前持仓）
        orders = self.db.query(StockOrder).filter(
            StockOrder.event_id == event_id,
            StockOrder.status == 'holding'
        ).all()
        
        booth_shares: Dict[int, int] = {}
        for o in orders:
            if o.booth_id not in booth_shares:
                booth_shares[o.booth_id] = 0
            booth_shares[o.booth_id] += o.shares
        
        # 5. 构建结果
        results = []
        for booth in booths:
            shares = booth_shares.get(booth.id, 0)
            current_price = prices.get(booth.id, float(INITIAL_STOCK_PRICE))
            revenue = self._get_booth_revenue(booth.id, event_id)
            profit = self._get_booth_profit(booth.id, event_id)
            traffic = self._get_booth_traffic(booth.id, event_id)
            
            # 涨跌幅
            price_change = (current_price - float(INITIAL_STOCK_PRICE)) / float(INITIAL_STOCK_PRICE) * 100
            
            results.append({
                'booth_id': booth.id,
                'booth_name': booth.name,
                'class_name': booth.class_name or '',
                'shares': shares,
                'revenue': revenue,
                'profit': profit,
                'traffic': traffic,
                'current_price': current_price,
                'initial_price': float(INITIAL_STOCK_PRICE),
                'price_change': round(price_change, 2),
            })
        
        # 按股价降序排列
        results.sort(key=lambda x: x['current_price'], reverse=True)
        
        return {
            'pool_info': pool_info,
            'booths': results,
        }
    
    # ==================== 实时动态股价（Pari-mutuel 模型） ====================
    
    def get_dynamic_price(self, booth_id: int, event_id: int) -> float:
        """
        获取单个摊位的实时动态股价（Pari-mutuel 模型）
        内部调用 get_all_dynamic_prices 利用缓存。
        """
        try:
            prices = self.get_all_dynamic_prices(event_id)
            return prices.get(booth_id, float(INITIAL_STOCK_PRICE))
        except Exception as e:
            logger.warning(f"动态股价计算失败(booth={booth_id}): {e}")
            return float(INITIAL_STOCK_PRICE)
    
    def get_all_dynamic_prices(self, event_id: int) -> Dict[int, float]:
        """
        获取所有摊位的实时动态股价（Pari-mutuel 模型）
        结果缓存在实例上，同一请求内不重复计算。
        
        Returns:
            Dict[booth_id, price]: 摊位ID → 当前股价
        """
        # 同一实例内缓存
        cache_key = '_price_cache'
        if hasattr(self, cache_key):
            return getattr(self, cache_key)
        
        try:
            prices = self._calculate_pari_mutuel_prices(event_id)
            setattr(self, cache_key, prices)
            return prices
        except Exception as e:
            logger.warning(f"批量动态股价计算失败: {e}")
            return {}
    
    def _calculate_pari_mutuel_prices(self, event_id: int) -> Dict[int, float]:
        """
        核心：Pari-mutuel 彩池定价引擎（6维度版 + 虚拟流动性）
        
        设计原则：
        - 浮动买入价 = 当前动态股价
        - 做市商卖出价 = 动态股价 × 折扣系数
        - 6维度综合评分：营业额、利润、人流、客单价、投资人数、增长率
        - 虚拟流动性：每个摊位有虚拟底仓，降低单笔交易对价格的冲击
        - 零和博弈：学生赚的钱来自其他学生亏的钱
        - 官方稳赚5%手续费 + 10%做市商价差
        
        五步法：
        1. 全局资金池 Pool = Σ(历史买入金额) × (1 - F)
        2. 摊位综合分 S_i = 6维度归一化加权
        3. 分红占比 Ratio_i = S_i / ΣS_j
        4. 摊位真实资金 = Pool × Ratio_i
        5. 最终股价 = (真实资金 + 虚拟资金) / (真实持仓 + 虚拟股数)
        
        虚拟流动性效果：
        - 无交易时：价格 = 虚拟资金/虚拟股数 = 初始价
        - 少量交易：价格 ≈ 初始价（微幅波动）
        - 大量交易：真实资金池主导，虚拟部分影响减弱
        """
        # 获取所有活跃摊位
        all_booths = self.db.query(Booth).filter(
            Booth.event_id == event_id
        ).all()
        if not all_booths:
            all_booths = self.db.query(Booth).filter(
                Booth.status == 'active'
            ).all()
        
        if not all_booths:
            return {}
        
        booth_ids = [b.id for b in all_booths]
        
        # 获取当前持仓订单（仅 holding，sold 不再计入分母）
        holding_orders = self.db.query(StockOrder).filter(
            StockOrder.event_id == event_id,
            StockOrder.status == 'holding'
        ).all()
        
        # 获取所有历史订单（holding + sold）用于计算资金池（分子）
        all_orders = self.db.query(StockOrder).filter(
            StockOrder.event_id == event_id,
            StockOrder.status.in_(['holding', 'sold'])
        ).all()
        
        # 按摊位统计当前持仓股数（仅 holding，sold 已移除）
        booth_shares: Dict[int, int] = {bid: 0 for bid in booth_ids}
        for o in holding_orders:
            if o.booth_id in booth_shares:
                booth_shares[o.booth_id] += o.shares
        
        # 第一步：全局资金池（基于所有历史买入金额）
        total_investment = sum(float(o.total_amount) for o in all_orders)
        if total_investment == 0:
            # 没有任何交易历史，全部返回初始价
            return {bid: float(INITIAL_STOCK_PRICE) for bid in booth_ids}
        
        # Pool = Σ(所有历史买入金额) × (1 - F)
        # 注意：sold 订单的买入金额仍计入池子，保证池子不因卖出而缩水
        pool = total_investment * (1 - float(OFFICIAL_FEE_RATE))
        
        # 第二步：批量加载所有摊位经营数据（6维度）
        self._batch_load_booth_data(booth_ids, event_id)
        
        booth_raw_data: Dict[int, Dict] = {}
        totals = {'revenue': 0.0, 'profit': 0.0, 'traffic': 0, 'avg_ticket': 0.0, 'investor_count': 0, 'growth': 0.0}
        
        for booth in all_booths:
            data = getattr(self, '_booth_data_cache', {}).get(booth.id, {
                'revenue': 0.0, 'profit': 0.0, 'traffic': 0,
                'avg_ticket': 0.0, 'investor_count': 0, 'growth': 0.0
            })
            booth_raw_data[booth.id] = data
            for key in totals:
                totals[key] += data.get(key, 0)
        
        # 第三步：归一化 + 加权计算综合分（6维度）
        booth_scores: Dict[int, float] = {}
        total_score = 0.0
        
        for booth in all_booths:
            data = booth_raw_data[booth.id]
            
            # 归一化（各项除以全场总和，转为百分比）
            norm_r = data['revenue'] / totals['revenue'] if totals['revenue'] > 0 else 0
            norm_p = data['profit'] / totals['profit'] if totals['profit'] > 0 else 0
            norm_t = data['traffic'] / totals['traffic'] if totals['traffic'] > 0 else 0
            norm_a = data['avg_ticket'] / totals['avg_ticket'] if totals['avg_ticket'] > 0 else 0
            norm_i = data['investor_count'] / totals['investor_count'] if totals['investor_count'] > 0 else 0
            norm_g = data['growth'] / totals['growth'] if totals['growth'] > 0 else 0
            
            # 6维度加权综合分
            score = (
                float(SCORE_WEIGHTS['revenue']) * norm_r +
                float(SCORE_WEIGHTS['profit']) * norm_p +
                float(SCORE_WEIGHTS['traffic']) * norm_t +
                float(SCORE_WEIGHTS['avg_ticket']) * norm_a +
                float(SCORE_WEIGHTS['investor_count']) * norm_i +
                float(SCORE_WEIGHTS['growth']) * norm_g
            )
            
            # 保底分（防止完全没经营数据的摊位分为0）
            score = max(score, 0.001)
            
            booth_scores[booth.id] = score
            total_score += score
        
        if total_score == 0:
            total_score = 1.0
        
        # 第四步：计算最终股价（含虚拟流动性缓冲）
        # 虚拟流动性：每个摊位的分母加上虚拟底仓股数，降低单笔交易对价格的冲击
        # 同时在分子端为虚拟股数注入对应的初始价资金，保证无交易时股价 = 初始价
        virtual_shares = VIRTUAL_LIQUIDITY_SHARES
        virtual_pool_per_booth = float(INITIAL_STOCK_PRICE) * virtual_shares  # 虚拟注入资金
        
        prices: Dict[int, float] = {}
        for booth in all_booths:
            shares = booth_shares.get(booth.id, 0)
            score = booth_scores.get(booth.id, 0)
            
            # 分红占比
            ratio = score / total_score
            
            # 摊位从真实资金池分到的资金
            booth_pool = pool * ratio
            
            # 加入虚拟流动性：分子加虚拟资金，分母加虚拟股数
            # 效果：当真实交易量小时，价格趋近初始价；交易量大时，真实资金池主导价格
            effective_pool = booth_pool + virtual_pool_per_booth
            effective_shares = shares + virtual_shares
            
            # 最终股价 = (真实资金池分配 + 虚拟资金) / (真实持仓 + 虚拟股数)
            price = effective_pool / effective_shares
            
            # 股价下限保护（不低于0.5元）
            price = max(0.50, price)
            prices[booth.id] = round(price, 2)
        
        return prices
    
    # 兼容旧方法名
    def get_realtime_price(self, booth_id: int, event_id: int) -> float:
        """兼容旧接口，内部调用 get_dynamic_price"""
        return self.get_dynamic_price(booth_id, event_id)
    
    # ==================== 公示：股价计算明细 ====================
    
    def get_price_breakdown(self, event_id: int) -> Dict:
        """
        获取所有摊位股价的详细计算过程（公示用）。
        
        返回内容包括：
        - 资金池信息（总投入、手续费、净池）
        - 权重配置
        - 各摊位的6维度原始数据、归一化值、加权得分
        - 最终股价、分红占比、持股数
        - 全场总和与排名
        """
        # 获取所有活跃摊位（同 _calculate_pari_mutuel_prices 逻辑）
        all_booths = self.db.query(Booth).filter(
            Booth.event_id == event_id
        ).all()
        if not all_booths:
            all_booths = self.db.query(Booth).filter(
                Booth.status == 'active'
            ).all()
        
        if not all_booths:
            return {
                'pool_info': {'total_investment': 0, 'fee': 0, 'net_pool': 0, 'fee_rate': float(OFFICIAL_FEE_RATE)},
                'weights': {k: float(v) for k, v in SCORE_WEIGHTS.items()},
                'totals': {},
                'booths': [],
                'initial_price': float(INITIAL_STOCK_PRICE),
            }
        
        booth_ids = [b.id for b in all_booths]
        
        # 当前持仓订单（仅 holding，用于计算股数分母）
        holding_orders = self.db.query(StockOrder).filter(
            StockOrder.event_id == event_id,
            StockOrder.status == 'holding'
        ).all()
        
        # 所有历史订单（holding + sold，用于计算资金池分子）
        all_orders = self.db.query(StockOrder).filter(
            StockOrder.event_id == event_id,
            StockOrder.status.in_(['holding', 'sold'])
        ).all()
        
        booth_shares: Dict[int, int] = {bid: 0 for bid in booth_ids}
        for o in holding_orders:
            if o.booth_id in booth_shares:
                booth_shares[o.booth_id] += o.shares
        
        total_investment = sum(float(o.total_amount) for o in all_orders)
        fee = total_investment * float(OFFICIAL_FEE_RATE)
        pool = total_investment - fee
        
        # 加载6维度数据
        self._batch_load_booth_data(booth_ids, event_id)
        booth_raw_data: Dict[int, Dict] = {}
        totals = {'revenue': 0.0, 'profit': 0.0, 'traffic': 0, 'avg_ticket': 0.0, 'investor_count': 0, 'growth': 0.0}
        
        for booth in all_booths:
            data = getattr(self, '_booth_data_cache', {}).get(booth.id, {
                'revenue': 0.0, 'profit': 0.0, 'traffic': 0,
                'avg_ticket': 0.0, 'investor_count': 0, 'growth': 0.0
            })
            booth_raw_data[booth.id] = data
            for key in totals:
                totals[key] += data.get(key, 0)
        
        # 计算各摊位归一化值与综合分
        booth_breakdown: List[Dict] = []
        booth_scores: Dict[int, float] = {}
        total_score = 0.0
        
        for booth in all_booths:
            data = booth_raw_data[booth.id]
            
            norms = {
                'revenue': data['revenue'] / totals['revenue'] if totals['revenue'] > 0 else 0,
                'profit': data['profit'] / totals['profit'] if totals['profit'] > 0 else 0,
                'traffic': data['traffic'] / totals['traffic'] if totals['traffic'] > 0 else 0,
                'avg_ticket': data['avg_ticket'] / totals['avg_ticket'] if totals['avg_ticket'] > 0 else 0,
                'investor_count': data['investor_count'] / totals['investor_count'] if totals['investor_count'] > 0 else 0,
                'growth': data['growth'] / totals['growth'] if totals['growth'] > 0 else 0,
            }
            
            # 加权综合分
            weighted = {k: float(SCORE_WEIGHTS[k]) * v for k, v in norms.items()}
            score = sum(weighted.values())
            score = max(score, 0.001)  # 保底分
            
            booth_scores[booth.id] = score
            total_score += score
            
            booth_breakdown.append({
                'booth_id': booth.id,
                'booth_name': booth.name,
                'class_name': booth.class_name or '',
                'shares': booth_shares.get(booth.id, 0),
                'raw': {k: round(v, 4) for k, v in data.items()},
                'normalized': {k: round(v, 6) for k, v in norms.items()},
                'weighted': {k: round(v, 6) for k, v in weighted.items()},
                'score': round(score, 6),
            })
        
        if total_score == 0:
            total_score = 1.0
        
        # 计算最终股价与分红占比（含虚拟流动性）
        virtual_shares = VIRTUAL_LIQUIDITY_SHARES
        virtual_pool_per_booth = float(INITIAL_STOCK_PRICE) * virtual_shares
        
        for item in booth_breakdown:
            score = item['score']
            shares = item['shares']
            ratio = score / total_score
            booth_pool = pool * ratio
            
            # 虚拟流动性缓冲
            effective_pool = booth_pool + virtual_pool_per_booth
            effective_shares = shares + virtual_shares
            price = effective_pool / effective_shares
            
            price = max(0.50, price)
            base_price = float(INITIAL_STOCK_PRICE)
            
            item['ratio'] = round(ratio, 6)
            item['booth_pool'] = round(booth_pool, 2)
            item['virtual_pool'] = round(virtual_pool_per_booth, 2)
            item['effective_shares'] = effective_shares
            item['current_price'] = round(price, 2)
            item['base_price'] = base_price
            item['change_percent'] = round((price - base_price) / base_price * 100, 2)
        
        # 按综合分降序
        booth_breakdown.sort(key=lambda x: x['score'], reverse=True)
        for idx, item in enumerate(booth_breakdown, 1):
            item['rank'] = idx
        
        return {
            'pool_info': {
                'total_investment': round(total_investment, 2),
                'fee': round(fee, 2),
                'net_pool': round(pool, 2),
                'fee_rate': float(OFFICIAL_FEE_RATE),
                'sell_discount_factor': float(SELL_DISCOUNT_FACTOR),
                'virtual_liquidity_shares': VIRTUAL_LIQUIDITY_SHARES,
                'order_count': len(all_orders),
                'holding_count': len(holding_orders),
                'investor_count': len(set(o.participant_id for o in all_orders)),
            },
            'weights': {k: float(v) for k, v in SCORE_WEIGHTS.items()},
            'totals': {k: round(v, 4) for k, v in totals.items()},
            'total_score': round(total_score, 6),
            'initial_price': float(INITIAL_STOCK_PRICE),
            'booths': booth_breakdown,
        }
    
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
            raise ValidationError(f"该卡片持卡人处于实名审核中，请先到管理后台完成实名审核后再进行投资操作")
        
        # 2. 查询摊位
        booth = self.db.query(Booth).filter(Booth.id == booth_id).first()
        if not booth:
            raise ResourceNotFoundError(f"摊位不存在: {booth_id}")
        
        if booth.event_id != event_id:
            raise ValidationError(f"摊位 {booth_id} 不属于活动 {event_id}")
        
        if not booth.is_active():
            raise ValidationError(f"摊位状态异常: {booth.status}")
        
        # 检查该摊位的股票是否已收盘/结算
        from models.stock import Stock as StockModel
        stock = self.db.query(StockModel).filter(StockModel.booth_id == booth_id).first()
        if stock and stock.status in ('suspended', 'settled'):
            raise ValidationError(f"该股票已{'收盘' if stock.status == 'suspended' else '结算'}，无法买入")
        
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
            
            # 4. 计算金额（浮动买入价 = 当前动态股价）
            buy_price = Decimal(str(self.get_dynamic_price(booth_id, event_id)))
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
    ) -> Tuple[int, Account, float]:
        """
        抛售股票（以当前股价结算，资金返回主账户）
        
        Args:
            card_uid: NFC卡UID
            event_id: 活动ID
            booth_id: 摊位ID
            shares: 抛售股数
            
        Returns:
            Tuple[int, Account, float]: 实际卖出股数、主账户、卖出单价
            
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
            raise ValidationError(f"该卡片持卡人处于实名审核中，请先到管理后台完成实名审核后再进行投资操作")
        
        # 2. 查询摊位
        booth = self.db.query(Booth).filter(Booth.id == booth_id).first()
        if not booth:
            raise ResourceNotFoundError(f"摊位不存在: {booth_id}")
        
        if booth.event_id != event_id:
            raise ValidationError(f"摊位 {booth_id} 不属于活动 {event_id}")
        
        # 检查该摊位的股票是否已收盘/结算
        from models.stock import Stock as StockModel
        stock = self.db.query(StockModel).filter(StockModel.booth_id == booth_id).first()
        if stock and stock.status == 'settled':
            raise ValidationError(f"该股票已结算，无法卖出")
        if stock and stock.status == 'suspended':
            raise ValidationError(f"该股票已收盘，无法卖出")
        
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
            
            # 5. 以做市商折扣价卖出（卖出价 = 当前动态股价 × 折扣系数）
            dynamic_price = Decimal(str(self.get_dynamic_price(booth_id, event_id)))
            sell_price = (dynamic_price * SELL_DISCOUNT_FACTOR).quantize(Decimal('0.01'))
            # 卖出价下限保护（不低于0.50元）
            sell_price = max(sell_price, Decimal('0.50'))
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
                    order.settled_at = datetime.now(CST)
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
                    order.settled_at = datetime.now(CST)
                    
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
            
            return shares, account, float(sell_price)
        
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
                    'current_price': self.get_dynamic_price(bid, event_id),
                }
            booth_holdings[bid]['shares'] += order.shares
            booth_holdings[bid]['total_cost'] += order.total_amount
        
        result = []
        for bh in booth_holdings.values():
            bh['total_cost'] = float(bh['total_cost'])
            bh['market_value'] = bh['shares'] * bh['current_price']
            # 做市商卖出价 = 当前股价 × 折扣系数
            bh['sell_price'] = round(max(0.50, bh['current_price'] * float(SELL_DISCOUNT_FACTOR)), 2)
            bh['sell_value'] = bh['shares'] * bh['sell_price']
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
                    order.settled_at = datetime.now(CST)
                
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
                'settled_at': datetime.now(CST)
            }
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"结算失败: {e}", exc_info=True)
            raise
    
    # ============ Market Close (收盘) ============
    
    def close_market(self, event_id: int) -> Dict:
        """
        一键收盘：暂停活动下所有股票交易。
        将所有 holding 状态的订单保持不变，但阻止新的买卖。
        通过在 event 级别标记来实现。
        """
        from models.stock import Stock
        
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise ResourceNotFoundError(f"活动不存在: {event_id}")
        
        # 将该活动下所有 active 状态的股票设为 suspended
        stocks = self.db.query(Stock).filter(
            Stock.event_id == event_id,
            Stock.status == 'active'
        ).all()
        
        if not stocks:
            # 检查是否已经收盘
            suspended = self.db.query(Stock).filter(
                Stock.event_id == event_id,
                Stock.status == 'suspended'
            ).count()
            if suspended > 0:
                raise BusinessLogicError(f"活动 {event_id} 已经收盘")
            raise BusinessLogicError(f"活动 {event_id} 没有活跃的股票")
        
        count = 0
        for stock in stocks:
            stock.status = 'suspended'
            count += 1
        
        self.db.commit()
        
        logger.info(f"收盘成功: event_id={event_id}, suspended_count={count}")
        
        return {
            'success': True,
            'event_id': event_id,
            'suspended_count': count,
            'message': f'已收盘，{count} 只股票已暂停交易'
        }
    
    # ============ Reopen Market (重新开盘) ============
    
    def reopen_market(self, event_id: int) -> Dict:
        """
        重新开盘：将活动下所有 suspended 状态的股票恢复为 active，允许买卖。
        已结算(settled)的股票不会被恢复。
        """
        from models.stock import Stock
        
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise ResourceNotFoundError(f"活动不存在: {event_id}")
        
        # 将该活动下所有 suspended 状态的股票设为 active
        stocks = self.db.query(Stock).filter(
            Stock.event_id == event_id,
            Stock.status == 'suspended'
        ).all()
        
        if not stocks:
            # 检查是否有 active 的（已经开盘了）
            active = self.db.query(Stock).filter(
                Stock.event_id == event_id,
                Stock.status == 'active'
            ).count()
            if active > 0:
                raise BusinessLogicError(f"活动 {event_id} 已经处于开盘状态")
            raise BusinessLogicError(f"活动 {event_id} 没有可恢复的股票（可能已清算）")
        
        count = 0
        for stock in stocks:
            stock.status = 'active'
            count += 1
        
        self.db.commit()
        
        logger.info(f"重新开盘成功: event_id={event_id}, reopened_count={count}")
        
        return {
            'success': True,
            'event_id': event_id,
            'reopened_count': count,
            'message': f'已重新开盘，{count} 只股票已恢复交易'
        }
    
    # ============ Full Liquidation (全部清算) ============
    
    def liquidate_market(self, event_id: int, fee_rate: float = 0.05) -> Dict:
        """
        一键全部清算：
        1. 先收盘（如果尚未收盘）
        2. 使用 Pari-mutuel 模型计算最终股价
        3. 将结算金额退还到每个参与者的主账户
        4. 标记所有订单为 settled
        """
        from models.stock import Stock
        
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise ResourceNotFoundError(f"活动不存在: {event_id}")
        
        # 检查是否已结算
        orders = self.db.query(StockOrder).filter(
            StockOrder.event_id == event_id
        ).all()
        
        if not orders:
            raise BusinessLogicError(f"活动 {event_id} 没有股票订单")
        
        if any(o.status == 'settled' for o in orders):
            raise BusinessLogicError(f"活动 {event_id} 已完成清算")
        
        # 1. 先收盘（将所有 active 股票设为 suspended）
        active_stocks = self.db.query(Stock).filter(
            Stock.event_id == event_id,
            Stock.status == 'active'
        ).all()
        for stock in active_stocks:
            stock.status = 'suspended'
        
        # 2. 获取当前动态股价作为最终结算价
        prices = self.get_all_dynamic_prices(event_id)
        
        # 3. 计算全局资金池（所有历史买入金额）
        all_invested_orders = [o for o in orders if o.status in ('holding', 'sold')]
        total_investment = sum(float(o.total_amount) for o in all_invested_orders)
        fee = total_investment * fee_rate
        net_pool = total_investment - fee
        
        # 4. 按参与者聚合，计算每人应得金额并退还（仅结算 holding 订单，sold 已在抛售时结算）
        unsettled_orders = [o for o in orders if o.status == 'holding']
        participant_returns: Dict[int, Decimal] = {}
        booth_final_prices: Dict[int, float] = {}
        
        try:
            for order in unsettled_orders:
                booth_id = order.booth_id
                final_price = Decimal(str(prices.get(booth_id, float(INITIAL_STOCK_PRICE))))
                settlement_amount = final_price * order.shares
                
                # 更新订单
                order.settlement_price = final_price
                order.settlement_amount = settlement_amount
                order.status = 'settled'
                order.settled_at = datetime.now(CST)
                
                # 累计参与者应得
                if order.participant_id not in participant_returns:
                    participant_returns[order.participant_id] = Decimal('0')
                participant_returns[order.participant_id] += settlement_amount
                
                booth_final_prices[booth_id] = float(final_price)
            
            # 5. 退还资金到参与者主账户
            returned_count = 0
            total_returned = Decimal('0')
            
            for participant_id, amount in participant_returns.items():
                account = self.db.query(Account).filter(
                    and_(
                        Account.participant_id == participant_id,
                        Account.event_id == event_id
                    )
                ).first()
                
                if account:
                    account.balance += amount
                    total_returned += amount
                    returned_count += 1
            
            # 6. 将所有股票标记为 settled
            all_stocks = self.db.query(Stock).filter(
                Stock.event_id == event_id
            ).all()
            for stock in all_stocks:
                stock.status = 'settled'
            
            self.db.commit()
            
            logger.info(
                f"全部清算完成: event_id={event_id}, "
                f"orders={len(unsettled_orders)}, participants={returned_count}, "
                f"total_returned={total_returned}元"
            )
            
            return {
                'success': True,
                'event_id': event_id,
                'total_investment': total_investment,
                'fee_collected': fee,
                'net_pool': net_pool,
                'order_count': len(unsettled_orders),
                'participant_count': returned_count,
                'total_returned': float(total_returned),
                'booth_final_prices': booth_final_prices,
                'message': f'清算完成，{returned_count} 位投资者已收到退款，共退还 ¥{float(total_returned):.2f}'
            }
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"全部清算失败: {e}", exc_info=True)
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
    
    def get_all_booth_stats(self, event_id: int) -> list:
        """获取活动下所有摊位的股票统计（包括未被购买的摊位）"""
        # 获取所有活跃摊位（优先按 event_id 查，如果没有则获取所有活跃摊位）
        all_booths = self.db.query(Booth).filter(
            Booth.event_id == event_id
        ).all()
        
        # 如果指定活动下没有摊位，尝试获取所有活跃摊位
        if not all_booths:
            all_booths = self.db.query(Booth).filter(
                Booth.status == 'active'
            ).all()
        
        if not all_booths:
            return []
        
        # 获取所有订单（不限制 event_id，因为摊位可能跨活动）
        booth_ids = [b.id for b in all_booths]
        orders = self.db.query(StockOrder).filter(
            StockOrder.booth_id.in_(booth_ids)
        ).all()
        
        # 按摊位分组
        booth_orders: Dict[int, list] = {}
        for o in orders:
            if o.booth_id not in booth_orders:
                booth_orders[o.booth_id] = []
            booth_orders[o.booth_id].append(o)
        
        results = []
        # 批量获取动态股价（避免N次重复计算）
        all_prices = self.get_all_dynamic_prices(event_id)
        
        for booth in all_booths:
            orders_list = booth_orders.get(booth.id, [])
            
            buy_orders = [o for o in orders_list if o.status in ('holding', 'settled', 'sold')]
            sold_shares = sum(o.shares for o in buy_orders)
            total_investment = sum(float(o.total_amount) for o in buy_orders)
            investor_count = len(set(o.participant_id for o in buy_orders))
            is_settled = any(o.status == 'settled' for o in orders_list)
            
            result = {
                'booth_id': booth.id,
                'booth_name': booth.name,
                'class_name': booth.class_name,
                'sold_shares': sold_shares,
                'total_investment': total_investment,
                'total_investment_yuan': total_investment,
                'investor_count': investor_count,
                'current_price': all_prices.get(booth.id, float(INITIAL_STOCK_PRICE)),
                'is_settled': is_settled,
                'final_price': None,
                'final_price_yuan': None
            }
            
            if is_settled:
                settled_order = next((o for o in orders_list if o.settlement_price), None)
                if settled_order:
                    result['final_price'] = float(settled_order.settlement_price)
                    result['final_price_yuan'] = float(settled_order.settlement_price)
            
            results.append(result)
        
        # 按总投资额降序排列
        results.sort(key=lambda x: x['total_investment'], reverse=True)
        return results

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
            'current_price': self.get_dynamic_price(booth_id, event_id),
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
