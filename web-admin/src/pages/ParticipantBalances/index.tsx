import { useState, useEffect, useCallback } from 'react'
import {
  Table,
  Select,
  Input,
  Space,
  Tag,
  Card,
  Statistic,
  Row,
  Col,
  Typography,
} from 'antd'
import {
  WalletOutlined,
  TeamOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import { getEvents, type Event } from '@/services/event'
import request from '@/utils/request'
import type { ColumnsType } from 'antd/es/table'

const { Title } = Typography

interface ParticipantBalance {
  id: number
  name: string
  card_uid: string
  class_name?: string
  student_no?: string
  status: string
  balance: number
  credit_borrowed: number
  credit_fee_paid: number
}

interface BalancesResponse {
  participants: ParticipantBalance[]
  total_count: number
  total_balance: number
  event_id: number
}

const ParticipantBalances = () => {
  const [events, setEvents] = useState<Event[]>([])
  const [selectedEventId, setSelectedEventId] = useState<number>()
  const [data, setData] = useState<ParticipantBalance[]>([])
  const [loading, setLoading] = useState(false)
  const [totalCount, setTotalCount] = useState(0)
  const [totalBalance, setTotalBalance] = useState(0)
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('balance_desc')
  const [pagination, setPagination] = useState({ current: 1, pageSize: 50 })

  useEffect(() => {
    loadEvents()
  }, [])

  const loadEvents = async () => {
    try {
      const res = await getEvents()
      const eventList = res?.events || []
      setEvents(eventList)
      if (eventList.length > 0) {
        setSelectedEventId(eventList[0].id)
      }
    } catch {
      setEvents([])
    }
  }

  const loadBalances = useCallback(async () => {
    if (!selectedEventId) return
    setLoading(true)
    try {
      const res = await request.get<any, BalancesResponse>('/admin/participants/balances', {
        params: {
          event_id: selectedEventId,
          search: search || undefined,
          sort_by: sortBy,
          limit: pagination.pageSize,
          offset: (pagination.current - 1) * pagination.pageSize,
        },
      })
      setData(res.participants)
      setTotalCount(res.total_count)
      setTotalBalance(res.total_balance)
    } catch {
      setData([])
      setTotalCount(0)
      setTotalBalance(0)
    } finally {
      setLoading(false)
    }
  }, [selectedEventId, search, sortBy, pagination])

  useEffect(() => {
    loadBalances()
  }, [loadBalances])

  const handleEventChange = (eventId: number) => {
    setSelectedEventId(eventId)
    setPagination({ ...pagination, current: 1 })
  }

  const handleSearch = (value: string) => {
    setSearch(value)
    setPagination({ ...pagination, current: 1 })
  }

  const handleSortChange = (value: string) => {
    setSortBy(value)
    setPagination({ ...pagination, current: 1 })
  }

  const columns: ColumnsType<ParticipantBalance> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 70,
    },
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
      width: 120,
    },
    {
      title: '卡号',
      dataIndex: 'card_uid',
      key: 'card_uid',
      width: 140,
    },
    {
      title: '班级',
      dataIndex: 'class_name',
      key: 'class_name',
      width: 120,
      render: (text: string) => text || '-',
    },
    {
      title: '学号',
      dataIndex: 'student_no',
      key: 'student_no',
      width: 120,
      render: (text: string) => text || '-',
    },
    {
      title: '余额（元）',
      dataIndex: 'balance',
      key: 'balance',
      width: 130,
      align: 'right',
      render: (balance: number) => (
        <span style={{ color: balance > 0 ? '#52c41a' : balance < 0 ? '#ff4d4f' : '#999', fontWeight: 600 }}>
          ¥{balance.toFixed(2)}
        </span>
      ),
    },
    {
      title: '借款总额（元）',
      dataIndex: 'credit_borrowed',
      key: 'credit_borrowed',
      width: 130,
      align: 'right',
      render: (val: number) => val > 0 ? <span style={{ color: '#fa8c16' }}>¥{val.toFixed(2)}</span> : '-',
    },
    {
      title: '手续费（元）',
      dataIndex: 'credit_fee_paid',
      key: 'credit_fee_paid',
      width: 120,
      align: 'right',
      render: (val: number) => val > 0 ? `¥${val.toFixed(2)}` : '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          active: 'success',
          inactive: 'default',
          blocked: 'error',
        }
        const textMap: Record<string, string> = {
          active: '正常',
          inactive: '未激活',
          blocked: '已冻结',
        }
        return <Tag color={colorMap[status]}>{textMap[status] || status}</Tag>
      },
    },
  ]

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>参与者余额查询</Title>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="参与者总数"
              value={totalCount}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="余额总计（元）"
              value={totalBalance}
              precision={2}
              prefix={<WalletOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="人均余额（元）"
              value={totalCount > 0 ? totalBalance / totalCount : 0}
              precision={2}
              prefix="¥"
            />
          </Card>
        </Col>
      </Row>

      {/* 筛选栏 */}
      <Space style={{ marginBottom: 16 }} wrap>
        <Select
          style={{ width: 200 }}
          placeholder="选择活动"
          value={selectedEventId}
          onChange={handleEventChange}
          options={events.map((e) => ({ label: e.name, value: e.id }))}
        />
        <Input.Search
          style={{ width: 250 }}
          placeholder="搜索姓名/卡号/学号"
          prefix={<SearchOutlined />}
          allowClear
          onSearch={handleSearch}
          enterButton
        />
        <Select
          style={{ width: 160 }}
          value={sortBy}
          onChange={handleSortChange}
          options={[
            { label: '余额从高到低', value: 'balance_desc' },
            { label: '余额从低到高', value: 'balance_asc' },
            { label: '按姓名排序', value: 'name' },
          ]}
        />
      </Space>

      {/* 数据表格 */}
      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: totalCount,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条`,
          pageSizeOptions: ['20', '50', '100', '200'],
          onChange: (page, pageSize) => setPagination({ current: page, pageSize }),
        }}
        scroll={{ x: 1000 }}
      />
    </div>
  )
}

export default ParticipantBalances
