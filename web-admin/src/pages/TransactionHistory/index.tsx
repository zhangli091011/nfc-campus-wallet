import { useState, useEffect } from 'react'
import { Table, Space, Select, DatePicker, Button, Tag, Input } from 'antd'
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons'
import {
  getTransactions,
  type Transaction,
  type TransactionListResponse,
} from '@/services/transaction'
import { getEvents, type Event } from '@/services/event'
import { getBooths, type Booth } from '@/services/booth'
import dayjs, { Dayjs } from 'dayjs'

const { RangePicker } = DatePicker

const TransactionHistory = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [events, setEvents] = useState<Event[]>([])
  const [booths, setBooths] = useState<Booth[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedEventId, setSelectedEventId] = useState<number>()
  const [selectedBoothId, setSelectedBoothId] = useState<number>()
  const [selectedType, setSelectedType] = useState<string>()
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20 })

  useEffect(() => {
    loadEvents()
  }, [])

  useEffect(() => {
    if (selectedEventId) {
      loadBooths()
      loadTransactions()
    }
  }, [selectedEventId, selectedBoothId, selectedType, dateRange, pagination.current])

  const loadEvents = async () => {
    try {
      const data = await getEvents({ status: 'active' })
      setEvents(data)
      if (data.length > 0) {
        setSelectedEventId(data[0].id)
      }
    } catch (error) {
      // 错误已处理
    }
  }

  const loadBooths = async () => {
    if (!selectedEventId) return
    try {
      const data = await getBooths({ event_id: selectedEventId, limit: 100 })
      setBooths(data)
    } catch (error) {
      // 错误已处理
    }
  }

  const loadTransactions = async () => {
    if (!selectedEventId) return
    setLoading(true)
    try {
      const params: any = {
        event_id: selectedEventId,
        limit: pagination.pageSize,
        offset: (pagination.current - 1) * pagination.pageSize,
      }

      if (selectedBoothId) {
        params.booth_id = selectedBoothId
      }

      if (selectedType) {
        params.type = selectedType
      }

      if (dateRange) {
        params.start_date = dateRange[0].format('YYYY-MM-DD')
        params.end_date = dateRange[1].format('YYYY-MM-DD')
      }

      const data: TransactionListResponse = await getTransactions(params)
      setTransactions(data.transactions)
      setTotalCount(data.total_count)
    } catch (error) {
      // 错误已处理
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setSelectedBoothId(undefined)
    setSelectedType(undefined)
    setDateRange(null)
    setPagination({ current: 1, pageSize: 20 })
  }

  const columns = [
    {
      title: '交易ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type: string) => {
        const typeMap: Record<string, { text: string; color: string }> = {
          recharge: { text: '充值', color: 'success' },
          pay: { text: '支付', color: 'processing' },
          refund: { text: '退款', color: 'warning' },
          correction: { text: '更正', color: 'default' },
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
        const sign = record.type === 'pay' ? '-' : '+'
        const color = record.type === 'pay' ? '#ff4d4f' : '#52c41a'
        return (
          <span style={{ color }}>
            {sign}¥{(amount / 100).toFixed(2)}
          </span>
        )
      },
    },
    {
      title: '交易前余额',
      dataIndex: 'balance_before',
      key: 'balance_before',
      width: 120,
      render: (balance: number) => `¥${(balance / 100).toFixed(2)}`,
    },
    {
      title: '交易后余额',
      dataIndex: 'balance_after',
      key: 'balance_after',
      width: 120,
      render: (balance: number) => `¥${(balance / 100).toFixed(2)}`,
    },
    {
      title: '卡号',
      dataIndex: 'card_uid',
      key: 'card_uid',
      width: 150,
    },
    {
      title: '摊位ID',
      dataIndex: 'booth_id',
      key: 'booth_id',
      width: 100,
      render: (id: number | null) => id || '-',
    },
    {
      title: '商品ID',
      dataIndex: 'product_id',
      key: 'product_id',
      width: 100,
      render: (id: number | null) => id || '-',
    },
    {
      title: '操作员ID',
      dataIndex: 'operator_id',
      key: 'operator_id',
      width: 100,
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
      width: 180,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
  ]

  return (
    <div>
      <Space style={{ marginBottom: 16 }} wrap>
        <Select
          style={{ width: 200 }}
          placeholder="选择活动"
          value={selectedEventId}
          onChange={(value) => {
            setSelectedEventId(value)
            setSelectedBoothId(undefined)
            setPagination({ current: 1, pageSize: 20 })
          }}
          options={events.map((e) => ({ label: e.name, value: e.id }))}
        />
        <Select
          style={{ width: 200 }}
          placeholder="选择摊位（可选）"
          value={selectedBoothId}
          onChange={(value) => {
            setSelectedBoothId(value)
            setPagination({ current: 1, pageSize: 20 })
          }}
          allowClear
          options={booths.map((b) => ({ label: b.name, value: b.id }))}
        />
        <Select
          style={{ width: 150 }}
          placeholder="交易类型"
          value={selectedType}
          onChange={(value) => {
            setSelectedType(value)
            setPagination({ current: 1, pageSize: 20 })
          }}
          allowClear
        >
          <Select.Option value="recharge">充值</Select.Option>
          <Select.Option value="pay">支付</Select.Option>
          <Select.Option value="refund">退款</Select.Option>
          <Select.Option value="correction">更正</Select.Option>
        </Select>
        <RangePicker
          value={dateRange}
          onChange={(dates) => {
            setDateRange(dates as [Dayjs, Dayjs] | null)
            setPagination({ current: 1, pageSize: 20 })
          }}
        />
        <Button icon={<SearchOutlined />} type="primary" onClick={loadTransactions}>
          查询
        </Button>
        <Button icon={<ReloadOutlined />} onClick={handleReset}>
          重置
        </Button>
      </Space>

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
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page, pageSize) => {
            setPagination({ current: page, pageSize })
          },
        }}
        scroll={{ x: 1500 }}
      />
    </div>
  )
}

export default TransactionHistory
