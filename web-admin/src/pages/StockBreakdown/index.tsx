import { useState, useEffect, useCallback } from 'react'
import {
  Card,
  Table,
  Select,
  Space,
  Statistic,
  Row,
  Col,
  Button,
  Tag,
  Tooltip,
  Descriptions,
  Modal,
} from 'antd'
import {
  ReloadOutlined,
  StockOutlined,
  InfoCircleOutlined,
  TrophyOutlined,
} from '@ant-design/icons'
import request from '@/utils/request'
import { getEvents, type Event } from '@/services/event'

interface BoothBreakdown {
  booth_id: number
  booth_name: string
  class_name: string
  shares: number
  raw: {
    revenue: number
    profit: number
    traffic: number
    avg_ticket: number
    investor_count: number
    growth: number
  }
  normalized: {
    revenue: number
    profit: number
    traffic: number
    avg_ticket: number
    investor_count: number
    growth: number
  }
  weighted: {
    revenue: number
    profit: number
    traffic: number
    avg_ticket: number
    investor_count: number
    growth: number
  }
  score: number
  ratio: number
  booth_pool: number
  current_price: number
  base_price: number
  change_percent: number
  rank: number
}

interface BreakdownResponse {
  pool_info: {
    total_investment: number
    fee: number
    net_pool: number
    fee_rate: number
    order_count: number
    investor_count: number
  }
  weights: Record<string, number>
  totals: Record<string, number>
  total_score: number
  initial_price: number
  booths: BoothBreakdown[]
}

const DIM_LABELS: Record<string, string> = {
  revenue: '营业额',
  profit: '净利润',
  traffic: '人流',
  avg_ticket: '客单价',
  investor_count: '投资人数',
  growth: '增长率',
}

