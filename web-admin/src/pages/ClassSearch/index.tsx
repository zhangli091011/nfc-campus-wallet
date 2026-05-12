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
  Switch,
  Empty,
  Spin,
  Collapse,
  Timeline,
} from 'antd'
import {
  SearchOutlined,
  TeamOutlined,
  WalletOutlined,
  DollarOutlined,
  BookOutlined,
  TransactionOutlined,
} from '@ant-design/icons'
import { getEvents, type Event } from '@/services/event'
import request from '@/utils/request'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { Panel } = Collapse

interface TransactionRecord {
  id: number
  type: string
  amount: number
  balance_before: number
  balance_after: number
  remark: string | null
  operator_id: string | null
  card_uid: string | null
  created_at: string | null
}

interface ParticipantData {
  id: number
  name: string
  card_uid: string
  class_name: string | null
  student_no: string | null
  status: string
  balance: number
  credit_borrowed: number
  credit_fee_paid: number
  transactions: TransactionRecord[]
}

interface ClassSummary {
  total_balance: number
  total_credit_borrowed: number
  total_credit_fee: number
  total_consumed: number
  total_recharged: number
  total_refunded: number
  participant_count: number
}

interface ClassSearchResponse {
  class_name: string
  event_id: number
  participants: ParticipantData[]
  total_count: number
  summary: ClassSummary
}

interface ClassItem {
  class_name: string
  participant_count: number
  total_balance?: number
}

const typeLabels: Record<string, { text: string; color: string }> = {
  recharge: { text: '充值', color: 'green' },
  pay: { text: '消费', color: 'orange' },
  refund: { text: '退款', color: 'red' },
  adjust: { text: '调整', color: 'purple' },
  issue: { text: '发卡', color: 'blue' },
  loan_issue: { text: '贷款发放', color: 'cyan' },
  loan_fee: { text: '贷款手续费', color: 'volcano' },
  stock_buy: { text: '购买股票', color: 'geekblue' },
  correction: { text: '修正', color: 'default' },
  void: { text: '作废', color: 'default' },
  expire: { text: '过期', color: 'default' },
}

