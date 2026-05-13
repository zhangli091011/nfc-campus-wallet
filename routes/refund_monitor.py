"""
退款监控与审计报表 API

提供退款统计、异常预警、退款明细等数据接口。
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, text, and_
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import logging

from core.database import get_db
from core.security import get_current_user, RoleChecker
from models.transaction import Transaction
from models.booth import Booth
from models.participant import Participant
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["refund-monitor"])


# ============================================================================
# Response Models
# ============================================================================

class RefundSummary(BaseModel):
    """退款总览"""
    total_refund_count: int
    total_refund_amount: float
    total_refund_amount_yuan: float
    total_pay_count: int
    total_pay_amount: float
    total_pay_amount_yuan: float
    overall_refund_rate: float  # 退款率 = 退款笔数 / 支付笔数


class BoothRefundRank(BaseModel):
    """摊位退款率排名"""
    booth_id: int
    booth_name: str
    class_name: str
    refund_count: int
    pay_count: int
    refund_amount: float
    refund_amount_yuan: float
    refund_rate: float  # 退款率


class RefundAlert(BaseModel):
    """退款异常预警"""
    booth_id: int
    booth_name: str
    class_name: str
    refund_count_in_window: int
    window_minutes: int
    alert_level: str  # warning / critical
    latest_refund_time: str


class RefundReasonStat(BaseModel):
    """退款原因分布"""
    reason: str
    count: int
    amount: float
    amount_yuan: float
    percentage: float


class RefundDetail(BaseModel):
    """退款明细"""
    id: int
    original_transaction_id: Optional[int]
    amount: float
    amount_yuan: float
    booth_id: Optional[int]
    booth_name: Optional[str]
    participant_id: Optional[int]
    participant_name: Optional[str]
    card_uid: Optional[str]
    reason: str
    operator_name: Optional[str]
    created_at: str


class RefundMonitorResponse(BaseModel):
    """退款监控完整响应"""
    summary: RefundSummary
    top_refund_booths: List[BoothRefundRank]
    alerts: List[RefundAlert]
    reason_distribution: List[RefundReasonStat]


class RefundDetailResponse(BaseModel):
    """退款明细列表响应"""
    refunds: List[RefundDetail]
    total_count: int


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/refund-monitor/stats", response_model=RefundMonitorResponse)
async def get_refund_monitor_stats(
    event_id: Optional[int] = Query(None, description="活动ID（可选，默认使用当前激活活动）"),
    alert_window_minutes: int = Query(5, ge=1, le=60, description="异常预警时间窗口（分钟）"),
    alert_threshold: int = Query(3, ge=1, le=20, description="预警阈值（窗口内退款笔数）"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    获取退款监控统计数据。

    包含：
    - 退款总览（总额、退款率）
    - 退款率最高的 Top 3 摊位
    - 异常预警（时间窗口内高频退款摊位）
    - 退款原因分布
    """
    try:
        # 如果未指定 event_id，使用当前激活活动
        if event_id is None:
            from services.event_service import EventService
            event_service = EventService(db)
            active_event = event_service.get_active_event()
            if active_event:
                event_id = active_event.id

        # ── 1. 退款总览 ──
        refund_query = db.query(
            func.count(Transaction.id).label('count'),
            func.coalesce(func.sum(Transaction.amount), 0).label('total')
        ).filter(Transaction.type == 'refund')

        pay_query = db.query(
            func.count(Transaction.id).label('count'),
            func.coalesce(func.sum(Transaction.amount), 0).label('total')
        ).filter(Transaction.type == 'pay')

        if event_id:
            refund_query = refund_query.filter(Transaction.event_id == event_id)
            pay_query = pay_query.filter(Transaction.event_id == event_id)

        refund_stats = refund_query.first()
        pay_stats = pay_query.first()

        refund_count = refund_stats.count or 0
        refund_total = refund_stats.total or 0
        pay_count = pay_stats.count or 0
        pay_total = pay_stats.total or 0

        overall_refund_rate = (refund_count / pay_count * 100) if pay_count > 0 else 0.0

        summary = RefundSummary(
            total_refund_count=refund_count,
            total_refund_amount=refund_total,
            total_refund_amount_yuan=float(refund_total),
            total_pay_count=pay_count,
            total_pay_amount=pay_total,
            total_pay_amount_yuan=float(pay_total),
            overall_refund_rate=round(overall_refund_rate, 2)
        )

        # ── 2. 退款率最高的 Top 3 摊位 ──
        booth_refund_query = db.query(
            Transaction.booth_id,
            func.count(Transaction.id).label('refund_count'),
            func.coalesce(func.sum(Transaction.amount), 0).label('refund_amount')
        ).filter(
            Transaction.type == 'refund',
            Transaction.booth_id.isnot(None)
        )

        booth_pay_query = db.query(
            Transaction.booth_id,
            func.count(Transaction.id).label('pay_count')
        ).filter(
            Transaction.type == 'pay',
            Transaction.booth_id.isnot(None)
        )

        if event_id:
            booth_refund_query = booth_refund_query.filter(Transaction.event_id == event_id)
            booth_pay_query = booth_pay_query.filter(Transaction.event_id == event_id)

        booth_refunds = booth_refund_query.group_by(Transaction.booth_id).all()
        booth_pays = {r.booth_id: r.pay_count for r in booth_pay_query.group_by(Transaction.booth_id).all()}

        booth_ranks = []
        for br in booth_refunds:
            booth = db.query(Booth).filter(Booth.id == br.booth_id).first()
            if not booth:
                continue
            pc = booth_pays.get(br.booth_id, 0)
            rate = (br.refund_count / pc * 100) if pc > 0 else 100.0
            booth_ranks.append(BoothRefundRank(
                booth_id=br.booth_id,
                booth_name=booth.name,
                class_name=booth.class_name or '',
                refund_count=br.refund_count,
                pay_count=pc,
                refund_amount=br.refund_amount,
                refund_amount_yuan=float(br.refund_amount),
                refund_rate=round(rate, 2)
            ))

        # 按退款率降序排列，取 Top 3
        booth_ranks.sort(key=lambda x: x.refund_rate, reverse=True)
        top_refund_booths = booth_ranks[:3]

        # ── 3. 异常预警 ──
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=alert_window_minutes)

        recent_refunds_query = db.query(
            Transaction.booth_id,
            func.count(Transaction.id).label('count'),
            func.max(Transaction.created_at).label('latest')
        ).filter(
            Transaction.type == 'refund',
            Transaction.booth_id.isnot(None),
            Transaction.created_at >= window_start
        )

        if event_id:
            recent_refunds_query = recent_refunds_query.filter(Transaction.event_id == event_id)

        recent_refunds = recent_refunds_query.group_by(Transaction.booth_id).all()

        alerts = []
        for rr in recent_refunds:
            if rr.count >= alert_threshold:
                booth = db.query(Booth).filter(Booth.id == rr.booth_id).first()
                if not booth:
                    continue
                alert_level = 'critical' if rr.count >= alert_threshold * 2 else 'warning'
                alerts.append(RefundAlert(
                    booth_id=rr.booth_id,
                    booth_name=booth.name,
                    class_name=booth.class_name or '',
                    refund_count_in_window=rr.count,
                    window_minutes=alert_window_minutes,
                    alert_level=alert_level,
                    latest_refund_time=rr.latest.isoformat() if rr.latest else ''
                ))

        # 按严重程度和数量排序
        alerts.sort(key=lambda x: (-1 if x.alert_level == 'critical' else 0, -x.refund_count_in_window))

        # ── 4. 退款原因分布 ──
        reason_query = db.query(
            Transaction.remark,
            func.count(Transaction.id).label('count'),
            func.coalesce(func.sum(Transaction.amount), 0).label('amount')
        ).filter(
            Transaction.type == 'refund'
        )

        if event_id:
            reason_query = reason_query.filter(Transaction.event_id == event_id)

        reason_results = reason_query.group_by(Transaction.remark).all()

        # 解析退款原因（remark 格式为 "退款原因: xxx"）
        reason_map = {}
        for rr in reason_results:
            raw_reason = rr.remark or '未知原因'
            # 提取原因文本
            if '退款原因:' in raw_reason:
                reason_text = raw_reason.split('退款原因:')[1].strip()
            elif '退款原因：' in raw_reason:
                reason_text = raw_reason.split('退款原因：')[1].strip()
            else:
                reason_text = raw_reason

            # 归类原因
            category = _categorize_reason(reason_text)
            if category not in reason_map:
                reason_map[category] = {'count': 0, 'amount': 0}
            reason_map[category]['count'] += rr.count
            reason_map[category]['amount'] += rr.amount

        total_reason_count = sum(v['count'] for v in reason_map.values())
        reason_distribution = []
        for reason, data in reason_map.items():
            pct = (data['count'] / total_reason_count * 100) if total_reason_count > 0 else 0
            reason_distribution.append(RefundReasonStat(
                reason=reason,
                count=data['count'],
                amount=data['amount'],
                amount_yuan=float(data['amount']),
                percentage=round(pct, 1)
            ))

        reason_distribution.sort(key=lambda x: x.count, reverse=True)

        return RefundMonitorResponse(
            summary=summary,
            top_refund_booths=top_refund_booths,
            alerts=alerts,
            reason_distribution=reason_distribution
        )

    except Exception as e:
        logger.error(f"获取退款监控数据失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": f"获取退款监控数据失败: {str(e)}"}
        )


