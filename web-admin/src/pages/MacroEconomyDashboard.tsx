/**
 * 宏观经济与风控审计大屏 - Macro Economy & Risk Audit Dashboard
 *
 * 极简未来交易指挥中心风格，暗黑模式
 * 数据来源：
 *   - /api/bank/dashboard/{event_id}  → 央行信贷宏观数据
 *   - /api/refund-monitor/stats       → 退款率与摊位退款排名
 *   - /api/transactions               → 敏感操作流水（loan_issue, loan_fee, refund, correction）
 *   - /api/reports/summary            → 全场总流动性
 */

import React, { useEffect, useState, useRef, useCallback } from 'react';
import * as echarts from 'echarts';
import { Table } from 'antd';
import {
  AlertOutlined,
  BankOutlined,
  FundViewOutlined,
  WarningOutlined,
  AuditOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import dayjs from 'dayjs';
import './MacroEconomyDashboard.css';

// ============================================================================
// Types
// ============================================================================

interface CreditDashboardStats {
  total_principal: number;
  total_principal_yuan: number;
  total_fee: number;
  total_fee_yuan: number;
  total_disbursed: number;
  total_disbursed_yuan: number;
  total_loans: number;
  total_borrowers: number;
  total_participants: number;
  penetration_rate: number;
  credit_limit: number;
  credit_limit_yuan: number;
  credit_utilization: number;
  avg_loan_amount: number;
  avg_loan_amount_yuan: number;
  class_distribution: ClassDebt[];
  lending_trend: LendingTrend[];
  top_debtors: Debtor[];
}

interface ClassDebt {
  class_name: string;
  total_amount: number;
  total_amount_yuan: number;
  loan_count: number;
  borrower_count: number;
}

interface LendingTrend {
  time: string;
  amount: number;
  amount_yuan: number;
  count: number;
}

interface Debtor {
  class_name: string;
  participant_name: string;
  total_principal: number;
  total_principal_yuan: number;
  loan_count: number;
}

interface RefundMonitorData {
  summary: {
    total_refund_count: number;
    total_refund_amount: number;
    total_refund_amount_yuan: number;
    total_pay_count: number;
    total_pay_amount: number;
    total_pay_amount_yuan: number;
    overall_refund_rate: number;
  };
  top_refund_booths: BoothRefund[];
  alerts: RefundAlert[];
}

interface BoothRefund {
  booth_id: number;
  booth_name: string;
  class_name: string;
  refund_count: number;
  pay_count: number;
  refund_amount: number;
  refund_amount_yuan: number;
  refund_rate: number;
}

interface RefundAlert {
  booth_id: number;
  booth_name: string;
  alert_level: string;
}

interface AuditTransaction {
  id: number;
  type: string;
  amount: number;
  card_uid: string;
  booth_name?: string;
  participant_name?: string;
  operator_id?: string;
  remark?: string;
  created_at: string;
}

interface SummaryReport {
  total_issued: number;
  total_recharged: number;
  total_consumed: number;
  total_refunded: number;
}

// ============================================================================
// Component
// ============================================================================

const MacroEconomyDashboard: React.FC = () => {
  const [creditStats, setCreditStats] = useState<CreditDashboardStats | null>(null);
  const [refundData, setRefundData] = useState<RefundMonitorData | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditTransaction[]>([]);
  const [summaryReport, setSummaryReport] = useState<SummaryReport | null>(null);
  const [currentTime, setCurrentTime] = useState(new Date());

  const pieChartRef = useRef<HTMLDivElement>(null);
  const barChartRef = useRef<HTMLDivElement>(null);
  const pieInstance = useRef<echarts.ECharts | null>(null);
  const barInstance = useRef<echarts.ECharts | null>(null);
  const auditScrollRef = useRef<HTMLDivElement>(null);

  const eventId = 1; // TODO: 从配置或路由获取

  // 时钟
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // 数据加载
  const loadData = useCallback(async () => {
    const token = localStorage.getItem('nfc_wallet_token');
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const baseUrl = import.meta.env.VITE_API_URL || '';

    try {
      const [creditRes, refundRes, txnRes, summaryRes] = await Promise.allSettled([
        axios.get<CreditDashboardStats>(
          `${baseUrl}/api/bank/dashboard/${eventId}`,
          { headers }
        ),
        axios.get<RefundMonitorData>(
          `${baseUrl}/api/refund-monitor/stats`,
          { headers, params: { event_id: eventId } }
        ),
        axios.get<{ transactions: AuditTransaction[] }>(
          `${baseUrl}/api/transactions`,
          {
            headers,
            params: {
              event_id: eventId,
              type: 'loan_issue,loan_fee,refund,correction',
              limit: 50,
            },
          }
        ),
        axios.get<SummaryReport>(
          `${baseUrl}/api/reports/summary`,
          { headers, params: { event_id: eventId } }
        ),
      ]);

      if (creditRes.status === 'fulfilled') setCreditStats(creditRes.value.data);
      if (refundRes.status === 'fulfilled') setRefundData(refundRes.value.data);
      if (txnRes.status === 'fulfilled') setAuditLogs(txnRes.value.data?.transactions || []);
      if (summaryRes.status === 'fulfilled') setSummaryReport(summaryRes.value.data);
    } catch (err) {
      console.error('Dashboard data load error:', err);
    }
  }, [eventId]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 8000);
    return () => clearInterval(interval);
  }, [loadData]);

  // 图表初始化与更新
  useEffect(() => {
    if (pieChartRef.current) {
      if (!pieInstance.current) {
        pieInstance.current = echarts.init(pieChartRef.current);
      }
      updatePieChart();
    }
    return () => { pieInstance.current?.dispose(); pieInstance.current = null; };
  }, [creditStats]);

  useEffect(() => {
    if (barChartRef.current) {
      if (!barInstance.current) {
        barInstance.current = echarts.init(barChartRef.current);
      }
      updateBarChart();
    }
    return () => { barInstance.current?.dispose(); barInstance.current = null; };
  }, [refundData]);

  // 自动滚动审计表
  useEffect(() => {
    const el = auditScrollRef.current;
    if (!el) return;
    const scrollInterval = setInterval(() => {
      if (el.scrollTop + el.clientHeight >= el.scrollHeight - 10) {
        el.scrollTop = 0;
      } else {
        el.scrollTop += 1;
      }
    }, 80);
    return () => clearInterval(scrollInterval);
  }, [auditLogs]);

  // ── 环形图：各班级负债分布 ──
  const updatePieChart = () => {
    if (!pieInstance.current || !creditStats) return;

    const data = creditStats.class_distribution.map((item) => ({
      name: item.class_name,
      value: item.total_amount_yuan,
    }));

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        borderColor: 'rgba(0, 212, 255, 0.3)',
        textStyle: { color: '#E0E7FF', fontSize: 13 },
        formatter: (params: any) =>
          `<b>${params.name}</b><br/>负债: ¥${params.value.toFixed(2)}<br/>占比: ${params.percent}%`,
      },
      legend: {
        orient: 'vertical',
        right: 20,
        top: 'center',
        textStyle: { color: '#8B9DC3', fontSize: 12 },
        itemWidth: 12,
        itemHeight: 12,
        itemGap: 12,
      },
      series: [
        {
          type: 'pie',
          radius: ['45%', '72%'],
          center: ['38%', '50%'],
          avoidLabelOverlap: true,
          itemStyle: {
            borderRadius: 6,
            borderColor: '#111827',
            borderWidth: 2,
          },
          label: {
            show: false,
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold',
              color: '#E0E7FF',
            },
            itemStyle: {
              shadowBlur: 20,
              shadowColor: 'rgba(0, 212, 255, 0.5)',
            },
          },
          data: data,
          color: ['#7C3AED', '#00D4FF', '#FF3B5C', '#00FF88', '#FF8C00', '#F472B6', '#34D399', '#FBBF24'],
        },
      ],
    };

    pieInstance.current.setOption(option, true);
  };

  // ── 柱状图：各摊位退款率预警 ──
  const updateBarChart = () => {
    if (!barInstance.current || !refundData) return;

    const booths = refundData.top_refund_booths || [];
    const names = booths.map((b) => b.booth_name);
    const rates = booths.map((b) => b.refund_rate);

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        borderColor: 'rgba(0, 212, 255, 0.3)',
        textStyle: { color: '#E0E7FF', fontSize: 13 },
        formatter: (params: any) => {
          const p = params[0];
          return `<b>${p.name}</b><br/>退款率: ${p.value.toFixed(1)}%`;
        },
      },
      grid: {
        left: '8%',
        right: '5%',
        top: '12%',
        bottom: '15%',
      },
      xAxis: {
        type: 'category',
        data: names,
        axisLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.2)' } },
        axisLabel: {
          color: '#8B9DC3',
          fontSize: 11,
          rotate: names.length > 6 ? 30 : 0,
          interval: 0,
        },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        name: '退款率 %',
        nameTextStyle: { color: '#6B7280', fontSize: 11 },
        axisLine: { show: false },
        axisLabel: { color: '#6B7280', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.06)', type: 'dashed' } },
      },
      series: [
        {
          type: 'bar',
          data: rates.map((rate) => ({
            value: rate,
            itemStyle: {
              color: rate > 10
                ? new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#FF3B5C' },
                    { offset: 1, color: 'rgba(255, 59, 92, 0.3)' },
                  ])
                : new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#00D4FF' },
                    { offset: 1, color: 'rgba(0, 212, 255, 0.3)' },
                  ]),
              borderRadius: [4, 4, 0, 0],
            },
          })),
          barWidth: '50%',
          markLine: {
            silent: true,
            symbol: 'none',
            lineStyle: { color: '#FF3B5C', type: 'dashed', width: 1.5 },
            data: [{ yAxis: 10, label: { formatter: '预警线 10%', color: '#FF3B5C', fontSize: 11 } }],
          },
        },
      ],
    };

    barInstance.current.setOption(option, true);
  };

  // ── 计算宏观指标 ──
  const totalLiquidity = summaryReport
    ? (summaryReport.total_issued + summaryReport.total_recharged - summaryReport.total_consumed)
    : 0;

  const totalDebt = creditStats?.total_principal_yuan || 0;
  const bankProfit = creditStats?.total_fee_yuan || 0;
  const isDebtWarning = totalDebt > 100; // 超过100元（10000分）触发警告

  // ── 格式化数字 ──
  const formatMoney = (val: number) => {
    return new Intl.NumberFormat('zh-CN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(val);
  };

  // ── 操作类型映射 ──
  const typeLabel = (type: string) => {
    const map: Record<string, { label: string; cls: string }> = {
      loan_issue: { label: '放贷', cls: 'loan' },
      loan_fee: { label: '手续费', cls: 'fee' },
      refund: { label: '退款', cls: 'refund' },
      correction: { label: '冲正', cls: 'correction' },
    };
    return map[type] || { label: type, cls: '' };
  };

  // ── 审计表格列 ──
  const auditColumns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (t: string) => (
        <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}>
          {dayjs(t).format('HH:mm:ss')}
        </span>
      ),
    },
    {
      title: '操作类型',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type: string) => {
        const { label, cls } = typeLabel(type);
        return <span className={`op-tag ${cls}`}>{label}</span>;
      },
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      render: (amount: number, record: AuditTransaction) => {
        const yuan = amount;
        const isNegative = record.type === 'loan_fee' || record.type === 'refund';
        return (
          <span style={{
            color: isNegative ? '#FF3B5C' : '#00FF88',
            fontFamily: 'JetBrains Mono, monospace',
            fontWeight: 600,
          }}>
            {isNegative ? '-' : '+'}¥{formatMoney(yuan)}
          </span>
        );
      },
    },
    {
      title: '操作人',
      dataIndex: 'operator_id',
      key: 'operator_id',
      width: 100,
      render: (op: string) => <span style={{ color: '#8B9DC3' }}>{op || '-'}</span>,
    },
    {
      title: '目标对象',
      key: 'target',
      width: 160,
      render: (_: unknown, record: AuditTransaction) => (
        <span style={{ color: '#C0C8E0' }}>
          {record.card_uid || record.booth_name || '-'}
        </span>
      ),
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
      ellipsis: true,
      render: (remark: string) => (
        <span style={{ color: '#6B7280', fontSize: 12 }}>{remark || '-'}</span>
      ),
    },
  ];

  return (
    <div className="macro-dashboard">
      {/* ═══════════ 顶部标题栏 ═══════════ */}
      <div className="macro-header">
        <div className="macro-header-content">
          <div className="macro-title-section">
            <BankOutlined className="macro-title-icon" />
            <h1 className="macro-title">宏观经济与风控审计中心</h1>
          </div>
          <div className="macro-status-section">
            <div className="macro-live-badge">
              <div className="macro-live-dot" />
              <span className="macro-live-text">LIVE</span>
            </div>
            <div className="macro-clock">
              {currentTime.toLocaleTimeString('zh-CN', { hour12: false })}
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════ 顶部宏观指标卡片 ═══════════ */}
      <div className="macro-indicators">
        {/* 全场总流动性 */}
        <div className="indicator-card liquidity">
          <div className="indicator-label">全场总流动性 Total Liquidity</div>
          <div className="indicator-value blue">¥{formatMoney(totalLiquidity)}</div>
          <div className="indicator-sub">
            发放 ¥{formatMoney(summaryReport?.total_issued || 0)} · 消费 ¥{formatMoney(summaryReport?.total_consumed || 0)}
          </div>
        </div>

        {/* 社会总负债 */}
        <div className={`indicator-card debt ${isDebtWarning ? 'warning' : ''}`}>
          <div className="indicator-label">社会总负债 M2 Debt</div>
          <div className={`indicator-value ${isDebtWarning ? 'red' : 'normal-debt'}`}>
            ¥{formatMoney(totalDebt)}
          </div>
          <div className="indicator-sub">
            累计放款 {creditStats?.total_loans || 0} 笔 · 借款人 {creditStats?.total_borrowers || 0} 人
          </div>
          {isDebtWarning && (
            <div className="warning-icon">
              <WarningOutlined /> 负债超限预警
            </div>
          )}
        </div>

        {/* 央行净收益 */}
        <div className="indicator-card profit">
          <div className="indicator-label">央行净收益 Bank Profit</div>
          <div className="indicator-value green">¥{formatMoney(bankProfit)}</div>
          <div className="indicator-sub">
            手续费率 5% · 信贷利用率 {creditStats?.credit_utilization?.toFixed(1) || '0.0'}%
          </div>
        </div>
      </div>

      {/* ═══════════ 中部图表分析区 ═══════════ */}
      <div className="macro-charts">
        {/* 左侧：班级负债分布环形图 */}
        <div className="chart-panel">
          <div className="chart-panel-header">
            <FundViewOutlined className="chart-panel-icon" />
            <span className="chart-panel-title">各班级负债分布 Class Debt Distribution</span>
          </div>
          <div ref={pieChartRef} className="chart-container-macro" />
        </div>

        {/* 右侧：退款率预警柱状图 */}
        <div className="chart-panel">
          <div className="chart-panel-header">
            <AlertOutlined className="chart-panel-icon" style={{ color: '#FF3B5C' }} />
            <span className="chart-panel-title">实时退款率预警 Refund Rate Alert</span>
          </div>
          <div ref={barChartRef} className="chart-container-macro" />
        </div>
      </div>

      {/* ═══════════ 底部实时审计流水墙 ═══════════ */}
      <div className="macro-audit-wall">
        <div className="audit-panel">
          <div className="audit-panel-header">
            <div className="audit-panel-left">
              <AuditOutlined className="audit-panel-icon" />
              <span className="audit-panel-title">实时敏感操作流水 Audit Stream</span>
            </div>
            <div className="audit-count-badge">
              {auditLogs.length} 条记录
            </div>
          </div>
          <div ref={auditScrollRef} style={{ maxHeight: 360, overflow: 'auto' }}>
            <Table
              className="audit-table"
              columns={auditColumns}
              dataSource={auditLogs}
              rowKey="id"
              pagination={false}
              size="small"
              rowClassName={(record) =>
                record.type === 'refund' ? 'refund-row' : ''
              }
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default MacroEconomyDashboard;
