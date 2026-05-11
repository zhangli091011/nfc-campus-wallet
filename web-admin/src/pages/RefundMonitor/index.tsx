/**
 * 退款监控与审计报表
 *
 * 功能：
 * 1. 退款总览统计（总额、退款率）
 * 2. 退款率最高 Top 3 摊位
 * 3. 异常预警（5分钟内超过3笔退款自动标红闪烁）
 * 4. 退款原因分布饼图
 * 5. 退款明细表（支持按原因过滤）
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Select,
  Space,
  Alert,
  Input,
  Badge,
  Tooltip,
  Typography,
} from 'antd'
import {
  WarningOutlined,
  AlertOutlined,
  DollarOutlined,
  PercentageOutlined,
  ShopOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import * as echarts from 'echarts'
import {
  getRefundMonitorStats,
  getRefundDetails,
  type RefundMonitorResponse,
  type RefundDetail,
  type RefundAlert,
} from '@/services/refundMonitor'
import { getEvents, type Event } from '@/services/event'
import dayjs from 'dayjs'

const { Title } = Typography

const RefundMonitor = () => {
  const [stats, setStats] = useState<RefundMonitorResponse | null>(null)
  const [details, setDetails] = useState<RefundDetail[]>([])
  const [detailTotal, setDetailTotal] = useState(0)
  const [events, setEvents] = useState<Event[]>([])
  const [selectedEventId, setSelectedEventId] = useState<number>()
  const [_loading, setLoading] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [reasonFilter, setReasonFilter] = useState<string>()
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20 })
  const [alertFlash, setAlertFlash] = useState(false)

  const pieChartRef = useRef<HTMLDivElement>(null)
  const pieInstance = useRef<echarts.ECharts | null>(null)
  const refreshTimer = useRef<ReturnType<typeof setInterval> | null>(null)

  // 加载活动列表
  useEffect(() => {
    loadEvents()
  }, [])

  // 加载数据
  useEffect(() => {
    if (selectedEventId) {
      loadStats()
      loadDetails()
    }
  }, [selectedEventId])

  // 分页变化时重新加载明细
  useEffect(() => {
    if (selectedEventId) {
      loadDetails()
    }
  }, [pagination.current, reasonFilter])

  // 自动刷新（每10秒）
  useEffect(() => {
    refreshTimer.current = setInterval(() => {
      if (selectedEventId) {
        loadStats()
      }
    }, 10000)
    return () => {
      if (refreshTimer.current) clearInterval(refreshTimer.current)
    }
  }, [selectedEventId])

  // 预警闪烁动画
  useEffect(() => {
    if (stats?.alerts && stats.alerts.length > 0) {
      const flashInterval = setInterval(() => {
        setAlertFlash(prev => !prev)
      }, 800)
      return () => clearInterval(flashInterval)
    } else {
      setAlertFlash(false)
    }
  }, [stats?.alerts])

  // 饼图渲染
  useEffect(() => {
    if (pieChartRef.current && stats?.reason_distribution) {
      if (!pieInstance.current) {
        pieInstance.current = echarts.init(pieChartRef.current)
      }
      renderPieChart()
    }
    return () => {
      if (pieInstance.current) {
        pieInstance.current.dispose()
        pieInstance.current = null
      }
    }
  }, [stats?.reason_distribution])

  const loadEvents = async () => {
    try {
      const data = await getEvents()
      const eventList = data?.events || []
      setEvents(eventList)
      if (eventList.length > 0) {
        setSelectedEventId(eventList[0].id)
      }
    } catch {
      setEvents([])
    }
  }

  const loadStats = useCallback(async () => {
    if (!selectedEventId) return
    setLoading(true)
    try {
      const data = await getRefundMonitorStats({
        event_id: selectedEventId,
        alert_window_minutes: 5,
        alert_threshold: 3,
      })
      setStats(data)
    } catch {
      // handled
    } finally {
      setLoading(false)
    }
  }, [selectedEventId])

  const loadDetails = async () => {
    if (!selectedEventId) return
    setDetailLoading(true)
    try {
      const data = await getRefundDetails({
        event_id: selectedEventId,
        reason_keyword: reasonFilter || undefined,
        limit: pagination.pageSize,
        offset: (pagination.current - 1) * pagination.pageSize,
      })
      setDetails(data?.refunds || [])
      setDetailTotal(data?.total_count || 0)
    } catch {
      setDetails([])
    } finally {
      setDetailLoading(false)
    }
  }

  const renderPieChart = () => {
    if (!pieInstance.current || !stats?.reason_distribution) return

    const data = stats.reason_distribution.map(item => ({
      name: item.reason,
      value: item.count,
    }))

    const colorPalette = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272']

    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          const item = stats.reason_distribution.find(r => r.reason === params.name)
          return `${params.name}<br/>笔数: ${params.value} (${params.percent}%)<br/>金额: ¥${item?.amount_yuan?.toFixed(2) || '0.00'}`
        },
      },
      legend: {
        orient: 'vertical',
        right: '5%',
        top: 'center',
        textStyle: { color: '#666' },
      },
      series: [
        {
          name: '退款原因',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['40%', '50%'],
          avoidLabelOverlap: true,
          itemStyle: {
            borderRadius: 6,
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            show: true,
            formatter: '{b}: {d}%',
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 16,
              fontWeight: 'bold',
            },
          },
          data,
          color: colorPalette,
        },
      ],
    }

    pieInstance.current.setOption(option, true)
  }

  // ========== 表格列定义 ==========
  const detailColumns = [
    {
      title: '退款ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '金额',
      dataIndex: 'amount_yuan',
      key: 'amount_yuan',
      width: 100,
      render: (val: number) => (
        <span style={{ color: '#cf1322', fontWeight: 600 }}>¥{val.toFixed(2)}</span>
      ),
    },
    {
      title: '摊位',
      dataIndex: 'booth_name',
      key: 'booth_name',
      width: 140,
      render: (name: string | null) => name || '-',
    },
    {
      title: '参与者',
      dataIndex: 'participant_name',
      key: 'participant_name',
      width: 120,
      render: (name: string | null) => name || '-',
    },
    {
      title: '卡号',
      dataIndex: 'card_uid',
      key: 'card_uid',
      width: 120,
      render: (uid: string | null) => uid || '-',
    },
    {
      title: '退款原因',
      dataIndex: 'reason',
      key: 'reason',
      width: 180,
      render: (reason: string) => {
        const colorMap: Record<string, string> = {
          '操作失误': 'blue',
          '商品质量': 'red',
          '服务不周': 'orange',
          '缺货/无法提供': 'purple',
          '价格争议': 'gold',
          '其他': 'default',
        }
        const color = colorMap[reason] || 'default'
        return <Tag color={color}>{reason}</Tag>
      },
    },
    {
      title: '操作员',
      dataIndex: 'operator_name',
      key: 'operator_name',
      width: 100,
      render: (name: string | null) => name || '-',
    },
    {
      title: '退款时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (time: string) => time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
    {
      title: '原交易ID',
      dataIndex: 'original_transaction_id',
      key: 'original_transaction_id',
      width: 90,
      render: (id: number | null) => id || '-',
    },
  ]

  return (
    <div style={{ padding: '0' }}>
      {/* 顶部控制栏 */}
      <Space style={{ marginBottom: 16 }}>
        <Select
          style={{ width: 200 }}
          placeholder="选择活动"
          value={selectedEventId}
          onChange={(val) => {
            setSelectedEventId(val)
            setPagination({ current: 1, pageSize: 20 })
          }}
          options={events.map(e => ({ label: e.name, value: e.id }))}
        />
        <Badge count={stats?.alerts?.length || 0} offset={[0, 0]}>
          <Tag color={stats?.alerts?.length ? 'red' : 'green'} style={{ fontSize: 14, padding: '4px 12px' }}>
            {stats?.alerts?.length ? `${stats.alerts.length} 个预警` : '无异常'}
          </Tag>
        </Badge>
      </Space>

      {/* 异常预警区域 */}
      {stats?.alerts && stats.alerts.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          {stats.alerts.map((alert: RefundAlert) => (
            <Alert
              key={alert.booth_id}
              type={alert.alert_level === 'critical' ? 'error' : 'warning'}
              showIcon
              icon={alert.alert_level === 'critical' ? <AlertOutlined /> : <WarningOutlined />}
              message={
                <span style={{
                  fontWeight: 700,
                  animation: alertFlash ? 'none' : undefined,
                  color: alert.alert_level === 'critical' ? '#cf1322' : '#d46b08',
                  opacity: alertFlash ? 1 : 0.6,
                  transition: 'opacity 0.4s',
                }}>
                  ⚠️ 异常预警：「{alert.booth_name}」({alert.class_name})
                  在 {alert.window_minutes} 分钟内发生 {alert.refund_count_in_window} 笔退款！
                </span>
              }
              description={`最近退款时间: ${alert.latest_refund_time ? dayjs(alert.latest_refund_time).format('HH:mm:ss') : '-'} | 建议立即核查是否存在刷单恶意退款行为`}
              style={{
                marginBottom: 8,
                borderColor: alert.alert_level === 'critical' ? '#ff4d4f' : '#faad14',
                backgroundColor: alertFlash
                  ? (alert.alert_level === 'critical' ? '#fff1f0' : '#fffbe6')
                  : (alert.alert_level === 'critical' ? '#fff2f0' : '#fffce6'),
                transition: 'background-color 0.4s',
              }}
            />
          ))}
        </div>
      )}

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="退款总额"
              value={stats?.summary?.total_refund_amount_yuan || 0}
              prefix={<DollarOutlined />}
              suffix="元"
              precision={2}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="退款笔数"
              value={stats?.summary?.total_refund_count || 0}
              suffix="笔"
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="全场退款率"
              value={stats?.summary?.overall_refund_rate || 0}
              prefix={<PercentageOutlined />}
              suffix="%"
              precision={2}
              valueStyle={{ color: (stats?.summary?.overall_refund_rate || 0) > 5 ? '#cf1322' : '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="支付总笔数"
              value={stats?.summary?.total_pay_count || 0}
              suffix="笔"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 中间区域：Top 3 + 饼图 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        {/* 退款率 Top 3 摊位 */}
        <Col span={10}>
          <Card
            title={
              <Space>
                <ShopOutlined />
                <span>退款率最高 Top 3 摊位</span>
              </Space>
            }
            style={{ height: 360 }}
          >
            {stats?.top_refund_booths && stats.top_refund_booths.length > 0 ? (
              <div>
                {stats.top_refund_booths.map((booth, index) => (
                  <div
                    key={booth.booth_id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '12px 16px',
                      marginBottom: 8,
                      borderRadius: 8,
                      background: index === 0 ? '#fff1f0' : index === 1 ? '#fff7e6' : '#f6ffed',
                      border: `1px solid ${index === 0 ? '#ffa39e' : index === 1 ? '#ffd591' : '#b7eb8f'}`,
                    }}
                  >
                    <div style={{
                      width: 32,
                      height: 32,
                      borderRadius: '50%',
                      background: index === 0 ? '#ff4d4f' : index === 1 ? '#faad14' : '#52c41a',
                      color: '#fff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                      marginRight: 12,
                    }}>
                      {index + 1}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, fontSize: 14 }}>
                        {booth.booth_name}
                        <span style={{ color: '#999', fontSize: 12, marginLeft: 8 }}>
                          {booth.class_name}
                        </span>
                      </div>
                      <div style={{ color: '#666', fontSize: 12, marginTop: 2 }}>
                        退款 {booth.refund_count} 笔 / 支付 {booth.pay_count} 笔 | 退款额 ¥{booth.refund_amount_yuan.toFixed(2)}
                      </div>
                    </div>
                    <Tooltip title={`退款率 = 退款笔数 / 支付笔数 × 100%`}>
                      <Tag color={booth.refund_rate > 10 ? 'red' : booth.refund_rate > 5 ? 'orange' : 'green'} style={{ fontSize: 14, padding: '2px 8px' }}>
                        {booth.refund_rate.toFixed(1)}%
                      </Tag>
                    </Tooltip>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', color: '#999', paddingTop: 60 }}>
                暂无退款数据
              </div>
            )}
          </Card>
        </Col>

        {/* 退款原因分布饼图 */}
        <Col span={14}>
          <Card
            title={
              <Space>
                <PercentageOutlined />
                <span>退款原因分布</span>
              </Space>
            }
            style={{ height: 360 }}
          >
            {stats?.reason_distribution && stats.reason_distribution.length > 0 ? (
              <div ref={pieChartRef} style={{ width: '100%', height: 280 }} />
            ) : (
              <div style={{ textAlign: 'center', color: '#999', paddingTop: 80 }}>
                暂无退款原因数据
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 退款明细表 */}
      <Card
        title={
          <Space>
            <Title level={5} style={{ margin: 0 }}>退款明细</Title>
            <Input
              placeholder="按原因关键词过滤"
              prefix={<SearchOutlined />}
              style={{ width: 200 }}
              allowClear
              onChange={(e) => {
                setReasonFilter(e.target.value || undefined)
                setPagination({ ...pagination, current: 1 })
              }}
            />
            <Select
              style={{ width: 150 }}
              placeholder="原因分类"
              allowClear
              onChange={(val) => {
                setReasonFilter(val || undefined)
                setPagination({ ...pagination, current: 1 })
              }}
              options={[
                { label: '操作失误', value: '操作失误' },
                { label: '商品质量', value: '商品质量' },
                { label: '服务不周', value: '服务不周' },
                { label: '缺货/无法提供', value: '缺货' },
                { label: '价格争议', value: '价格' },
              ]}
            />
          </Space>
        }
      >
        <Table
          columns={detailColumns}
          dataSource={details}
          rowKey="id"
          loading={detailLoading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: detailTotal,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条退款记录`,
            onChange: (page, pageSize) => setPagination({ current: page, pageSize }),
          }}
          scroll={{ x: 1200 }}
          size="small"
        />
      </Card>

      {/* 闪烁动画样式 */}
      <style>{`
        @keyframes alert-flash {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  )
}

export default RefundMonitor
