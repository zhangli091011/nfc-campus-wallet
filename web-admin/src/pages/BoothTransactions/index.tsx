import { useState, useEffect } from 'react'
import { Table, Space, Select, DatePicker, Button, Tag, Card, Statistic, Row, Col } from 'antd'
import {
  SearchOutlined,
  ReloadOutlined,
  ShopOutlined,
  DollarOutlined,
  TransactionOutlined,
} from '@ant-design/icons'
import {
  getTransactions,
  type Transaction,
  type TransactionListResponse,
} from '@/services/transaction'
import { getEvents, type Event } from '@/services/event'
import { getBooths, type Booth } from '@/services/booth'
import dayjs, { Dayjs } from 'dayjs'

const { RangePicker } = DatePicker

const BoothTransactions = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [events, setEvents] = useState<Event[]>([])
  const [booths, setBooths] = useState<Booth[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedEventId, setSelectedEventId] = useState<number>()
  const [selectedBoothId, setSelectedBoothId] = useState<number>()
  const [selectedType, setSelectedType] = useState<string>()
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 50 })

  useEffect(() => {
    loadEvents()
  }, [])

  useEffect(() => {
    if (selectedEventId) {
      loadBooths()
    }
  }, [selectedEventId])

  useEffect(() => {
    if (selectedEventId && selectedBoothId) {
      loadTransactions()
    }
  }, [selectedEventId, selectedBoothId, selectedType, dateRange, pagination.current, pagination.pageSize])

  const loadEvents = async () => {
    try {
      const data = await getEvents()
      const eventList = data?.events || []
      setEvents(eventList)
      if (eventList.length > 0) {
        const activeEvent = eventList.find((e: Event) => e.status === 'active')
        setSelectedEventId(activeEvent ? activeEvent.id : eventList[0].id)
      }
    } catch (error) {
      setEvents([])
    }
  }

  const loadBooths = async () => {
    if (!selectedEventId) return
    try {
      const data = await getBooths({ event_id: selectedEventId, limit: 200 })
      setBooths(Array.isArray(data) ? data : [])
    } catch (error) {
      setBooths([])
    }
  }

  const loadTransactions = async () => {
    if (!selectedEventId || !selectedBoothId) return
    setLoading(true)
    try {
      const params: any = {
        event_id: selectedEventId,
        booth_id: selectedBoothId,
        limit: pagination.pageSize,
        offset: (pagination.current - 1) * pagination.pageSize,
      }

      if (selectedType) {
        params.type = selectedType
      }

      if (dateRange) {
        params.start_date = dateRange[0].format('YYYY-MM-DD')
        params.end_date = dateRange[1].format('YYYY-MM-DD')
      }

      const data: TransactionListResponse = await getTransactions(params)
      setTransactions(data?.transactions || [])
      setTotalCount(data?.total_count || 0)
    } catch (error) {
      setTransactions([])
      setTotalCount(0)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setSelectedType(undefined)
    setDateRange(null)
    setPagination({ current: 1, pageSize: 50 })
  }

  // 统计数据
  const totalIncome = transactions
    .filter((t) => t.type === 'pay' || t.type === 'cash_payment')
    .reduce((sum, t) => sum + t.amount, 0)

  const totalRefund = transactions
    .filter((t) => t.type === 'refund')
    .reduce((sum, t) => sum + t.amount, 0)

  const selectedBooth = booths.find((b) => b.id === selectedBoothId)

  const columns = [
    {
      title: '交易ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 110,
      render: (type: string) => {
        const typeMap: Record<string, { text: string; color: string }> = {
          recharge: { text: '充值', color: 'success' },
          pay: { text: '支付', color: 'processing' },
          refund: { text: '退款', color: 'warning' },
          correction: { text: '更正', color: 'default' },
          cash_payment: { text: '现金收款', color: 'gold' },
          stock_buy: { text: '股票买入', color: 'purple' },
          stock_sell: { text: '股票卖出', color: 'magenta' },
          loan_issue: { text: '垫资发放', color: 'cyan' },
          loan_fee: { text: '手续费', color: 'orange' },
        }
        const config = typeMap[type] || { text: type, color: 'default' }
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      render: (amount: number, record: Transaction) => {
        const isDebit = ['pay', 'stock_buy', 'loan_fee'].includes(record.type)
        const sign = isDebit ? '-' : '+'
        const color = isDebit ? '#ff4d4f' : '#52c41a'
        return (
          <span style={{ color, fontWeight: 'bold' }}>
            {sign}¥{amount.toFixed(2)}
          </span>
        )
      },
    },
    {
      title: '交易前余额',
      dataIndex: 'balance_before',
      key: 'balance_before',
      width: 120,
      render: (balance: number) => `¥${balance.toFixed(2)}`,
    },
    {
      title: '交易后余额',
      dataIndex: 'balance_after',
      key: 'balance_after',
      width: 120,
      render: (balance: number) => `¥${balance.toFixed(2)}`,
    },
    {
      title: '卡号',
      dataIndex: 'card_uid',
      key: 'card_uid',
      width: 130,
      render: (uid: string | null) => uid || '-',
    },
    {
      title: '商品ID',
      dataIndex: 'product_id',
      key: 'product_id',
      width: 90,
      render: (id: number | null) => id || '-',
    },
    {
      title: '操作员',
      dataIndex: 'operator_id',
      key: 'operator_id',
      width: 90,
      render: (id: number | null) => id || '-',
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
      ellipsis: true,
      render: (remark: string | null) => remark || '-',
    },
    {
      title: '交易时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>
        <ShopOutlined style={{ marginRight: 8 }} />
        商铺流水查询
      </h2>

      {/* 筛选区 */}
      <Space style={{ marginBottom: 16 }} wrap>
        <Select
          style={{ width: 200 }}
          placeholder="选择活动"
          value={selectedEventId}
          onChange={(value) => {
            setSelectedEventId(value)
            setSelectedBoothId(undefined)
            setTransactions([])
            setTotalCount(0)
            setPagination({ current: 1, pageSize: 50 })
          }}
          options={events.map((e) => ({ label: e.name, value: e.id }))}
        />
        <Select
          style={{ width: 220 }}
          placeholder="选择商铺"
          value={selectedBoothId}
          onChange={(value) => {
            setSelectedBoothId(value)
            setPagination({ current: 1, pageSize: 50 })
          }}
          showSearch
          filterOption={(input, option) =>
            (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
          }
          options={booths.map((b) => ({
            label: `${b.name} (${b.class_name})`,
            value: b.id,
          }))}
        />
        <Select
          style={{ width: 150 }}
          placeholder="交易类型"
          value={selectedType}
          onChange={(value) => {
            setSelectedType(value)
            setPagination({ current: 1, pageSize: 50 })
          }}
          allowClear
        >
          <Select.Option value="pay">支付</Select.Option>
          <Select.Option value="refund">退款</Select.Option>
          <Select.Option value="cash_payment">现金收款</Select.Option>
          <Select.Option value="stock_buy">股票买入</Select.Option>
          <Select.Option value="stock_sell">股票卖出</Select.Option>
          <Select.Option value="recharge">充值</Select.Option>
        </Select>
        <RangePicker
          value={dateRange}
          onChange={(dates) => {
            setDateRange(dates as [Dayjs, Dayjs] | null)
            setPagination({ current: 1, pageSize: 50 })
          }}
        />
        <Button icon={<SearchOutlined />} type="primary" onClick={loadTransactions}>
          查询
        </Button>
        <Button icon={<ReloadOutlined />} onClick={handleReset}>
          重置
        </Button>
      </Space>

      {/* 统计卡片 */}
      {selectedBoothId && transactions.length > 0 && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="商铺名称"
                value={selectedBooth?.name || '-'}
                prefix={<ShopOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="总交易笔数"
                value={totalCount}
                prefix={<TransactionOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="收入总额"
                value={totalIncome}
                precision={2}
                prefix={<DollarOutlined />}
                suffix="元"
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="退款总额"
                value={totalRefund}
                precision={2}
                prefix={<DollarOutlined />}
                suffix="元"
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 交易表格 */}
      <Table
        columns={columns}
        dataSource={transactions}
        rowKey="id"
        loading={loading}
        pagination={{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: totalCount,
          showSizeChanger: true,
          pageSizeOptions: ['20', '50', '100', '200'],
          showTotal: (total) => `共 ${total} 条记录`,
          onChange: (page, pageSize) => {
            setPagination({ current: page, pageSize })
          },
        }}
        scroll={{ x: 1400 }}
        locale={{ emptyText: selectedBoothId ? '暂无交易记录' : '请先选择商铺' }}
      />
    </div>
  )
}

export default BoothTransactions
