"""
Report schemas for NFC Campus E-Wallet System.

Provides Pydantic models for report requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# Summary Report Schemas
# ============================================================================

class SummaryReportResponse(BaseModel):
    """总览统计报表响应"""
    total_issued: float = Field(..., description="总发放额度（元）")
    total_recharged: float = Field(..., description="总充值额（元）")
    total_consumed: float = Field(..., description="总消费额（元）")
    total_refunded: float = Field(..., description="总退款额（元）")
    net_consumed: float = Field(..., description="净消费额（元）= 总消费 - 总退款")
    total_transactions: int = Field(..., description="总交易笔数")
    participant_count: int = Field(..., description="参与者数量")
    booth_count: int = Field(..., description="摊位数量")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_issued": 50000.00,
                "total_recharged": 30000.00,
                "total_consumed": 45000.00,
                "total_refunded": 2000.00,
                "net_consumed": 43000.00,
                "total_transactions": 1250,
                "participant_count": 500,
                "booth_count": 20
            }
        }


# ============================================================================
# Booth Report Schemas
# ============================================================================

class BoothReportItem(BaseModel):
    """摊位报表项"""
    booth_id: int = Field(..., description="摊位ID")
    booth_name: str = Field(..., description="摊位名称")
    class_name: str = Field(..., description="班级名称")
    revenue: float = Field(..., description="营业额（元）")
    refund_amount: float = Field(..., description="退款额（元）")
    net_revenue: float = Field(..., description="净收入（元）= 营业额 - 退款")
    sales_count: int = Field(..., description="销量（笔数）")
    total_cost: float = Field(..., description="总成本（元）")
    profit: float = Field(..., description="利润（元）= 净收入 - 成本")
    profit_margin: Optional[float] = Field(None, description="利润率（%）= 利润 / 净收入 * 100")
    
    class Config:
        json_schema_extra = {
            "example": {
                "booth_id": 1,
                "booth_name": "美食摊",
                "class_name": "高一(1)班",
                "revenue": 5000.00,
                "refund_amount": 200.00,
                "net_revenue": 4800.00,
                "sales_count": 150,
                "total_cost": 2000.00,
                "profit": 2800.00,
                "profit_margin": 58.33
            }
        }


class BoothReportResponse(BaseModel):
    """摊位报表响应"""
    booths: List[BoothReportItem] = Field(..., description="摊位报表列表")
    total_count: int = Field(..., description="摊位总数")


# ============================================================================
# Product Report Schemas
# ============================================================================

class ProductReportItem(BaseModel):
    """商品报表项"""
    product_id: int = Field(..., description="商品ID")
    product_name: str = Field(..., description="商品名称")
    booth_id: int = Field(..., description="所属摊位ID")
    booth_name: str = Field(..., description="所属摊位名称")
    sales_quantity: int = Field(..., description="销量（件数）")
    revenue: float = Field(..., description="收入（元）")
    total_cost: float = Field(..., description="总成本（元）")
    profit: float = Field(..., description="利润（元）")
    profit_margin: Optional[float] = Field(None, description="利润率（%）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": 1,
                "product_name": "奶茶",
                "booth_id": 1,
                "booth_name": "美食摊",
                "sales_quantity": 100,
                "revenue": 1000.00,
                "total_cost": 400.00,
                "profit": 600.00,
                "profit_margin": 60.00
            }
        }


class ProductReportResponse(BaseModel):
    """商品报表响应"""
    products: List[ProductReportItem] = Field(..., description="商品报表列表")
    total_count: int = Field(..., description="商品总数")


# ============================================================================
# Leaderboard Schemas
# ============================================================================

class LeaderboardItem(BaseModel):
    """排行榜项"""
    rank: int = Field(..., description="排名")
    booth_id: int = Field(..., description="摊位ID")
    booth_name: str = Field(..., description="摊位名称")
    class_name: str = Field(..., description="班级名称")
    value: float = Field(..., description="指标值")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rank": 1,
                "booth_id": 1,
                "booth_name": "美食摊",
                "class_name": "高一(1)班",
                "value": 5000.00
            }
        }


class LeaderboardResponse(BaseModel):
    """排行榜响应"""
    leaderboard: List[LeaderboardItem] = Field(..., description="排行榜列表")
    metric: str = Field(..., description="指标名称")
    total_count: int = Field(..., description="总数")


class ProductLeaderboardItem(BaseModel):
    """商品排行榜项"""
    rank: int = Field(..., description="排名")
    product_id: int = Field(..., description="商品ID")
    product_name: str = Field(..., description="商品名称")
    booth_id: int = Field(..., description="所属摊位ID")
    booth_name: str = Field(..., description="所属摊位名称")
    value: float = Field(..., description="指标值")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rank": 1,
                "product_id": 1,
                "product_name": "奶茶",
                "booth_id": 1,
                "booth_name": "美食摊",
                "value": 100
            }
        }


class ProductLeaderboardResponse(BaseModel):
    """商品排行榜响应"""
    leaderboard: List[ProductLeaderboardItem] = Field(..., description="商品排行榜列表")
    metric: str = Field(..., description="指标名称")
    total_count: int = Field(..., description="总数")


# ============================================================================
# Audit Log Schemas
# ============================================================================

class AuditLogItem(BaseModel):
    """异常审计日志项"""
    transaction_id: int = Field(..., description="交易ID")
    transaction_type: str = Field(..., description="交易类型")
    amount: float = Field(..., description="金额（元）")
    participant_name: Optional[str] = Field(None, description="参与者姓名")
    booth_name: Optional[str] = Field(None, description="摊位名称")
    operator_username: Optional[str] = Field(None, description="操作员用户名")
    remark: Optional[str] = Field(None, description="备注")
    created_at: datetime = Field(..., description="交易时间")
    flag_reason: str = Field(..., description="标记原因")
    
    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": 123,
                "transaction_type": "refund",
                "amount": 500.00,
                "participant_name": "张三",
                "booth_name": "美食摊",
                "operator_username": "cashier01",
                "remark": "商品质量问题",
                "created_at": "2024-01-15T10:30:00Z",
                "flag_reason": "大额退款"
            }
        }


class AuditLogResponse(BaseModel):
    """异常审计日志响应"""
    logs: List[AuditLogItem] = Field(..., description="异常日志列表")
    total_count: int = Field(..., description="总数")


# ============================================================================
# Export Schemas
# ============================================================================

class ExportRequest(BaseModel):
    """导出请求"""
    event_id: Optional[int] = Field(None, description="活动ID（可选，不填则导出所有）")
    report_type: str = Field(..., description="报表类型: summary/booths/products/transactions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": 1,
                "report_type": "booths"
            }
        }
