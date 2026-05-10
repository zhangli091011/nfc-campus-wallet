"""
Pydantic schemas for Stock Market module.

股票交易模块 - 数据验证模式
所有金额以"元"为单位。
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal


# ============ Stock Buy Schemas ============

class StockBuyRequest(BaseModel):
    """购买股票请求"""
    card_uid: str = Field(..., min_length=1, max_length=32, description="NFC卡UID")
    event_id: int = Field(..., description="活动ID")
    booth_id: int = Field(..., description="摊位ID")
    shares: int = Field(..., gt=0, description="购买股数")


class StockBuyResponse(BaseModel):
    """购买股票响应"""
    success: bool
    order_id: int
    booth_id: int
    booth_name: str
    shares: int
    buy_price: float = Field(description="购买单价（元）")
    buy_price_yuan: float = Field(description="购买单价（元）- 兼容字段")
    total_amount: float = Field(description="购买总金额（元）")
    total_amount_yuan: float = Field(description="购买总金额（元）- 兼容字段")
    new_balance: float = Field(description="账户新余额（元）")
    new_balance_yuan: float = Field(description="账户新余额（元）- 兼容字段")
    message: str


class StockOrderResponse(BaseModel):
    """股票订单响应"""
    id: int
    event_id: int
    participant_id: int
    booth_id: int
    booth_name: Optional[str] = None
    class_name: Optional[str] = None
    shares: int
    buy_price: float
    buy_price_yuan: float
    total_amount: float
    total_amount_yuan: float
    status: str
    settlement_price: Optional[float] = None
    settlement_price_yuan: Optional[float] = None
    settlement_amount: Optional[float] = None
    settlement_amount_yuan: Optional[float] = None
    profit_loss: Optional[float] = None
    profit_loss_yuan: Optional[float] = None
    created_at: datetime
    settled_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============ Stock Sell Schemas ============

class StockSellRequest(BaseModel):
    """抛售股票请求"""
    card_uid: str = Field(..., min_length=1, max_length=32, description="NFC卡UID")
    event_id: int = Field(..., description="活动ID")
    booth_id: int = Field(..., description="摊位ID")
    shares: int = Field(..., gt=0, description="抛售股数")


class StockSellResponse(BaseModel):
    """抛售股票响应"""
    success: bool
    booth_id: int
    booth_name: str
    shares_sold: int
    sell_price: float = Field(description="卖出单价（元）")
    sell_price_yuan: float = Field(description="卖出单价（元）- 兼容字段")
    total_amount: float = Field(description="卖出总金额（元）")
    total_amount_yuan: float = Field(description="卖出总金额（元）- 兼容字段")
    new_balance: float = Field(description="账户新余额（元）")
    new_balance_yuan: float = Field(description="账户新余额（元）- 兼容字段")
    message: str


# ============ Settlement Schemas ============

class StockSettlementRequest(BaseModel):
    """期末结算请求"""
    event_id: int = Field(..., description="活动ID")
    fee_rate: float = Field(default=0.05, ge=0, le=1, description="手续费率，默认5%")


class BoothStockData(BaseModel):
    """摊位股票数据"""
    booth_id: int
    booth_name: str
    class_name: str
    revenue: float  # 营业额（元）
    revenue_yuan: float
    profit: float  # 净利润（元）
    profit_yuan: float
    order_count: int
    score: Decimal
    ratio: Decimal
    sold_shares: int
    total_investment: float  # 总投资额（元）
    total_investment_yuan: float
    final_price: float  # 最终股价（元）
    final_price_yuan: float


class StockSettlementResponse(BaseModel):
    """期末结算响应"""
    success: bool
    event_id: int
    global_pool: float  # 全局奖金池（元）
    global_pool_yuan: float
    total_investment: float  # 总投资额（元）
    total_investment_yuan: float
    fee_collected: float  # 手续费（元）
    fee_collected_yuan: float
    total_score: Decimal
    booth_count: int
    booths: list[BoothStockData]
    settled_at: datetime
    message: str


# ============ Statistics Schemas ============

class StockMarketStatsResponse(BaseModel):
    """股市统计数据响应"""
    event_id: int
    total_investment: float  # 全场买股总金额（元）
    total_investment_yuan: float
    global_pool: float  # 全局奖金池（元）
    global_pool_yuan: float
    fee_collected: float  # 手续费（元）
    fee_collected_yuan: float
    total_orders: int
    total_investors: int
    total_booths: int
    is_settled: bool


class BoothStockStatsResponse(BaseModel):
    """摊位股票统计响应"""
    booth_id: int
    booth_name: str
    class_name: str
    sold_shares: int
    total_investment: float  # 总投资额（元）
    total_investment_yuan: float
    investor_count: int
    current_price: float  # 当前股价（元）
    is_settled: bool
    final_price: Optional[float] = None
    final_price_yuan: Optional[float] = None


# ============ Deprecated / Removed ============
# AccountTransferRequest, AccountTransferResponse, StockAccountResponse
# 已移除 - 不再有独立投资币账户

# Backward compatibility aliases
class AccountTransferRequest(BaseModel):
    """已废弃 - 保留以避免导入错误"""
    card_uid: str = ""
    event_id: int = 0
    transfer_type: str = ""
    amount: float = 0


class AccountTransferResponse(BaseModel):
    """已废弃 - 保留以避免导入错误"""
    success: bool = False
    message: str = "此接口已废弃，股票购买直接从主账户扣款"


class StockAccountResponse(BaseModel):
    """已废弃 - 保留以避免导入错误"""
    id: int = 0
    balance: float = 0
    balance_yuan: float = 0
