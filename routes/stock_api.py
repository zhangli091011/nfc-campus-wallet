"""
Stock API Routes - 股票交易API

核心接口：
- POST /api/stock/buy: 购买股票（直接从主账户扣款，使用悲观锁）
- POST /api/stock/settle: 期末结算（仅管理员）
- GET /api/stock/orders/{participant_id}: 查询订单
- GET /api/stock/stats/{event_id}: 市场统计

注意：/api/stock/transfer 已废弃（不再有独立投资币账户）
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict
import logging

from core.database import get_db
from core.security import get_current_user, RoleChecker
from core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    InsufficientFundsError,
    BusinessLogicError
)
from models.user import User
from services.stock_account_service import StockAccountService, INITIAL_STOCK_PRICE, SELL_DISCOUNT_FACTOR
from schemas.stock_account import (
    AccountTransferResponse,
    StockBuyRequest,
    StockBuyResponse,
    StockSellRequest,
    StockSellResponse,
    StockOrderResponse,
    StockSettlementRequest,
    StockSettlementResponse,
    BoothStockData,
    StockMarketStatsResponse,
    BoothStockStatsResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stock")


# ============ Deprecated: Account Transfer ============

@router.post(
    "/transfer",
    response_model=AccountTransferResponse,
    summary="[已废弃] 账户互转",
    description="此接口已废弃。股票购买现在直接从主账户扣款，不再需要转账。",
    deprecated=True
)
async def transfer_balance():
    """已废弃 - 不再有独立投资币账户"""
    return AccountTransferResponse(
        success=False,
        message="此接口已废弃。股票购买现在直接从主账户扣款，无需转账。"
    )


# ============ Stock Buy ============

@router.post(
    "/buy",
    response_model=StockBuyResponse,
    summary="购买股票（NFC刷卡）",
    description="直接从主账户余额购买股票（使用悲观锁防止并发超卖）"
)
async def buy_stock(
    request: StockBuyRequest,
    db: Session = Depends(get_db)
):
    """
    购买股票 - 直接从主账户扣款
    
    **安全机制**:
    - 使用数据库事务保证原子性
    - 使用悲观锁 (SELECT ... FOR UPDATE) 防止并发超卖
    - 防止余额扣成负数
    
    **购买流程**:
    1. 验证参与者和摊位
    2. 锁定主账户（悲观锁）
    3. 检查余额是否充足
    4. 扣除账户余额
    5. 写入交易流水
    6. 创建股票订单
    7. 提交事务
    """
    try:
        service = StockAccountService(db)
        order, account = service.buy_stock(
            card_uid=request.card_uid,
            event_id=request.event_id,
            booth_id=request.booth_id,
            shares=request.shares
        )
        
        return StockBuyResponse(
            success=True,
            order_id=order.id,
            booth_id=order.booth_id,
            booth_name=order.booth.name,
            shares=order.shares,
            buy_price=float(order.buy_price),
            buy_price_yuan=float(order.buy_price),
            total_amount=float(order.total_amount),
            total_amount_yuan=float(order.total_amount),
            new_balance=float(account.balance),
            new_balance_yuan=float(account.balance),
            message=f"成功购买 {order.booth.name} {order.shares}股，扣款{order.total_amount}元"
        )
    
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "RESOURCE_NOT_FOUND", "message": str(e)}
        )
    except InsufficientFundsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INSUFFICIENT_FUNDS", "message": str(e)}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"购买股票失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "购买失败"}
        )


# ============ Stock Sell ============

@router.post(
    "/sell",
    response_model=StockSellResponse,
    summary="抛售股票（NFC刷卡）",
    description="以当前股价抛售持仓股票，资金返回主账户"
)
async def sell_stock(
    request: StockSellRequest,
    db: Session = Depends(get_db)
):
    """
    抛售股票 - 以当前股价卖出，资金返回主账户
    
    **安全机制**:
    - 使用数据库事务保证原子性
    - 使用悲观锁 (SELECT ... FOR UPDATE) 防止并发问题
    - FIFO 顺序消减持仓
    
    **抛售流程**:
    1. 验证参与者和摊位
    2. 查询持仓订单
    3. 锁定主账户（悲观锁）
    4. 按 FIFO 消减持仓
    5. 资金返回主账户
    6. 写入交易流水
    7. 提交事务
    """
    try:
        service = StockAccountService(db)
        shares_sold, account, sell_price = service.sell_stock(
            card_uid=request.card_uid,
            event_id=request.event_id,
            booth_id=request.booth_id,
            shares=request.shares
        )
        
        total_amount = sell_price * shares_sold
        
        # 获取摊位名称
        from models.booth import Booth
        booth = db.query(Booth).filter(Booth.id == request.booth_id).first()
        booth_name = booth.name if booth else "未知"
        
        return StockSellResponse(
            success=True,
            booth_id=request.booth_id,
            booth_name=booth_name,
            shares_sold=shares_sold,
            sell_price=sell_price,
            sell_price_yuan=sell_price,
            total_amount=total_amount,
            total_amount_yuan=total_amount,
            new_balance=float(account.balance),
            new_balance_yuan=float(account.balance),
            message=f"成功抛售 {booth_name} {shares_sold}股，到账¥{total_amount:.2f}"
        )
    
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "RESOURCE_NOT_FOUND", "message": str(e)}
        )
    except InsufficientFundsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INSUFFICIENT_HOLDINGS", "message": str(e)}
        )
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"抛售股票失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "抛售失败"}
        )


# ============ Holdings ============

@router.get(
    "/holdings",
    summary="查询持仓汇总（按摊位聚合）"
)
async def get_holdings(
    card_uid: str = Query(..., description="NFC卡UID"),
    event_id: int = Query(..., description="活动ID"),
    db: Session = Depends(get_db)
):
    """查询参与者的持仓汇总（按摊位聚合）"""
    try:
        service = StockAccountService(db)
        holdings = service.get_participant_holdings(card_uid, event_id)
        return holdings
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "RESOURCE_NOT_FOUND", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"查询持仓失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "查询失败"}
        )


# ============ Orders ============

@router.get(
    "/orders/{participant_id}",
    response_model=List[StockOrderResponse],
    summary="查询股票订单"
)
async def get_orders(
    participant_id: int,
    event_id: Optional[int] = Query(None, description="活动ID过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查询股票订单"""
    try:
        service = StockAccountService(db)
        orders = service.get_participant_orders(participant_id, event_id)
        
        return [
            StockOrderResponse(
                id=o.id,
                event_id=o.event_id,
                participant_id=o.participant_id,
                booth_id=o.booth_id,
                booth_name=o.booth.name if o.booth else None,
                class_name=o.booth.class_name if o.booth else None,
                shares=o.shares,
                buy_price=float(o.buy_price),
                buy_price_yuan=float(o.buy_price),
                total_amount=float(o.total_amount),
                total_amount_yuan=float(o.total_amount),
                status=o.status,
                settlement_price=float(o.settlement_price) if o.settlement_price else None,
                settlement_price_yuan=float(o.settlement_price) if o.settlement_price else None,
                settlement_amount=float(o.settlement_amount) if o.settlement_amount else None,
                settlement_amount_yuan=float(o.settlement_amount) if o.settlement_amount else None,
                profit_loss=(float(o.settlement_amount) - float(o.total_amount)) if o.settlement_amount else None,
                profit_loss_yuan=(float(o.settlement_amount) - float(o.total_amount)) if o.settlement_amount else None,
                created_at=o.created_at,
                settled_at=o.settled_at
            )
            for o in orders
        ]
    
    except Exception as e:
        logger.error(f"查询订单失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "查询失败"}
        )