const StockBreakdown = () => {
  const [events, setEvents] = useState<Event[]>([])
  const [selectedEventId, setSelectedEventId] = useState<number>()
  const [data, setData] = useState<BreakdownResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [detailBooth, setDetailBooth] = useState<BoothBreakdown | null>(null)

  const loadEvents = useCallback(async () => {
    try {
      const res = await getEvents()
      const list = res?.events || []
      setEvents(list)
      if (list.length > 0) {
        const active = list.find((e: Event) => e.status === 'active')
        setSelectedEventId(active ? active.id : list[0].id)
      }
    } catch {
      setEvents([])
    }
  }, [])

  const loadBreakdown = useCallback(async () => {
    if (!selectedEventId) return
    setLoading(true)
    try {
      const res = await request.get<any, BreakdownResponse>(
        `/stock/price-breakdown/${selectedEventId}`
      )
      setData(res)
    } catch {
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [selectedEventId])

  useEffect(() => {
    loadEvents()
  }, [loadEvents])

  useEffect(() => {
    if (selectedEventId) {
      loadBreakdown()
    }
  }, [selectedEventId, loadBreakdown])

  const showDetail = (record: BoothBreakdown) => {
    setDetailBooth(record)
    setDetailModalVisible(true)
  }

  const columns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 70,
      render: (rank: number) => {
        if (rank === 1) return <Tag color="gold" icon={<TrophyOutlined />}>No.1</Tag>
        if (rank === 2) return <Tag color="silver">No.2</Tag>
        if (rank === 3) return <Tag color="orange">No.3</Tag>
        return `#${rank}`
      },
    },
    {
      title: '摊位',
      dataIndex: 'booth_name',
      key: 'booth_name',
      width: 140,
      render: (name: string, r: BoothBreakdown) => (
        <div>
          <div style={{ fontWeight: 600 }}>{name}</div>
          <div style={{ fontSize: 12, color: '#999' }}>{r.class_name}</div>
        </div>
      ),
    },
    {
      title: '当前股价',
      dataIndex: 'current_price',
      key: 'current_price',
      width: 110,
      render: (price: number, r: BoothBreakdown) => (
        <div>
          <div style={{ fontWeight: 600, fontSize: 16 }}>¥{price.toFixed(2)}</div>
          <div
            style={{
              fontSize: 12,
              color: r.change_percent >= 0 ? '#52c41a' : '#ff4d4f',
            }}
          >
            {r.change_percent >= 0 ? '+' : ''}
            {r.change_percent.toFixed(2)}%
          </div>
        </div>
      ),
    },
    {
      title: '综合分',
      dataIndex: 'score',
      key: 'score',
      width: 110,
      render: (score: number) => (
        <span style={{ fontWeight: 600, color: '#1677ff' }}>{score.toFixed(4)}</span>
      ),
    },
    {
      title: '分红占比',
      dataIndex: 'ratio',
      key: 'ratio',
      width: 100,
      render: (ratio: number) => `${(ratio * 100).toFixed(2)}%`,
    },
    {
      title: '持股数',
      dataIndex: 'shares',
      key: 'shares',
      width: 90,
    },
    {
      title: '分到资金池',
      dataIndex: 'booth_pool',
      key: 'booth_pool',
      width: 110,
      render: (v: number) => `¥${v.toFixed(2)}`,
    },
    {
      title: '营业额',
      dataIndex: ['raw', 'revenue'],
      key: 'revenue',
      width: 100,
      render: (v: number) => `¥${v.toFixed(2)}`,
    },
    {
      title: '净利润',
      dataIndex: ['raw', 'profit'],
      key: 'profit',
      width: 100,
      render: (v: number) => `¥${v.toFixed(2)}`,
    },
    {
      title: '人流',
      dataIndex: ['raw', 'traffic'],
      key: 'traffic',
      width: 70,
    },
    {
      title: '客单价',
      dataIndex: ['raw', 'avg_ticket'],
      key: 'avg_ticket',
      width: 90,
      render: (v: number) => `¥${v.toFixed(2)}`,
    },
    {
      title: '投资人',
      dataIndex: ['raw', 'investor_count'],
      key: 'investor_count',
      width: 80,
    },
    {
      title: '增长率',
      dataIndex: ['raw', 'growth'],
      key: 'growth',
      width: 90,
      render: (v: number) => v.toFixed(2),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      fixed: 'right' as const,
      render: (_: any, r: BoothBreakdown) => (
        <Button type="link" size="small" icon={<InfoCircleOutlined />} onClick={() => showDetail(r)}>
          计算明细
        </Button>
      ),
    },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>
        <StockOutlined style={{ marginRight: 8 }} />
        股价计算公示
      </h2>

      <Space style={{ marginBottom: 16 }} wrap>
        <Select
          style={{ width: 240 }}
          placeholder="选择活动"
          value={selectedEventId}
          onChange={setSelectedEventId}
          options={events.map((e) => ({ label: e.name, value: e.id }))}
        />
        <Button icon={<ReloadOutlined />} onClick={loadBreakdown} loading={loading}>
          刷新
        </Button>
      </Space>

      {data && (
        <>
          {/* 资金池信息 */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="总投入"
                  value={data.pool_info.total_investment}
                  precision={2}
                  prefix="¥"
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title={`官方手续费 (${(data.pool_info.fee_rate * 100).toFixed(0)}%)`}
                  value={data.pool_info.fee}
                  precision={2}
                  prefix="¥"
                  valueStyle={{ color: '#fa8c16' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="净资金池（分红）"
                  value={data.pool_info.net_pool}
                  precision={2}
                  prefix="¥"
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="订单数 / 投资人"
                  value={`${data.pool_info.order_count} / ${data.pool_info.investor_count}`}
                />
              </Card>
            </Col>
          </Row>

          {/* 权重配置和全场总和 */}
          <Card size="small" style={{ marginBottom: 16 }} title="评分权重与全场总和">
            <Descriptions column={6} size="small" bordered>
              {Object.keys(DIM_LABELS).map((key) => (
                <Descriptions.Item key={key} label={DIM_LABELS[key]}>
                  <div>
                    权重: <Tag color="blue">{(data.weights[key] * 100).toFixed(0)}%</Tag>
                  </div>
                  <div style={{ marginTop: 4, fontSize: 12, color: '#666' }}>
                    总和:{' '}
                    {key === 'traffic' || key === 'investor_count'
                      ? data.totals[key]
                      : data.totals[key]?.toFixed(2)}
                  </div>
                </Descriptions.Item>
              ))}
            </Descriptions>
            <div style={{ marginTop: 12, color: '#666' }}>
              全场综合分总和：<strong style={{ color: '#1677ff' }}>{data.total_score.toFixed(4)}</strong>
              <Tooltip title="股价 = (净资金池 × 摊位综合分占比) ÷ 摊位持股数">
                <InfoCircleOutlined style={{ marginLeft: 8, color: '#999' }} />
              </Tooltip>
              　|　初始发行价：<strong>¥{data.initial_price.toFixed(2)}</strong>
            </div>
          </Card>

          {/* 摊位明细表格 */}
          <Table
            columns={columns}
            dataSource={data.booths}
            rowKey="booth_id"
            loading={loading}
            pagination={{ pageSize: 50, showSizeChanger: true }}
            scroll={{ x: 1400 }}
            size="small"
          />
        </>
      )}

      {/* 详细计算弹窗 */}
      <Modal
        title={`${detailBooth?.booth_name || ''} - 股价计算明细`}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={700}
      >
        {detailBooth && data && (
          <div>
            <Descriptions title="原始经营数据" column={2} size="small" bordered>
              <Descriptions.Item label="营业额">¥{detailBooth.raw.revenue.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="净利润">¥{detailBooth.raw.profit.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="人流">{detailBooth.raw.traffic}</Descriptions.Item>
              <Descriptions.Item label="客单价">¥{detailBooth.raw.avg_ticket.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="投资人数">{detailBooth.raw.investor_count}</Descriptions.Item>
              <Descriptions.Item label="增长率">{detailBooth.raw.growth.toFixed(2)}</Descriptions.Item>
            </Descriptions>

            <Descriptions title="归一化值（占全场比例）" column={2} size="small" bordered style={{ marginTop: 16 }}>
              {Object.keys(DIM_LABELS).map((key) => (
                <Descriptions.Item key={key} label={DIM_LABELS[key]}>
                  {(detailBooth.normalized[key as keyof typeof detailBooth.normalized] * 100).toFixed(2)}%
                </Descriptions.Item>
              ))}
            </Descriptions>

            <Descriptions title="加权得分（归一化 × 权重）" column={2} size="small" bordered style={{ marginTop: 16 }}>
              {Object.keys(DIM_LABELS).map((key) => (
                <Descriptions.Item key={key} label={`${DIM_LABELS[key]} (权重 ${(data.weights[key] * 100).toFixed(0)}%)`}>
                  {detailBooth.weighted[key as keyof typeof detailBooth.weighted].toFixed(6)}
                </Descriptions.Item>
              ))}
            </Descriptions>

            <Descriptions title="最终计算" column={2} size="small" bordered style={{ marginTop: 16 }}>
              <Descriptions.Item label="综合分">
                <strong style={{ color: '#1677ff' }}>{detailBooth.score.toFixed(6)}</strong>
              </Descriptions.Item>
              <Descriptions.Item label="分红占比">
                {(detailBooth.ratio * 100).toFixed(4)}%
              </Descriptions.Item>
              <Descriptions.Item label="持股数">{detailBooth.shares}</Descriptions.Item>
              <Descriptions.Item label="分到资金池">¥{detailBooth.booth_pool.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="当前股价" span={2}>
                <strong style={{ fontSize: 18, color: '#52c41a' }}>
                  ¥{detailBooth.current_price.toFixed(2)}
                </strong>
                <span
                  style={{
                    marginLeft: 12,
                    color: detailBooth.change_percent >= 0 ? '#52c41a' : '#ff4d4f',
                  }}
                >
                  ({detailBooth.change_percent >= 0 ? '+' : ''}
                  {detailBooth.change_percent.toFixed(2)}%)
                </span>
              </Descriptions.Item>
            </Descriptions>

            <Card size="small" style={{ marginTop: 16, background: '#fafafa' }}>
              <div style={{ fontSize: 13, color: '#666', lineHeight: 1.8 }}>
                <strong>计算公式：</strong>
                <br />
                1. 综合分 = Σ(权重 × 归一化值)，6维度加权
                <br />
                2. 分红占比 = 该摊位综合分 / 全场综合分总和
                <br />
                3. 摊位资金池 = 净资金池 × 分红占比
                <br />
                4. 当前股价 = 摊位资金池 / 持股数（无人持股则按初始价 × 预期倍数）
                <br />
                <em style={{ color: '#999' }}>股价下限保护：不低于 ¥0.50</em>
              </div>
            </Card>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default StockBreakdown
