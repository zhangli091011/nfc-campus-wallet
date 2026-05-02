import { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Table, Select, Space } from 'antd'
import {
  UserOutlined,
  ShopOutlined,
  TransactionOutlined,
  DollarOutlined,
} from '@ant-design/icons'
import { getEvents } from '@/services/event'
import { getBooths } from '@/services/booth'
import { getParticipants } from '@/services/participant'
import { getTransactions } from '@/services/transaction'
import type { Event } from '@/services/event'
import type { Transaction } from '@/services/transaction'
import dayjs from 'dayjs'

// const { RangePicker } = DatePicker

const Dashboard = () => {
  const [events, setEvents] = useState<Event[]>([])
  const [selectedEventId, setSelectedEventId] = useState<number>()
  const [stats, setStats] = useState({
    totalBooths: 0,
    totalParticipants: 0,
    totalTransactions: 0,
    totalAmount: 0,
  })
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(false)

  // 加载活动列表
  useEffect(() => {
    loadEvents()
  }, [])

  // 加载统计数据
  useEffect(() => {
    if (selectedEventId) {
      loadStats()
      loadRecentTransactions()
    }
  }, [selectedEventId])

  const loadEvents = async () => {
    try {
      const data = await getEvents()  // 移除 status 筛选
      const eventList = data?.events || []
      setEvents(eventList)
      if (eventList.length > 0) {
        setSelectedEventId(eventList[0].id)
      }
    } catch (error) {
      // 错误已处理
      setEvents([])
    }
  }

  const loadStats = async () => {
    if (!selectedEventId) return
    setLoading(true)
    try {
      const [boothsData, participantsData, transactionsData] = await Promise.all([
        getBooths({ event_id: selectedEventId }),
        getParticipants({ event_id: selectedEventId }),
        getTransactions({ event_id: selectedEventId, limit: 1000 }),
      ])

      const booths = Array.isArray(boothsData) ? boothsData : []
      const participants = Array.isArray(participantsData) ? participantsData : []
      const transactions = transactionsData?.transactions || []

      const totalAmount = transactions
        .filter((t) => t.type === 'pay')
        .reduce((sum, t) => sum + t.amount, 0)

      setStats({
        totalBooths: booths.length,
        totalParticipants: participants.length,
        totalTransactions: transactionsData?.total_count || 0,
        totalAmount: totalAmount / 100, // 转换为元
      })
    } catch (error) {
      // 错误已处理
      setStats({
        totalBooths: 0,
        totalParticipants: 0,
        totalTransactions: 0,
        totalAmount: 0,
      })
    } finally {
      setLoading(false)
    }
  }

  const loadRecentTransactions = async () => {
    if (!selectedEventId) return
    try {
      const data = await getTransactions({
        event_id: selectedEventId,
        limit: 10,
      })
      setRecentTransactions(data?.transactions || [])
    } catch (error) {
      // 错误已处理
      setRecentTransactions([])
    }
  }

  const transactionColumns = [
    {
      title: '交易ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const typeMap: Record<string, string> = {
          recharge: '充值',
          pay: '支付',
          refund: '退款',
          correction: '更正',
        }
        return typeMap[type] || type
      },
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => `¥${(amount / 100).toFixed(2)}`,
    },
    {
      title: '卡号',
      dataIndex: 'card_uid',
      key: 'card_uid',
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
  ]

  return (
    <div>
      <Space style={{ marginBottom: 24 }}>
        <Select
          style={{ width: 200 }}
          placeholder="选择活动"
          value={selectedEventId}
          onChange={setSelectedEventId}
          options={events.map((e) => ({ label: e.name, value: e.id }))}
        />
      </Space>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="摊位数量"
              value={stats.totalBooths}
              prefix={<ShopOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="参与者数量"
              value={stats.totalParticipants}
              prefix={<UserOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="交易笔数"
              value={stats.totalTransactions}
              prefix={<TransactionOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="交易总额"
              value={stats.totalAmount}
              prefix={<DollarOutlined />}
              precision={2}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>

      <Card title="最近交易" style={{ marginBottom: 24 }}>
        <Table
          columns={transactionColumns}
          dataSource={recentTransactions}
          rowKey="id"
          pagination={false}
        />
      </Card>
    </div>
  )
}

export default Dashboard