# ============ Market Close (收盘) ============

class MarketCloseRequest(BaseModel):
    event_id: int

@router.post(
    "/close-market",
    summary="一键收盘（暂停所有股票交易）"
)
async def close_market(
    request: MarketCloseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["event_admin", "super_admin"]))
):
    """
    一键收盘：将活动下所有股票状态设为 suspended，禁止买卖。
    股价停止变动（因为不再有新交易）。
    """
    try:
        service = StockAccountService(db)
        result = service.close_market(request.event_id)
        return result
    except (ResourceNotFoundError, BusinessLogicError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "CLOSE_MARKET_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"收盘失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "收盘失败"}
        )


# ============ Full Liquidation (全部清算) ============

class LiquidateRequest(BaseModel):
    event_id: int
    fee_rate: float = 0.05

@router.post(
    "/liquidate",
    summary="一键全部清算（结算并退还资金到参与者账户）"
)
async def liquidate_market(
    request: LiquidateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["event_admin", "super_admin"]))
):
    """
    一键全部清算：
    1. 先收盘（如果尚未收盘）
    2. 计算最终股价
    3. 将结算金额退还到每个参与者的主账户
    4. 标记所有订单为 settled
    """
    try:
        service = StockAccountService(db)
        result = service.liquidate_market(
            event_id=request.event_id,
            fee_rate=request.fee_rate
        )
        return result
    except (ResourceNotFoundError, BusinessLogicError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "LIQUIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"全部清算失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "清算失败"}
        )


