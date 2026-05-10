"""
Stock Market API Routes

模拟股市模块 - API路由
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
from services.stock_service import StockService
from schemas.stock import (
    StockCreate,
    StockUpdate,
    StockResponse,
    StockPurchaseRequest,
    StockPurchaseResponse,
    StockHoldingResponse,
    SettlementTriggerRequest,
    SettlementResponse,
    SettlementDetailResponse,
    StockMarketStatsResponse,
    BoothPerformanceResponse,
    BoothSettlementData
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ Stock Management ============

@router.post(
    "/stocks",
    response_model=StockResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建股票发行",
    description="为摊位创建股票发行（需要 event_admin 或 super_admin 权限）"
)
async def create_stock(
    request: StockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["event_admin", "super_admin"]))
):
    """创建股票发行"""
    try:
        service = StockService(db)
        stock = service.create_stock(
            booth_id=request.booth_id,
            event_id=request.event_id,
            total_shares=request.total_shares,
            initial_price=request.initial_price
        )
        
        # 构建响应
        return StockResponse(
            id=stock.id,
            booth_id=stock.booth_id,
            event_id=stock.event_id,
            booth_name=stock.booth.name,
            class_name=stock.booth.class_name,
            initial_price=stock.initial_price,
            initial_price_yuan=stock.initial_price_yuan,
            total_shares=stock.total_shares,
            sold_shares=stock.sold_shares,
            available_shares=stock.available_shares,
            status=stock.status,
            created_at=stock.created_at,
            updated_at=stock.updated_at
        )
    
    except (ValidationError, ResourceNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"创建股票失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "创建股票失败"}
        )


@router.get(
    "/stocks",
    response_model=List[StockResponse],
    summary="查询股票列表",
    description="查询股票列表（支持按活动、状态过滤）"
)
async def list_stocks(
    event_id: Optional[int] = Query(None, description="活动ID"),
    status: Optional[str] = Query(None, description="状态过滤"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查询股票列表"""
    try:
        service = StockService(db)
        stocks = service.list_stocks(
            event_id=event_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return [
            StockResponse(
                id=stock.id,
                booth_id=stock.booth_id,
                event_id=stock.event_id,
                booth_name=stock.booth.name,
                class_name=stock.booth.class_name,
                initial_price=stock.initial_price,
                initial_price_yuan=stock.initial_price_yuan,
                total_shares=stock.total_shares,
                sold_shares=stock.sold_shares,
                available_shares=stock.available_shares,
                status=stock.status,
                created_at=stock.created_at,
                updated_at=stock.updated_at
            )
            for stock in stocks
        ]
    
    except Exception as e:
        logger.error(f"查询股票列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "查询失败"}
        )


@router.get(
    "/stocks/{stock_id}",
    response_model=StockResponse,
    summary="获取股票详情",
    description="根据ID获取股票详细信息"
)
async def get_stock(
    stock_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取股票详情"""
    try:
        service = StockService(db)
        stock = service.get_stock(stock_id)
        
        return StockResponse(
            id=stock.id,
            booth_id=stock.booth_id,
            event_id=stock.event_id,
            booth_name=stock.booth.name,
            class_name=stock.booth.class_name,
            initial_price=stock.initial_price,
            initial_price_yuan=stock.initial_price_yuan,
            total_shares=stock.total_shares,
            sold_shares=stock.sold_shares,
            available_shares=stock.available_shares,
            status=stock.status,
            created_at=stock.created_at,
            updated_at=stock.updated_at
        )
    
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "STOCK_NOT_FOUND", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"获取股票详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "查询失败"}
        )


@router.patch(
    "/stocks/{stock_id}",
    response_model=StockResponse,
    summary="更新股票信息",
    description="更新股票状态或发行数量（需要 event_admin 或 super_admin 权限）"
)
async def update_stock(
    stock_id: int,
    request: StockUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["event_admin", "super_admin"]))
):
    """更新股票信息"""
    try:
        service = StockService(db)
        
        if request.status:
            stock = service.update_stock_status(stock_id, request.status)
        else:
            stock = service.get_stock(stock_id)
        
        return StockResponse(
            id=stock.id,
            booth_id=stock.booth_id,
            event_id=stock.event_id,
            booth_name=stock.booth.name,
            class_name=stock.booth.class_name,
            initial_price=stock.initial_price,
            initial_price_yuan=stock.initial_price_yuan,
            total_shares=stock.total_shares,
            sold_shares=stock.sold_shares,
            available_shares=stock.available_shares,
            status=stock.status,
            created_at=stock.created_at,
            updated_at=stock.updated_at
        )
    
    except (ValidationError, ResourceNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"更新股票失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "更新失败"}
        )


# ============ Stock Purchase ============

@router.post(
    "/stocks/purchase",
    response_model=StockPurchaseResponse,
    summary="购买股票（NFC刷卡）",
    description="参与者使用NFC卡购买股票"
)
async def purchase_stock(
    request: StockPurchaseRequest,
    db: Session = Depends(get_db)
):
    """购买股票（NFC刷卡）"""
    try:
        service = StockService(db)
        purchase, transaction = service.purchase_stock(
            card_uid=request.card_uid,
            stock_id=request.stock_id,
            quantity=request.quantity
        )
        
        return StockPurchaseResponse(
            success=True,
            purchase_id=purchase.id,
            stock_id=purchase.stock_id,
            booth_name=purchase.stock.booth.name,
            quantity=purchase.quantity,
            purchase_price=purchase.purchase_price,
            purchase_price_yuan=purchase.purchase_price_yuan,
            total_amount=purchase.total_amount,
            total_amount_yuan=purchase.total_amount_yuan,
            new_balance=transaction.balance_after,
            new_balance_yuan=transaction.balance_after_yuan,
            transaction_id=transaction.id,
            message=f"成功购买 {purchase.stock.booth.name} {purchase.quantity}股"
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


@router.get(
    "/stocks/holdings/{participant_id}",
    response_model=List[StockHoldingResponse],
    summary="查询持仓信息",
    description="查询参与者的股票持仓"
)
async def get_holdings(
    participant_id: int,
    event_id: Optional[int] = Query(None, description="活动ID过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查询持仓信息"""
    try:
        service = StockService(db)
        holdings = service.get_participant_holdings(participant_id, event_id)
        
        return [
            StockHoldingResponse(
                id=h.id,
                stock_id=h.stock_id,
                booth_name=h.stock.booth.name,
                class_name=h.stock.booth.class_name,
                quantity=h.quantity,
                purchase_price=h.purchase_price,
                purchase_price_yuan=h.purchase_price_yuan,
                total_amount=h.total_amount,
                total_amount_yuan=h.total_amount_yuan,
                status=h.status,
                settlement_price=h.settlement_price,
                settlement_price_yuan=h.settlement_price_yuan,
                settlement_amount=h.settlement_amount,
                settlement_amount_yuan=h.settlement_amount_yuan,
                profit_loss=h.profit_loss,
                profit_loss_yuan=h.profit_loss_yuan,
                created_at=h.created_at,
                settled_at=h.settled_at
            )
            for h in holdings
        ]
    
    except Exception as e:
        logger.error(f"查询持仓失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "查询失败"}
        )


# ============ Settlement ============

@router.post(
    "/stocks/settlement",
    response_model=SettlementResponse,
    summary="触发期末结算",
    description="触发活动的期末股市结算（需要 event_admin 或 super_admin 权限）"
)
async def trigger_settlement(
    request: SettlementTriggerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["event_admin", "super_admin"]))
):
    """触发期末结算"""
    try:
        service = StockService(db)
        result = service.trigger_settlement(
            event_id=request.event_id,
            fee_rate=request.fee_rate
        )
        
        # 构建响应
        booths_data = [
            BoothSettlementData(
                booth_id=b['booth_id'],
                booth_name=b['booth_name'],
                class_name=b['class_name'],
                revenue=b['revenue'],
                revenue_yuan=b['revenue'] / 1.0,
                profit=b['profit'],
                profit_yuan=b['profit'] / 1.0,
                order_count=b['order_count'],
                score=b['score'],
                ratio=b['ratio'],
                final_price=b['final_price'],
                final_price_yuan=b['final_price'] / 1.0,
                sold_shares=b['sold_shares']
            )
            for b in result['booths']
        ]
        
        return SettlementResponse(
            success=result['success'],
            event_id=result['event_id'],
            global_pool=result['global_pool'],
            global_pool_yuan=result['global_pool'] / 1.0,
            total_score=result['total_score'],
            fee_rate=result['fee_rate'],
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


@router.get(
    "/stocks/settlement/{booth_id}",
    response_model=SettlementDetailResponse,
    summary="查询摊位结算详情",
    description="查询指定摊位的结算详情"
)
async def get_settlement(
    booth_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查询摊位结算详情"""
    try:
        service = StockService(db)
        settlement = service.get_settlement(booth_id)
        
        if not settlement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error_code": "SETTLEMENT_NOT_FOUND", "message": "结算记录不存在"}
            )
        
        return SettlementDetailResponse(
            id=settlement.id,
            booth_id=settlement.booth_id,
            booth_name=settlement.booth.name,
            class_name=settlement.booth.class_name,
            stock_id=settlement.stock_id,
            event_id=settlement.event_id,
            revenue=settlement.revenue,
            revenue_yuan=settlement.revenue_yuan,
            profit=settlement.profit,
            profit_yuan=settlement.profit_yuan,
            order_count=settlement.order_count,
            score=settlement.score,
            global_pool=settlement.global_pool,
            global_pool_yuan=settlement.global_pool_yuan,
            total_score=settlement.total_score,
            ratio=settlement.ratio,
            final_price=settlement.final_price,
            final_price_yuan=settlement.final_price_yuan,
            settled_at=settlement.settled_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询结算详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "查询失败"}
        )


@router.get(
    "/stocks/settlement/event/{event_id}",
    response_model=List[SettlementDetailResponse],
    summary="查询活动所有结算记录",
    description="查询指定活动的所有摊位结算记录"
)
async def list_settlements(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查询活动所有结算记录"""
    try:
        service = StockService(db)
        settlements = service.list_settlements(event_id)
        
        return [
            SettlementDetailResponse(
                id=s.id,
                booth_id=s.booth_id,
                booth_name=s.booth.name,
                class_name=s.booth.class_name,
                stock_id=s.stock_id,
                event_id=s.event_id,
                revenue=s.revenue,
                revenue_yuan=s.revenue_yuan,
                profit=s.profit,
                profit_yuan=s.profit_yuan,
                order_count=s.order_count,
                score=s.score,
                global_pool=s.global_pool,
                global_pool_yuan=s.global_pool_yuan,
                total_score=s.total_score,
                ratio=s.ratio,
                final_price=s.final_price,
                final_price_yuan=s.final_price_yuan,
                settled_at=s.settled_at
            )
            for s in settlements
        ]
    
    except Exception as e:
        logger.error(f"查询结算记录失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "查询失败"}
        )


# ============ Statistics ============

@router.get(
    "/stocks/stats/{event_id}",
    response_model=StockMarketStatsResponse,
    summary="获取股市统计数据",
    description="获取活动的股市统计数据"
)
async def get_market_stats(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取股市统计数据"""
    try:
        service = StockService(db)
        stats = service.get_market_stats(event_id)
        
        return StockMarketStatsResponse(
            event_id=stats['event_id'],
            total_investment=stats['total_investment'],
            total_investment_yuan=stats['total_investment'] / 1.0,
            global_pool=stats['global_pool'],
            global_pool_yuan=stats['global_pool'] / 1.0,
            fee_collected=stats['fee_collected'],
            fee_collected_yuan=stats['fee_collected'] / 1.0,
            total_stocks=stats['total_stocks'],
            active_stocks=stats['active_stocks'],
            total_purchases=stats['total_purchases'],
            total_investors=stats['total_investors'],
            is_settled=stats['is_settled']
        )
    
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "查询失败"}
        )
