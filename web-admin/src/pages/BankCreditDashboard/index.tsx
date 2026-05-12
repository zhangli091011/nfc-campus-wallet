/**
 * 央行宏观经济与信用风险看板
 * 
 * 数据风控中心风格 - 深色背景 + 红黄绿三色水位警示
 * 核心功能：
 *   - 社会总负债 (M2) 监控
 *   - 官方无风险收益统计
 *   - 信用渗透率
 *   - 班级负债分布环形图
 *   - 放贷趋势折线图
 *   - 大额债务人预警名单
 *   - 一键导出对账单
 */

import React, { useEffect, useState, useRef, useCallback } from 'react'
import * as echarts from 'echarts'
import { Table, Button, Tag, Tooltip, message, Select } from 'antd'
import {
  BankOutlined,
  WarningOutlined,
  DownloadOutlined,
  ReloadOutlined,
  AlertOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import {
  getCreditDashboard,
  exportLoansCSV,
  type CreditDashboardStats,
  type TopDebtor,
} from '@/services/bankCredit'
import { getEvents, type Event } from '@/services/event'
import './index.css'

const BankCreditDashboard: React.FC = () => {
  const [stats, setStats] = useState<CreditDashboardStats | null>(null)
  const [currentTime, setCurrentTime] = useState(new Date())
  const [loading, setLoading] = useState(true)
  const [events, setEvents] = useState<Event[]>([])
  const [eventId, setEventId] = useState<number | null>(null)

  const pieChartRef = useRef<HTMLDivElement>(null)
  const lineChartRef = useRef<HTMLDivElement>(null)
  const pieInstance = useRef<echarts.ECharts | null>(null)
  const lineInstance = useRef<echarts.ECharts | null>(null)

  // 加载活动列表
  useEffect(() => {
    const loadEvents = async () => {
      try {
        const data = await getEvents()
        const eventList = data?.events || []
        setEvents(eventList)
        if (eventList.length > 0) {
          setEventId(eventList[0].id)
        }
      } catch {
        setEvents([])
      }
    }
    loadEvents()
  }, [])

  // 时钟
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  // 数据加载
  const loadData = useCallback(async () => {
    if (!eventId) return
    try {
      const data = await getCreditDashboard(eventId)
      setStats(data)
      setLoading(false)
    } catch (error) {
      console.error('加载风控数据失败:', error)
      setLoading(false)
    }
  }, [eventId])

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 10000) // 每10秒刷新
    return () => clearInterval(interval)
  }, [loadData])

  // 环形图
  useEffect(() => {
    if (!pieChartRef.current || !stats) return

    if (!pieInstance.current) {
      pieInstance.current = echarts.init(pieChartRef.current)
    }

    const data = stats.class_distribution.map((item) => ({
      name: item.class_name,
      value: item.total_amount_yuan,
    }))

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(20, 20, 40, 0.95)',
        borderColor: 'rgba(255, 100, 100, 0.3)',
        textStyle: { color: '#e0e0e0' },
        formatter: '{b}: ¥{c} ({d}%)',
      },
      legend: {
        orient: 'vertical',
        right: '5%',
        top: 'center',
        textStyle: { color: '#a0a0a0', fontSize: 12 },
        itemWidth: 12,
        itemHeight: 12,
      },
      series: [
        {
          type: 'pie',
          radius: ['45%', '72%'],
          center: ['40%', '50%'],
          avoidLabelOverlap: true,
          itemStyle: {
            borderRadius: 6,
            borderColor: '#1a1a2e',
            borderWidth: 2,
          },
          label: {
            show: true,
            color: '#c0c0c0',
            fontSize: 11,
            formatter: '{b}\n¥{c}',
          },
          labelLine: {
            lineStyle: { color: '#555' },
          },
          emphasis: {
            label: { show: true, fontSize: 14, fontWeight: 'bold' },
            itemStyle: {
              shadowBlur: 20,
              shadowColor: 'rgba(255, 100, 100, 0.5)',
            },
          },
          data: data,
          color: [
            '#e74c3c', '#f39c12', '#2ecc71', '#3498db',
            '#9b59b6', '#1abc9c', '#e67e22', '#34495e',
          ],
        },
      ],
    }

    pieInstance.current.setOption(option, true)

    return () => {
      // Don't dispose here, let the cleanup effect handle it
    }
  }, [stats])

  // 折线图
  useEffect(() => {
    if (!lineChartRef.current || !stats) return

    if (!lineInstance.current) {
      lineInstance.current = echarts.init(lineChartRef.current)
    }

    const times = stats.lending_trend.map((item) => item.time)
    const amounts = stats.lending_trend.map((item) => item.amount_yuan)
    const counts = stats.lending_trend.map((item) => item.count)

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(20, 20, 40, 0.95)',
        borderColor: 'rgba(255, 100, 100, 0.3)',
        textStyle: { color: '#e0e0e0' },
        axisPointer: {
          type: 'cross',
          crossStyle: { color: '#666' },
        },
      },
      legend: {
        data: ['放贷金额(元)', '放贷笔数'],
        textStyle: { color: '#a0a0a0' },
        top: 0,
      },
      grid: {
        left: '8%',
        right: '8%',
        bottom: '12%',
        top: '15%',
      },
      xAxis: {
        type: 'category',
        data: times,
        axisLine: { lineStyle: { color: '#333' } },
        axisLabel: { color: '#888', fontSize: 11 },
      },
      yAxis: [
        {
          type: 'value',
          name: '金额(元)',
          nameTextStyle: { color: '#888' },
          axisLine: { lineStyle: { color: '#333' } },
          axisLabel: { color: '#888' },
          splitLine: { lineStyle: { color: '#222', type: 'dashed' } },
        },
        {
          type: 'value',
          name: '笔数',
          nameTextStyle: { color: '#888' },
          axisLine: { lineStyle: { color: '#333' } },
          axisLabel: { color: '#888' },
          splitLine: { show: false },
        },
      ],
      series: [
        {
          name: '放贷金额(元)',
          type: 'line',
          yAxisIndex: 0,
          data: amounts,
          smooth: true,
          lineStyle: { color: '#e74c3c', width: 3 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(231, 76, 60, 0.4)' },
              { offset: 1, color: 'rgba(231, 76, 60, 0.02)' },
            ]),
          },
          itemStyle: { color: '#e74c3c' },
          symbol: 'circle',
          symbolSize: 6,
        },
        {
          name: '放贷笔数',
          type: 'bar',
          yAxisIndex: 1,
          data: counts,
          barWidth: '40%',
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(243, 156, 18, 0.8)' },
              { offset: 1, color: 'rgba(243, 156, 18, 0.2)' },
            ]),
            borderRadius: [4, 4, 0, 0],
          },
        },
      ],
    }

    lineInstance.current.setOption(option, true)
  }, [stats])

  // 窗口 resize
  useEffect(() => {
    const handleResize = () => {
      pieInstance.current?.resize()
      lineInstance.current?.resize()
    }
    window.addEventListener('resize', handleResize)
    return () => {
      window.removeEventListener('resize', handleResize)
      pieInstance.current?.dispose()
      lineInstance.current?.dispose()
    }
  }, [])

  // 导出
  const handleExport = () => {
    if (!eventId) return
    exportLoansCSV(eventId)
    message.success('正在导出对账单...')
  }

  // 判断风险等级
  const getRiskLevel = (utilization: number) => {
    if (utilization >= 90) return 'critical'
    if (utilization >= 70) return 'warning'
    return 'safe'
  }

  const riskLevel = stats ? getRiskLevel(stats.credit_utilization) : 'safe'

  // 表格列定义
  const columns: ColumnsType<TopDebtor> = [
    {
      title: '预警',
      key: 'alert',
      width: 60,
      align: 'center',
      render: (_, record) => {
        const amount = record.total_principal_yuan
        if (amount >= 300) return <AlertOutlined style={{ color: '#e74c3c', fontSize: 18 }} />
        if (amount >= 150) return <WarningOutlined style={{ color: '#f39c12', fontSize: 16 }} />
        return <span style={{ color: '#2ecc71' }}>●</span>
      },
    },
    {
      title: '班级',
      dataIndex: 'class_name',
      key: 'class_name',
      width: 120,
      render: (text) => <span className="cell-text">{text}</span>,
    },
    {
      title: '学号',
      dataIndex: 'student_id',
      key: 'student_id',
      width: 120,
      render: (text) => <span className="cell-text">{text}</span>,
    },
    {
      title: '姓名',
      dataIndex: 'participant_name',
      key: 'participant_name',
      width: 100,
      render: (text) => <span className="cell-text-highlight">{text}</span>,
    },
    {
      title: '名义借款',
      dataIndex: 'total_principal_yuan',
      key: 'total_principal_yuan',
      width: 120,
      align: 'right',
      sorter: (a, b) => a.total_principal_yuan - b.total_principal_yuan,
      render: (val: number) => (
        <span className={val >= 300 ? 'amount-critical' : val >= 150 ? 'amount-warning' : 'amount-safe'}>
          ¥{val.toFixed(2)}
        </span>
      ),
    },
    {
      title: '实际到账',
      dataIndex: 'total_disbursed_yuan',
      key: 'total_disbursed_yuan',
      width: 120,
      align: 'right',
      render: (val: number) => <span className="cell-text">¥{val.toFixed(2)}</span>,
    },
    {
      title: '放贷操作员',
      dataIndex: 'operator_name',
      key: 'operator_name',
      width: 110,
      render: (text) => <Tag color="geekblue">{text}</Tag>,
    },
    {
      title: '最近放贷时间',
      dataIndex: 'last_loan_time',
      key: 'last_loan_time',
      width: 160,
      render: (text: string) => (
        <span className="cell-text-dim">
          {text ? new Date(text).toLocaleString('zh-CN') : '-'}
        </span>
      ),
    },
    {
      title: '笔数',
      dataIndex: 'loan_count',
      key: 'loan_count',
      width: 70,
      align: 'center',
      render: (val: number) => (
        <Tag color={val >= 3 ? 'red' : 'default'}>{val}</Tag>
      ),
    },
  ]

  return (
    <div className="credit-dashboard">
      {/* ===== 顶部标题栏 ===== */}
      <header className="cd-header">
        <div className="cd-header-left">
          <BankOutlined className="cd-header-icon" />
          <h1 className="cd-title">央行宏观经济与信用风险看板</h1>
          <Select
            style={{ width: 180, marginLeft: 16 }}
            placeholder="选择活动"
            value={eventId ?? undefined}
            onChange={(val) => setEventId(val)}
            options={events.map((e) => ({ label: e.name, value: e.id }))}
          />
          <div className={`cd-risk-badge cd-risk-${riskLevel}`}>
            {riskLevel === 'critical' ? '⚠ 高风险' : riskLevel === 'warning' ? '⚡ 关注' : '✓ 正常'}
          </div>
        </div>
        <div className="cd-header-right">
          <Tooltip title="刷新数据">
            <Button
              type="text"
              icon={<ReloadOutlined />}
              onClick={loadData}
              className="cd-btn-refresh"
            />
          </Tooltip>
          <Button
            type="primary"
            danger
            icon={<DownloadOutlined />}
            onClick={handleExport}
            className="cd-btn-export"
          >
            导出全场对账单
          </Button>
          <div className="cd-clock">
            {currentTime.toLocaleTimeString('zh-CN', { hour12: false })}
          </div>
        </div>
      </header>

      {/* ===== 核心数据卡片 (顶排) ===== */}
      <section className="cd-metrics-row">
        {/* 社会总负债 M2 */}
        <div className={`cd-metric-card cd-metric-m2 ${riskLevel === 'critical' ? 'cd-blink' : ''}`}>
          <div className="cd-metric-label">
            <span className="cd-metric-dot cd-dot-red" />
            社会总负债 (M2)
          </div>
          <div className={`cd-metric-value ${riskLevel === 'critical' ? 'cd-value-critical' : ''}`}>
            ¥{stats?.total_principal_yuan.toFixed(2) || '0.00'}
          </div>
          <div className="cd-metric-sub">
            额度使用率：
            <span className={`cd-util-${riskLevel}`}>
              {stats?.credit_utilization.toFixed(1) || '0'}%
            </span>
            <span className="cd-metric-limit">
              / 上限 ¥{stats?.credit_limit_yuan.toFixed(0) || '10000'}
            </span>
          </div>
          <div className="cd-metric-bar">
            <div
              className={`cd-metric-bar-fill cd-bar-${riskLevel}`}
              style={{ width: `${Math.min(stats?.credit_utilization || 0, 100)}%` }}
            />
          </div>
        </div>

        {/* 官方无风险收益 */}
        <div className="cd-metric-card cd-metric-fee">
          <div className="cd-metric-label">
            <span className="cd-metric-dot cd-dot-green" />
            官方无风险收益
          </div>
          <div className="cd-metric-value cd-value-green">
            ¥{stats?.total_fee_yuan.toFixed(2) || '0.00'}
          </div>
          <div className="cd-metric-sub">
            手续费率 5% · 累计 {stats?.total_loans || 0} 笔
          </div>
        </div>

        {/* 信用渗透率 */}
        <div className="cd-metric-card cd-metric-penetration">
          <div className="cd-metric-label">
            <span className="cd-metric-dot cd-dot-yellow" />
            信用渗透率
          </div>
          <div className="cd-metric-value cd-value-yellow">
            {stats?.penetration_rate.toFixed(1) || '0'}%
          </div>
          <div className="cd-metric-sub">
            {stats?.total_borrowers || 0} 人借款 / {stats?.total_participants || 0} 人参与
          </div>
        </div>

        {/* 实际放出总额 */}
        <div className="cd-metric-card cd-metric-disbursed">
          <div className="cd-metric-label">
            <span className="cd-metric-dot cd-dot-blue" />
            实际放出总额
          </div>
          <div className="cd-metric-value cd-value-blue">
            ¥{stats?.total_disbursed_yuan.toFixed(2) || '0.00'}
          </div>
          <div className="cd-metric-sub">
            名义 - 手续费 = 实际到账
          </div>
        </div>
      </section>

      {/* ===== 图表区 (中排) ===== */}
      <section className="cd-charts-row">
        <div className="cd-chart-card">
          <div className="cd-chart-title">
            <span className="cd-chart-icon">◉</span>
            各班级负债分布
          </div>
          <div ref={pieChartRef} className="cd-chart-container" />
        </div>
        <div className="cd-chart-card cd-chart-wide">
          <div className="cd-chart-title">
            <span className="cd-chart-icon">📈</span>
            放贷趋势（按时间）
          </div>
          <div ref={lineChartRef} className="cd-chart-container" />
        </div>
      </section>

      {/* ===== 明细表格区 (底排) ===== */}
      <section className="cd-table-section">
        <div className="cd-table-header">
          <h2 className="cd-table-title">
            <AlertOutlined style={{ color: '#e74c3c', marginRight: 8 }} />
            全场大额债务人预警名单
          </h2>
          <div className="cd-table-legend">
            <span className="cd-legend-item"><AlertOutlined style={{ color: '#e74c3c' }} /> ≥300元</span>
            <span className="cd-legend-item"><WarningOutlined style={{ color: '#f39c12' }} /> ≥150元</span>
            <span className="cd-legend-item"><span style={{ color: '#2ecc71' }}>●</span> 正常</span>
          </div>
        </div>
        <Table
          columns={columns}
          dataSource={stats?.top_debtors || []}
          rowKey={(record) => `${record.student_id}-${record.participant_name}`}
          loading={loading}
          pagination={false}
          scroll={{ y: 400 }}
          className="cd-table"
          size="middle"
        />
      </section>
    </div>
  )
}

export default BankCreditDashboard
