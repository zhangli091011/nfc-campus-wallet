"""
Pydantic schemas for Stock Market module.

模拟股市模块 - 数据验证模式
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from decimal import Decimal


# ============ Stock Schemas ============

class StockCreate(BaseModel):
    """创建股票发行的请求模式"""
    booth_id: int = Field(..., description="摊位ID")
    event_id: int = Field(..., description="活动ID")
    total_shares: int = Field(..., gt=0, description="总发行股数")
    initial_price: int = Field(default=1000, description="初始发行价（分），默认1000分=10元")
    
    @field_validator('initial_price')
    @classmethod
    def validate_initial_price(cls, v):
        if v <= 0:
            raise ValueError("初始发行价必须大于0")
        return v


class StockUpdate(BaseModel):
    """更新股票信息的请求模式"""
    total_shares: Optional[int] = Field(None, gt=0, description="总发行股数")
    status: Optional[str] = Field(None, description="股票状态")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v and v not in ['active', 'suspended', 'settled']:
            raise ValueError("状态必须是 active, suspended 或 settled")
        return v


class StockResponse(BaseModel):
    """股票信息响应模式"""
    id: int
    booth_id: int
    event_id: int
    booth_name: Optional[str] = None
    class_name: Optional[str] = None
    initial_price: int
    initial_price_yuan: float
    total_shares: int
    sold_shares: int
    available_shares: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ Stock Purchase Schemas ============

class StockPurchaseRequest(BaseModel):
    """购买股票的请求模式（NFC刷卡）"""
    card_uid: str = Field(..., min_length=1, max_length=32, description="NFC卡UID")
    stock_id: int = Field(..., description="股票ID")
    quantity: int = Field(..., gt=0, description="购买股数")
    timestamp: int = Field(..., description="时间戳")
    signature: str = Field(..., description="签名")


class StockPurchaseResponse(BaseModel):
    """购买股票的响应模式"""
    success: bool
    purchase_id: int
    stock_id: int
    booth_name: str
    quantity: int
    purchase_price: int
    purchase_price_yuan: float
    total_amount: int
    total_amount_yuan: float
    new_balance: int
    new_balance_yuan: float
    transaction_id: int
    message: str


class StockHoldingResponse(BaseModel):
    """持仓信息响应模式"""
    id: int
    stock_id: int
    booth_name: str
    class_name: str
    quantity: int
    purchase_price: int
    purchase_price_yuan: float
    total_amount: int
    total_amount_yuan: float
    status: str
    settlement_price: Optional[int] = None
    settlement_price_yuan: Optional[float] = None
    settlement_amount: Optional[int] = None
    settlement_amount_yuan: Optional[float] = None
    profit_loss: Optional[int] = None
    profit_loss_yuan: Optional[float] = None
    created_at: datetime
    settled_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============ Settlement Schemas ============

class SettlementTriggerRequest(BaseModel):
    """触发期末结算的请求模式"""
    event_id: int = Field(..., description="活动ID")
    fee_rate: float = Field(default=0.05, ge=0, le=1, description="手续费率，默认5%")


class BoothSettlementData(BaseModel):
    """摊位结算数据"""
    booth_id: int
    booth_name: str
    class_name: str
    revenue: int
    revenue_yuan: float
    profit: int
    profit_yuan: float
    order_count: int
    score: Decimal
    ratio: Decimal
    final_price: int
    final_price_yuan: float
    sold_shares: int


class SettlementResponse(BaseModel):
    """期末结算响应模式"""
    success: bool
    event_id: int
    global_pool: int
    global_pool_yuan: float
    total_score: Decimal
    fee_rate: float
    booth_count: int
    booths: list[BoothSettlementData]
    settled_at: datetime
    message: str


class SettlementDetailResponse(BaseModel):
    """结算详情响应模式"""
    id: int
    booth_id: int
    booth_name: str
    class_name: str
    stock_id: int
    event_id: int
    revenue: int
    revenue_yuan: float
    profit: int
    profit_yuan: float
    order_count: int
    score: Decimal
    global_pool: int
    global_pool_yuan: float
    total_score: Decimal
    ratio: Decimal
    final_price: int
    final_price_yuan: float
    settled_at: datetime
    
    class Config:
        from_attributes = True


# ============ Statistics Schemas ============

class StockMarketStatsResponse(BaseModel):
    """股市统计数据响应模式"""
    event_id: int
    total_investment: int  # 全场买股总金额（分）
    total_investment_yuan: float
    global_pool: int  # 全局奖金池（分）
    global_pool_yuan: float
    fee_collected: int  # 手续费（分）
    fee_collected_yuan: float
    total_stocks: int  # 总股票数
    active_stocks: int  # 活跃股票数
    total_purchases: int  # 总购买记录数
    total_investors: int  # 总投资人数
    is_settled: bool  # 是否已结算


class BoothPerformanceResponse(BaseModel):
    """摊位经营表现响应模式"""
    booth_id: int
    booth_name: str
    class_name: str
    stock_id: Optional[int] = None
    revenue: int
    revenue_yuan: float
    profit: int
    profit_yuan: float
    order_count: int
    current_price: float  # 当前股价（元）
    sold_shares: int
    total_shares: int
    is_settled: bool
    final_price: Optional[float] = None  # 结算价（元）
