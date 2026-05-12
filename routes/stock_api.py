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
from sqlalchemy.orm import Session
from typing import List, Optional
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
from services.stock_account_service import StockAccountService
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
        shares_sold, account = service.sell_stock(
            card_uid=request.card_uid,
            event_id=request.event_id,
            booth_id=request.booth_id,
            shares=request.shares
        )
        
        from services.stock_account_service import DEFAULT_STOCK_PRICE
        sell_price = float(DEFAULT_STOCK_PRICE)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取股市统计数据（金额为元）"""
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