# ============ Settlement ============

@router.post(
    "/settle",
    response_model=StockSettlementResponse,
    summary="期末一键结算"
)
async def settle_stock_market(
    request: StockSettlementRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["event_admin", "super_admin"]))
):
    """
    期末一键结算（所有金额以元为单位）
    """
    try:
        service = StockAccountService(db)
        result = service.settle_stock_market(
            event_id=request.event_id,
            fee_rate=request.fee_rate
        )
        
        booths_data = [
            BoothStockData(
                booth_id=b['booth_id'],
                booth_name=b['booth_name'],
                class_name=b['class_name'],
                revenue=b['revenue'],
                revenue_yuan=b['revenue'],
                profit=b['profit'],
                profit_yuan=b['profit'],
                order_count=b['order_count'],
                score=b['score'],
                ratio=b['ratio'],
                sold_shares=b['sold_shares'],
                total_investment=b['total_investment'],
                total_investment_yuan=b['total_investment'],
                final_price=b['final_price'],
                final_price_yuan=b['final_price']
            )
            for b in result['booths']
        ]
        
        return StockSettlementResponse(
            success=result['success'],
            event_id=result['event_id'],
            global_pool=result['global_pool'],
            global_pool_yuan=result['global_pool'],
            total_investment=result['total_investment'],
            total_investment_yuan=result['total_investment'],
            fee_collected=result['fee_collected'],
            fee_collected_yuan=result['fee_collected'],
            total_score=result['total_score'],
            booth_count=result['booth_count'],
            booths=booths_data,
            settled_at=result['settled_at'],
            message=f"结算完成，共 {result['booth_count']} 个摊位"
        )
    
    except (ResourceNotFoundError, BusinessLogicError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "SETTLEMENT_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"期末结算失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "结算失败"}
        )


# ============ Statistics ============

@router.get(
    "/stats/{event_id}",
    response_model=StockMarketStatsResponse,
    summary="获取股市统计数据"
)
async def get_market_stats(
    event_id: int,
    db: Session = Depends(get_db)
):
    """获取股市统计数据（无需认证，供大屏展示）"""
    try:
        service = StockAccountService(db)
        stats = service.get_market_stats(event_id)
        
        return StockMarketStatsResponse(
            event_id=stats['event_id'],
            total_investment=stats['total_investment'],
            total_investment_yuan=stats['total_investment_yuan'],
            global_pool=stats['global_pool'],
            global_pool_yuan=stats['global_pool_yuan'],
            fee_collected=stats['fee_collected'],
            fee_collected_yuan=stats['fee_collected_yuan'],
            total_orders=stats['total_orders'],
            total_investors=stats['total_investors'],
            total_booths=stats['total_booths'],
            is_settled=stats['is_settled'],
            total_sold_orders=stats.get('total_sold_orders', 0),
            total_sold_shares=stats.get('total_sold_shares', 0),
            total_sold_amount=stats.get('total_sold_amount', 0.0),
        )
    
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "查询失败"}
        )


