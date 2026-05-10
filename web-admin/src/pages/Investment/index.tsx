import React, { useEffect, useState } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Select,
  Button,
  Table,
  Tag,
  Space,
  Modal,
  message,
  InputNumber,
  Descriptions,
  Spin,
} from 'antd'
import {
  DollarCircleOutlined,
  TeamOutlined,
  ShopOutlined,
  TransactionOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { getEvents, Event } from '@/services/event'
import {
  getMarketStats,
  settleStockMarket,
  MarketStats,
  SettlementResponse,
} from '@/services/investment'

const { Option } = Select

/**
 * 投资管理页
 *
 * 展示活动的股市概况，并提供一键结算功能。
 */
const InvestmentManagement: React.FC = () => {
  const [events, setEvents] = useState<Event[]>([])
  const [selectedEventId, setSelectedEventId] = useState<number | undefined>()
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<MarketStats | null>(null)
  const [feeRate, setFeeRate] = useState(0.05)
  const [settlementResult, setSettlementResult] = useState<SettlementResponse | null>(null)
  const [settlementVisible, setSettlementVisible] = useState(false)

  useEffect(() => {
    loadEvents()
  }, [])

  useEffect(() => {
    if (selectedEventId) {
      loadStats()
    }
  }, [selectedEventId])

  const loadEvents = async () => {
    try {
      const res = await getEvents()
      setEvents(res.events)
      if (res.events.length > 0) {
        setSelectedEventId(res.events[0].id)
      }
    } catch (e) {
      console.error(e)
    }
  }

  const loadStats = async () => {
    if (!selectedEventId) return
    setLoading(true)
    try {
      const data = await getMarketStats(selectedEventId)
      setStats(data)
    } catch (e) {
      console.error(e)
      setStats(null)
    } finally {
      setLoading(false)
    }
  }

  const handleSettle = () => {
    if (!selectedEventId) {
      message.warning('请选择活动')
      return
    }
    if (stats?.is_settled) {
      message.warning('该活动已经结算过了')
      return
    }

    Modal.confirm({
      title: '确认执行期末结算？',
      content: (
        <Space direction="vertical">
          <div>
            活动ID: <strong>{selectedEventId}</strong>
          </div>
          <div>
            手续费率: <strong>{(feeRate * 100).toFixed(1)}%</strong>
          </div>
          <div style={{ color: '#ff4d4f' }}>
            ⚠️ 结算后不可撤销，将锁定所有订单
          </div>
        </Space>
      ),
      okText: '确认结算',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          const result = await settleStockMarket({
            event_id: selectedEventId,
            fee_rate: feeRate,
          })
          setSettlementResult(result)
          setSettlementVisible(true)
          loadStats()
          message.success('结算成功')
        } catch (e: any) {
          message.error('结算失败: ' + (e?.message || '未知错误'))
        }
      },
    })
  }

  // 结算结果表格
  const settlementColumns: ColumnsType<any> = [
    { title: '摊位', dataIndex: 'booth_name' },
    { title: '班级', dataIndex: 'class_name' },
    {
      title: '营业额',
      dataIndex: 'revenue_yuan',
      render: (v: number) => `¥${v.toFixed(2)}`,
      align: 'right',
    },
    {
      title: '净利润',
      dataIndex: 'profit_yuan',
      render: (v: number) => `¥${v.toFixed(2)}`,
      align: 'right',
    },
    {
      title: '订单数',
      dataIndex: 'order_count',
      align: 'right',
    },
    {
      title: '经营分',
      dataIndex: 'score',
      render: (v: number) => v.toFixed(0),
      align: 'right',
    },
    {
      title: '分红占比',
      dataIndex: 'ratio',
      render: (v: number) => `${(v * 100).toFixed(2)}%`,
      align: 'right',
    },
    {
      title: '售出股数',
      dataIndex: 'sold_shares',
      align: 'right',
    },
    {
      title: '最终股价',
      dataIndex: 'final_price_yuan',
      render: (v: number) => (
        <Tag color={v >= 10 ? 'green' : 'red'}>¥{v.toFixed(2)}</Tag>
      ),
      align: 'right',
    },
  ]

  return (
    <div>
      <Row gutter={16} align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <span>选择活动：</span>
        </Col>
        <Col>
          <Select
            style={{ width: 260 }}
            value={selectedEventId}
            onChange={setSelectedEventId}
            placeholder="请选择活动"
          >
            {events.map((e) => (
              <Option key={e.id} value={e.id}>
                {e.name} (ID: {e.id})
              </Option>
            ))}
          </Select>
        </Col>
        <Col>
          <Button onClick={loadStats} loading={loading}>
            刷新
          </Button>
        </Col>
      </Row>

      <Spin spinning={loading}>
        {stats && (
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="总投资额"
                  value={stats.total_investment_yuan}
                  prefix={<DollarCircleOutlined />}
                  suffix="元"
                  precision={2}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="全局奖金池"
                  value={stats.global_pool_yuan}
                  prefix={<ThunderboltOutlined />}
                  suffix="元"
                  precision={2}
                  valueStyle={{ color: '#faad14' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="投资人数"
                  value={stats.total_investors}
                  prefix={<TeamOutlined />}
                  suffix="人"
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="参与摊位"
                  value={stats.total_booths}
                  prefix={<ShopOutlined />}
                  suffix="个"
                />
              </Card>
            </Col>
          </Row>
        )}

        {stats && (
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Card>
                <Statistic
                  title="订单总数"
                  value={stats.total_orders}
                  prefix={<TransactionOutlined />}
                  suffix="单"
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="手续费收入"
                  value={stats.fee_collected_yuan}
                  prefix={<DollarCircleOutlined />}
                  suffix="元"
                  precision={2}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="结算状态"
                  value={stats.is_settled ? '已结算' : '未结算'}
                  prefix={stats.is_settled ? <CheckCircleOutlined /> : <ClockCircleOutlined />}
                  valueStyle={{ color: stats.is_settled ? '#52c41a' : '#faad14' }}
                />
              </Card>
            </Col>
          </Row>
        )}
      </Spin>

      <Card
        title="期末一键结算"
        extra={
          <Space>
            <span>手续费率：</span>
            <InputNumber
              min={0}
              max={1}
              step={0.01}
              value={feeRate}
              onChange={(v) => setFeeRate(v ?? 0.05)}
              formatter={(v) => `${((v as number) * 100).toFixed(1)}%`}
              parser={(v) => (parseFloat(v?.replace('%', '') || '0') / 100) as any}
              disabled={stats?.is_settled}
            />
            <Button
              type="primary"
              danger
              onClick={handleSettle}
              disabled={!selectedEventId || stats?.is_settled}
            >
              执行结算
            </Button>
          </Space>
        }
      >
        <Descriptions column={1} bordered size="small">
          <Descriptions.Item label="结算逻辑">
            全局奖金池 = 全场投资总金额 × (1 - 手续费率)
          </Descriptions.Item>
          <Descriptions.Item label="摊位分">
            0.2 × 营业额 + 0.6 × 净利润 + 0.2 × 订单数
          </Descriptions.Item>
          <Descriptions.Item label="摊位分红占比">
            该摊位分 / 全场总分
          </Descriptions.Item>
          <Descriptions.Item label="最终股价">
            (奖金池 × 占比) / 该摊位售出股数
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Modal
        title="🏆 结算结果"
        open={settlementVisible}
        onCancel={() => setSettlementVisible(false)}
        footer={[
          <Button key="close" onClick={() => setSettlementVisible(false)}>
            关闭
          </Button>,
        ]}
        width={1100}
      >
        {settlementResult && (
          <>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={8}>
                <Statistic
                  title="总投资额"
                  value={settlementResult.total_investment_yuan}
                  suffix="元"
                  precision={2}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="奖金池"
                  value={settlementResult.global_pool_yuan}
                  suffix="元"
                  precision={2}
                  valueStyle={{ color: '#faad14' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="手续费"
                  value={settlementResult.fee_collected_yuan}
                  suffix="元"
                  precision={2}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
            </Row>
            <Table
              columns={settlementColumns}
              dataSource={settlementResult.booths}
              rowKey="booth_id"
              pagination={false}
              size="small"
            />
          </>
        )}
      </Modal>
    </div>
  )
}

export default InvestmentManagement