const ClassSearch = () => {
  const [events, setEvents] = useState<Event[]>([])
  const [selectedEventId, setSelectedEventId] = useState<number>()
  const [classList, setClassList] = useState<ClassItem[]>([])
  const [searchValue, setSearchValue] = useState('')
  const [includeTransactions, setIncludeTransactions] = useState(false)
  const [data, setData] = useState<ParticipantData[]>([])
  const [summary, setSummary] = useState<ClassSummary | null>(null)
  const [totalCount, setTotalCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [classListLoading, setClassListLoading] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 50 })
  const [expandedRowKeys, setExpandedRowKeys] = useState<number[]>([])

  useEffect(() => {
    loadEvents()
  }, [])

  useEffect(() => {
    if (selectedEventId) {
      loadClassList()
    }
  }, [selectedEventId])

  const loadEvents = async () => {
    try {
      const res = await getEvents()
      const eventList = res?.events || []
      setEvents(eventList)
      if (eventList.length > 0) {
        setSelectedEventId(eventList[0].id)
      }
    } catch (err) {
      console.error('Failed to load events:', err)
    }
  }

  const loadClassList = async () => {
    if (!selectedEventId) return
    setClassListLoading(true)
    try {
      const res: any = await request.get('/admin/class-list', {
        params: { event_id: selectedEventId },
      })
      setClassList(res?.classes || [])
    } catch (err) {
      console.error('Failed to load class list:', err)
    } finally {
      setClassListLoading(false)
    }
  }

  const searchByClass = useCallback(async (className?: string) => {
    const query = className || searchValue
    if (!selectedEventId || !query.trim()) return

    setLoading(true)
    try {
      const res: ClassSearchResponse = await request.get('/admin/class-search', {
        params: {
          event_id: selectedEventId,
          class_name: query.trim(),
          include_transactions: includeTransactions,
          txn_limit: 30,
          limit: pagination.pageSize,
          offset: (pagination.current - 1) * pagination.pageSize,
        },
      }) as any
      setData(res.participants || [])
      setTotalCount(res.total_count || 0)
      setSummary(res.summary || null)
      setExpandedRowKeys([])
    } catch (err) {
      console.error('Class search failed:', err)
      setData([])
      setTotalCount(0)
      setSummary(null)
    } finally {
      setLoading(false)
    }
  }, [selectedEventId, searchValue, includeTransactions, pagination])

  const handleSearch = () => {
    setPagination({ ...pagination, current: 1 })
    searchByClass()
  }

  const handleClassSelect = (className: string) => {
    setSearchValue(className)
    setPagination({ ...pagination, current: 1 })
    searchByClass(className)
  }

  const handleTableChange = (pag: any) => {
    setPagination({ current: pag.current, pageSize: pag.pageSize })
  }

  useEffect(() => {
    if (searchValue.trim() && selectedEventId) {
      searchByClass()
    }
  }, [pagination.current, pagination.pageSize])

  const columns: ColumnsType<ParticipantData> = [
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
      width: 100,
      render: (name: string, record) => (
        <Space>
          <span>{name}</span>
          {record.status !== 'active' && (
            <Tag color="red">{record.status}</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '学号',
      dataIndex: 'student_no',
      key: 'student_no',
      width: 100,
      render: (v: string) => v || '-',
    },
    {
      title: '卡号',
      dataIndex: 'card_uid',
      key: 'card_uid',
      width: 120,
      render: (v: string) => <Text code>{v}</Text>,
    },
    {
      title: '余额',
      dataIndex: 'balance',
      key: 'balance',
      width: 100,
      sorter: (a, b) => a.balance - b.balance,
      render: (v: number) => (
        <span style={{ color: v > 0 ? '#52c41a' : v < 0 ? '#ff4d4f' : '#999', fontWeight: 600 }}>
          ¥{v.toFixed(2)}
        </span>
      ),
    },
    {
      title: '已借款',
      dataIndex: 'credit_borrowed',
      key: 'credit_borrowed',
      width: 100,
      render: (v: number) => v > 0 ? <span style={{ color: '#fa8c16' }}>¥{v.toFixed(2)}</span> : '-',
    },
    {
      title: '手续费',
      dataIndex: 'credit_fee_paid',
      key: 'credit_fee_paid',
      width: 90,
      render: (v: number) => v > 0 ? <span style={{ color: '#8c8c8c' }}>¥{v.toFixed(2)}</span> : '-',
    },
    {
      title: '班级',
      dataIndex: 'class_name',
      key: 'class_name',
      width: 120,
      render: (v: string) => v || '-',
    },
  ]

  // 展开行：显示交易流水
  const expandedRowRender = (record: ParticipantData) => {
    if (!record.transactions || record.transactions.length === 0) {
      return <Empty description="暂无交易记录" image={Empty.PRESENTED_IMAGE_SIMPLE} />
    }

    const txnColumns: ColumnsType<TransactionRecord> = [
      {
        title: '时间',
        dataIndex: 'created_at',
        key: 'created_at',
        width: 160,
        render: (v: string) => v ? dayjs(v).format('MM-DD HH:mm:ss') : '-',
      },
      {
        title: '类型',
        dataIndex: 'type',
        key: 'type',
        width: 100,
        render: (type: string) => {
          const info = typeLabels[type] || { text: type, color: 'default' }
          return <Tag color={info.color}>{info.text}</Tag>
        },
      },
      {
        title: '金额',
        dataIndex: 'amount',
        key: 'amount',
        width: 100,
        render: (amount: number, record: TransactionRecord) => {
          const isDebit = ['pay', 'loan_fee', 'stock_buy'].includes(record.type)
          return (
            <span style={{ color: isDebit ? '#ff4d4f' : '#52c41a', fontWeight: 600 }}>
              {isDebit ? '-' : '+'}¥{amount.toFixed(2)}
            </span>
          )
        },
      },
      {
        title: '余额变化',
        key: 'balance_change',
        width: 160,
        render: (_: any, record: TransactionRecord) => (
          <Text type="secondary">
            ¥{record.balance_before.toFixed(2)} → ¥{record.balance_after.toFixed(2)}
          </Text>
        ),
      },
      {
        title: '备注',
        dataIndex: 'remark',
        key: 'remark',
        ellipsis: true,
        render: (v: string) => v || '-',
      },
    ]

    return (
      <Table
        columns={txnColumns}
        dataSource={record.transactions}
        rowKey="id"
        size="small"
        pagination={false}
        style={{ margin: '0 0 0 24px' }}
      />
    )
  }

  return (
    <div>
      <Title level={4}>
        <BookOutlined style={{ marginRight: 8 }} />
        班级搜索
      </Title>

      {/* 搜索区域 */}
      <Card style={{ marginBottom: 16 }}>
        <Space wrap size="middle">
          <Select
            style={{ width: 200 }}
            placeholder="选择活动"
            value={selectedEventId}
            onChange={(val) => {
              setSelectedEventId(val)
              setData([])
              setSummary(null)
            }}
            options={events.map((e) => ({ label: e.name, value: e.id }))}
          />
          <Input
            style={{ width: 240 }}
            placeholder="输入班级名称搜索..."
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onPressEnter={handleSearch}
            prefix={<SearchOutlined />}
            allowClear
          />
          <Switch
            checked={includeTransactions}
            onChange={(checked) => setIncludeTransactions(checked)}
            checkedChildren="含流水"
            unCheckedChildren="不含流水"
          />
          <button
            onClick={handleSearch}
            style={{
              padding: '4px 16px',
              background: '#1677ff',
              color: '#fff',
              border: 'none',
              borderRadius: 6,
              cursor: 'pointer',
            }}
          >
            搜索
          </button>
        </Space>

        {/* 班级快捷选择 */}
        {classList.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <Text type="secondary" style={{ marginRight: 8 }}>快捷选择：</Text>
            <Space wrap size="small">
              {classList.map((cls) => (
                <Tag
                  key={cls.class_name}
                  style={{ cursor: 'pointer' }}
                  color={searchValue === cls.class_name ? 'blue' : undefined}
                  onClick={() => handleClassSelect(cls.class_name)}
                >
                  {cls.class_name} ({cls.participant_count}人)
                </Tag>
              ))}
            </Space>
          </div>
        )}
        {classListLoading && <Spin size="small" style={{ marginLeft: 8 }} />}
      </Card>

      {/* 班级汇总统计 */}
      {summary && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="班级人数"
                value={summary.participant_count}
                prefix={<TeamOutlined />}
                suffix="人"
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="总余额"
                value={summary.total_balance}
                prefix={<WalletOutlined />}
                precision={2}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="总充值"
                value={summary.total_recharged}
                precision={2}
                prefix="¥"
                valueStyle={{ color: '#1677ff' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="总消费"
                value={summary.total_consumed}
                precision={2}
                prefix="¥"
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="总退款"
                value={summary.total_refunded}
                precision={2}
                prefix="¥"
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="总借款"
                value={summary.total_credit_borrowed}
                precision={2}
                prefix="¥"
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 参与者列表 */}
      <Card>
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
            showTotal: (total) => `共 ${total} 人`,
            pageSizeOptions: ['20', '50', '100'],
          }}
          onChange={handleTableChange}
          expandable={
            includeTransactions
              ? {
                  expandedRowRender,
                  expandedRowKeys,
                  onExpandedRowsChange: (keys) => setExpandedRowKeys(keys as number[]),
                  rowExpandable: (record) => (record.transactions?.length || 0) > 0,
                }
              : undefined
          }
          size="middle"
          locale={{ emptyText: <Empty description="请搜索班级名称查看数据" /> }}
        />
      </Card>
    </div>
  )
}

export default ClassSearch