@router.get("/refund-monitor/details", response_model=RefundDetailResponse)
async def get_refund_details(
    event_id: Optional[int] = Query(None, description="活动ID"),
    booth_id: Optional[int] = Query(None, description="摊位ID过滤"),
    reason_keyword: Optional[str] = Query(None, description="退款原因关键词过滤"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    获取退款明细列表，支持按原因、摊位、日期过滤。
    """
    try:
        # 如果未指定 event_id，使用当前激活活动
        if event_id is None:
            from services.event_service import EventService
            event_service = EventService(db)
            active_event = event_service.get_active_event()
            if active_event:
                event_id = active_event.id

        query = db.query(Transaction).filter(Transaction.type == 'refund')

        if event_id:
            query = query.filter(Transaction.event_id == event_id)
        if booth_id:
            query = query.filter(Transaction.booth_id == booth_id)
        if reason_keyword:
            query = query.filter(Transaction.remark.contains(reason_keyword))
        if start_date:
            query = query.filter(Transaction.created_at >= start_date)
        if end_date:
            query = query.filter(Transaction.created_at <= end_date + ' 23:59:59')

        total_count = query.count()
        refunds = query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()

        details = []
        for txn in refunds:
            # 获取摊位名称
            booth_name = None
            if txn.booth_id:
                booth = db.query(Booth).filter(Booth.id == txn.booth_id).first()
                if booth:
                    booth_name = booth.name

            # 获取参与者名称（未实名用户显示卡号）
            participant_name = None
            if txn.participant_id:
                participant = db.query(Participant).filter(Participant.id == txn.participant_id).first()
                if participant:
                    participant_name = participant.display_name

            # 获取操作员名称
            operator_name = None
            if txn.booth_operator_id:
                operator = db.query(User).filter(User.id == txn.booth_operator_id).first()
                if operator:
                    operator_name = operator.username
            elif txn.operator_id:
                try:
                    op_id = int(txn.operator_id)
                    operator = db.query(User).filter(User.id == op_id).first()
                    if operator:
                        operator_name = operator.username
                except (ValueError, TypeError):
                    operator_name = txn.operator_id

            # 解析原因
            raw_reason = txn.remark or '未知原因'
            if '退款原因:' in raw_reason:
                reason = raw_reason.split('退款原因:')[1].strip()
            elif '退款原因：' in raw_reason:
                reason = raw_reason.split('退款原因：')[1].strip()
            else:
                reason = raw_reason

            details.append(RefundDetail(
                id=txn.id,
                original_transaction_id=txn.related_txn_id,
                amount=txn.amount,
                amount_yuan=float(txn.amount),
                booth_id=txn.booth_id,
                booth_name=booth_name,
                participant_id=txn.participant_id,
                participant_name=participant_name,
                card_uid=txn.card_uid,
                reason=reason,
                operator_name=operator_name,
                created_at=txn.created_at.isoformat() if txn.created_at else ''
            ))

        return RefundDetailResponse(
            refunds=details,
            total_count=total_count
        )

    except Exception as e:
        logger.error(f"获取退款明细失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": f"获取退款明细失败: {str(e)}"}
        )


# ============================================================================
# Helper Functions
# ============================================================================

def _categorize_reason(reason_text: str) -> str:
    """将退款原因归类到预定义类别"""
    reason_lower = reason_text.lower()

    # 操作失误类
    if any(kw in reason_lower for kw in ['操作失误', '误操作', '输错', '打错', '多收', '重复', '误扣']):
        return '操作失误'

    # 商品质量类
    if any(kw in reason_lower for kw in ['质量', '变质', '过期', '坏了', '不新鲜', '有问题']):
        return '商品质量'

    # 服务不周类
    if any(kw in reason_lower for kw in ['服务', '态度', '等太久', '慢', '不满意']):
        return '服务不周'

    # 缺货/无法提供
    if any(kw in reason_lower for kw in ['缺货', '没有了', '卖完', '无法提供', '断货']):
        return '缺货/无法提供'

    # 价格争议
    if any(kw in reason_lower for kw in ['价格', '太贵', '标价', '不对']):
        return '价格争议'

    # 其他
    return '其他'