@router.get(
    "/all-booth-stats/{event_id}",
    summary="获取活动所有摊位股票统计（大屏用）"
)
async def get_all_booth_stats(
    event_id: int,
    db: Session = Depends(get_db)
):
    """获取活动下所有摊位的股票统计数据（无需认证，供大屏展示）"""
    try:
        service = StockAccountService(db)
        stats = service.get_all_booth_stats(event_id)
        return stats
    except Exception as e:
        logger.error(f"获取所有摊位统计失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "查询失败"}
        )


@router.get(
    "/booth-stats/{booth_id}",
    response_model=BoothStockStatsResponse,
    summary="获取摊位股票统计"
)
async def get_booth_stock_stats(
    booth_id: int,
    event_id: int = Query(..., description="活动ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取摊位股票统计（金额为元）"""
    try:
        service = StockAccountService(db)
        stats = service.get_booth_stock_stats(booth_id, event_id)
        
        return BoothStockStatsResponse(
            booth_id=stats['booth_id'],
            booth_name=stats['booth_name'],
            class_name=stats['class_name'],
            sold_shares=stats['sold_shares'],
            total_investment=stats['total_investment'],
            total_investment_yuan=stats['total_investment_yuan'],
            investor_count=stats['investor_count'],
            current_price=stats['current_price'],
            is_settled=stats['is_settled'],
            final_price=stats['final_price'],
            final_price_yuan=stats['final_price_yuan']
        )
    
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "BOOTH_NOT_FOUND", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"获取摊位统计失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "查询失败"}
        )


# ============ Dynamic Prices ============

@router.get(
    "/prices/{event_id}",
    summary="获取所有摊位实时股价（Pari-mutuel 动态计算）"
)
async def get_dynamic_prices(
    event_id: int,
    db: Session = Depends(get_db)
):
    """
    获取所有摊位的实时动态股价（无需认证，供手机端和大屏展示）。
    
    股价算法：Pari-mutuel 全局彩池模型
    - Pool = (Σ Q_i × P_0) × (1 - F)
    - Score_i = α×Revenue + β×Profit + γ×Traffic（归一化加权）
    - Price_i = (Pool × Score_i/ΣScore) / Q_i
    
    Returns:
        各摊位的实时股价列表
    """
    try:
        service = StockAccountService(db)
        prices = service.get_all_dynamic_prices(event_id)
        
        # 获取摊位信息和经营数据
        from models.booth import Booth
        booths = db.query(Booth).filter(Booth.status == 'active').all()
        booth_map = {b.id: b for b in booths}
        
        # 获取6维度经营数据（复用缓存）
        booth_data_cache = getattr(service, '_booth_data_cache', {})
        
        sell_discount = float(SELL_DISCOUNT_FACTOR)
        
        result = []
        for booth_id, price in prices.items():
            booth = booth_map.get(booth_id)
            if booth:
                base_price = float(INITIAL_STOCK_PRICE)
                data = booth_data_cache.get(booth_id, {})
                sell_price = round(max(0.50, price * sell_discount), 2)
                result.append({
                    "booth_id": booth_id,
                    "booth_name": booth.name,
                    "class_name": booth.class_name or "",
                    "current_price": price,
                    "sell_price": sell_price,
                    "sell_discount": sell_discount,
                    "base_price": base_price,
                    "change_percent": round((price - base_price) / base_price * 100, 2),
                    # 6维度经营数据
                    "revenue": round(data.get('revenue', 0), 2),
                    "profit": round(data.get('profit', 0), 2),
                    "traffic": data.get('traffic', 0),
                    "avg_ticket": round(data.get('avg_ticket', 0), 2),
                    "investor_count": data.get('investor_count', 0),
                    "growth": round(data.get('growth', 0), 2),
                })
        
        # 按股价降序
        result.sort(key=lambda x: x['current_price'], reverse=True)
        return result
    
    except Exception as e:
        logger.error(f"获取动态股价失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "查询失败"}
        )


# ============ Price Breakdown (公示) ============

@router.get(
    "/price-breakdown/{event_id}",
    summary="获取股价计算明细（公示用）"
)
async def get_price_breakdown(
    event_id: int,
    db: Session = Depends(get_db)
):
    """
    获取所有摊位股价的详细计算过程，用于公示透明化。
    
    返回内容：
    - pool_info: 资金池信息（总投入、手续费、净池）
    - weights: 6维度权重配置
    - totals: 全场各维度总和（用于归一化）
    - total_score: 全场综合分总和
    - booths: 每个摊位的详细计算过程
        - raw: 6维度原始数据
        - normalized: 归一化值（占全场比例）
        - weighted: 加权后的6维度得分
        - score: 综合分
        - ratio: 分红占比
        - booth_pool: 摊位分到的资金池
        - shares: 总持股数
        - current_price: 最终股价
        - rank: 综合分排名
    """
    try:
        service = StockAccountService(db)
        breakdown = service.get_price_breakdown(event_id)
        return breakdown
    except Exception as e:
        logger.error(f"获取股价计算明细失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "查询失败"}
        )


# ============ K-Line Data ============

@router.get(
    "/kline/{event_id}",
    summary="获取所有摊位的K线数据（大屏用）"
)
async def get_kline_data(
    event_id: int,
    interval: int = Query(5, description="K线时间间隔（分钟）"),
    db: Session = Depends(get_db)
):
    """
    获取活动下所有摊位的K线数据（基于Pari-mutuel模型）。
    
    在每个时间窗口结束时快照：
    - 累计订单（决定每摊位股数）
    - 累计交易（决定每摊位经营数据）
    - 应用 Pari-mutuel 公式计算当时的股价
    
    返回每个摊位的完整K线序列。
    """
    from models.stock_account import StockOrder
    from models.booth import Booth
    from models.transaction import Transaction
    from datetime import datetime, timedelta
    from core.timezone import CST
    from services.stock_account_service import (
        INITIAL_STOCK_PRICE, OFFICIAL_FEE_RATE, SCORE_WEIGHTS
    )
    
    try:
        # 获取活动下所有摊位
        booths = db.query(Booth).filter(Booth.event_id == event_id).all()
        if not booths:
            booths = db.query(Booth).filter(Booth.status == 'active').all()
        if not booths:
            return []
        
        booth_ids = [b.id for b in booths]
        base_price = float(INITIAL_STOCK_PRICE)
        fee_rate = float(OFFICIAL_FEE_RATE)
        
        # 一次性加载所有订单（按时间排序）
        orders = db.query(StockOrder).filter(
            StockOrder.event_id == event_id,
            StockOrder.status.in_(['holding', 'sold', 'settled'])
        ).order_by(StockOrder.created_at.asc()).all()
        
        # 一次性加载所有交易（按时间排序）
        transactions = db.query(Transaction).filter(
            Transaction.event_id == event_id,
            Transaction.booth_id.in_(booth_ids),
            Transaction.type.in_(['payment', 'cash_payment', 'recharge']),
            Transaction.amount > 0
        ).order_by(Transaction.created_at.asc()).all()
        
        # 加载成本数据（不随时间变化，一次加载）
        try:
            from models.cost_evidence import CostEvidence
            cost_rows = db.query(
                CostEvidence.booth_id,
                func.sum(CostEvidence.amount)
            ).filter(
                CostEvidence.booth_id.in_(booth_ids),
                CostEvidence.status == 'approved'
            ).group_by(CostEvidence.booth_id).all()
            cost_map = {r[0]: float(r[1]) for r in cost_rows if r[1]}
        except Exception:
            cost_map = {}
        
        if not orders and not transactions:
            now = datetime.now(CST)
            return [{
                "booth_id": b.id,
                "booth_name": b.name,
                "class_name": b.class_name or "",
                "kline": [{
                    "time": now.strftime("%H:%M"),
                    "open": base_price,
                    "close": base_price,
                    "high": base_price,
                    "low": base_price,
                    "volume": 0,
                }]
            } for b in booths]
        
        # 确定时间范围
        all_times = [o.created_at for o in orders] + [t.created_at for t in transactions]
        first_time = min(all_times)
        last_time = max(all_times)
        # 确保时间范围带时区信息
        if first_time.tzinfo is None:
            first_time = first_time.replace(tzinfo=CST)
        if last_time.tzinfo is None:
            last_time = last_time.replace(tzinfo=CST)
        
        # 对齐到时间窗口边界
        first_time = first_time.replace(second=0, microsecond=0)
        first_time = first_time - timedelta(minutes=first_time.minute % interval)
        
        interval_delta = timedelta(minutes=interval)
        
        # 计算窗口边界
        windows = []
        current = first_time
        end_time = last_time + interval_delta
        while current <= end_time:
            windows.append(current)
            current += interval_delta
        
        # 为每个时间窗口计算 Pari-mutuel 股价
        # 用累积索引避免重复扫描
        order_idx = 0
        txn_idx = 0
        
        # 累积状态
        cum_shares: Dict[int, int] = {bid: 0 for bid in booth_ids}
        cum_invest: Dict[int, float] = {bid: 0.0 for bid in booth_ids}
        cum_revenue: Dict[int, float] = {bid: 0.0 for bid in booth_ids}
        cum_traffic: Dict[int, int] = {bid: 0 for bid in booth_ids}
        # 增长率：上一窗口的收入快照
        prev_revenue: Dict[int, float] = {bid: 0.0 for bid in booth_ids}
        
        # 每个摊位的K线序列
        booth_klines: Dict[int, list] = {bid: [] for bid in booth_ids}
        prev_prices: Dict[int, float] = {bid: base_price for bid in booth_ids}
        window_volumes: Dict[int, int] = {bid: 0 for bid in booth_ids}
        
        def compute_prices_now(growth_factor: Dict[int, float]) -> Dict[int, float]:
            """根据当前累积状态计算各摊位股价"""
            total_shares = sum(cum_shares.values())
            if total_shares == 0:
                return {bid: base_price for bid in booth_ids}
            
            total_investment = sum(cum_invest.values())
            pool = total_investment * (1 - fee_rate)
            
            # 计算各维度总和（归一化用）
            totals_rev = sum(cum_revenue.values()) or 1
            totals_traf = sum(cum_traffic.values()) or 1
            totals_profit = sum(
                (cum_revenue[b] - cost_map.get(b, cum_revenue[b] * 0.3))
                for b in booth_ids
            ) or 1
            totals_avg = sum(
                (cum_revenue[b] / cum_traffic[b]) if cum_traffic[b] > 0 else 0
                for b in booth_ids
            ) or 1
            totals_growth = sum(growth_factor.values()) or 1
            
            # 简化：使用 4 个维度（投资人数维度暂略）
            scores = {}
            total_score = 0.0
            for bid in booth_ids:
                rev = cum_revenue[bid]
                profit = max(0, rev - cost_map.get(bid, rev * 0.3))
                avg_ticket = (rev / cum_traffic[bid]) if cum_traffic[bid] > 0 else 0
                growth = growth_factor.get(bid, 0)
                
                norm_r = rev / totals_rev if totals_rev > 0 else 0
                norm_p = profit / totals_profit if totals_profit > 0 else 0
                norm_t = cum_traffic[bid] / totals_traf if totals_traf > 0 else 0
                norm_a = avg_ticket / totals_avg if totals_avg > 0 else 0
                norm_g = growth / totals_growth if totals_growth > 0 else 0
                
                # 简化权重（K线展示用）：4维度
                score = 0.25 * norm_r + 0.30 * norm_p + 0.20 * norm_t + 0.15 * norm_a + 0.10 * norm_g
                score = max(score, 0.001)
                scores[bid] = score
                total_score += score
            
            if total_score == 0:
                total_score = 1.0
            
            prices = {}
            for bid in booth_ids:
                shares = cum_shares[bid]
                if shares > 0:
                    booth_pool = pool * scores[bid] / total_score
                    prices[bid] = max(0.5, round(booth_pool / shares, 2))
                else:
                    prices[bid] = base_price
            return prices
        
        for window_idx, window_start in enumerate(windows):
            window_end = window_start + interval_delta
            
            # 重置每窗口成交量
            window_volumes = {bid: 0 for bid in booth_ids}
            
            # 推进订单游标到本窗口末尾
            while order_idx < len(orders):
                o_time = orders[order_idx].created_at
                if o_time.tzinfo is None:
                    o_time = o_time.replace(tzinfo=CST)
                if o_time >= window_end:
                    break
                if orders[order_idx].booth_id in cum_shares:
                    bid = orders[order_idx].booth_id
                    cum_shares[bid] += orders[order_idx].shares
                    cum_invest[bid] += float(orders[order_idx].total_amount)
                    window_volumes[bid] += orders[order_idx].shares
                order_idx += 1
            
            # 推进交易游标到本窗口末尾
            while txn_idx < len(transactions):
                t_time = transactions[txn_idx].created_at
                if t_time.tzinfo is None:
                    t_time = t_time.replace(tzinfo=CST)
                if t_time >= window_end:
                    break
                if transactions[txn_idx].booth_id in cum_revenue:
                    bid = transactions[txn_idx].booth_id
                    cum_revenue[bid] += float(transactions[txn_idx].amount)
                    cum_traffic[bid] += 1
                txn_idx += 1
            
            # 计算增长率：本窗口收入 / 历史累积收入
            growth_factor = {}
            for bid in booth_ids:
                delta_rev = cum_revenue[bid] - prev_revenue[bid]
                older_rev = prev_revenue[bid]
                if older_rev > 0:
                    growth_factor[bid] = delta_rev / older_rev
                elif delta_rev > 0:
                    growth_factor[bid] = 1.0
                else:
                    growth_factor[bid] = 0.0
            
            # 计算本窗口结束时的股价
            current_prices = compute_prices_now(growth_factor)
            
            # 写入K线
            time_str = window_start.strftime("%H:%M")
            for bid in booth_ids:
                open_p = prev_prices[bid]
                close_p = current_prices[bid]
                # 高低价：在窗口有交易时，假设波动幅度，否则等于开收盘
                if window_volumes[bid] > 0:
                    high_p = max(open_p, close_p) * 1.01
                    low_p = min(open_p, close_p) * 0.99
                else:
                    high_p = max(open_p, close_p)
                    low_p = min(open_p, close_p)
                
                booth_klines[bid].append({
                    "time": time_str,
                    "open": round(open_p, 2),
                    "close": round(close_p, 2),
                    "high": round(high_p, 2),
                    "low": round(low_p, 2),
                    "volume": window_volumes[bid],
                })
                prev_prices[bid] = close_p
            
            # 更新增长率基线
            prev_revenue = dict(cum_revenue)
        
        # 构建结果
        result = []
        for booth in booths:
            kline = booth_klines[booth.id]
            if not kline:
                kline = [{
                    "time": datetime.now(CST).strftime("%H:%M"),
                    "open": base_price,
                    "close": base_price,
                    "high": base_price,
                    "low": base_price,
                    "volume": 0,
                }]
            result.append({
                "booth_id": booth.id,
                "booth_name": booth.name,
                "class_name": booth.class_name or "",
                "kline": kline,
            })
        
        # 按最新收盘价降序
        result.sort(key=lambda x: x['kline'][-1]['close'] if x['kline'] else 0, reverse=True)
        return result
    
    except Exception as e:
        logger.error(f"获取K线数据失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "获取K线数据失败"}
        )
