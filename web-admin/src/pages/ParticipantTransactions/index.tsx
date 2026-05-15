import { useState } from 'react'
import { Table, Space, Select, DatePicker, Button, Tag, Card, Input, Descriptions, message, List, Radio } from 'antd'
import {
  SearchOutlined,
  ReloadOutlined,
  UserOutlined,
} from '@ant-design/icons'
import {
  getTransactions,
  type Transaction,
  type TransactionListResponse,
} from '@/services/transaction'
import dayjs, { Dayjs } from 'dayjs'

const { RangePicker } = DatePicker

type SearchMode = 'card_uid' | 'name'

const ParticipantTransactions = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [searchMode, setSearchMode] = useState<SearchMode>('card_uid')
  const [cardUidValue, setCardUidValue] = useState('')
  const [nameValue, setNameValue] = useState('')
  const [classValue, setClassValue] = useState('')
  const [selectedType, setSelectedType] = useState<string>()
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 50 })
  const [participantInfo, setParticipantInfo] = useState<{
    id: number
    name: string
    card_uid: string
    class_name?: string
    student_no?: string
  } | null>(null)
  const [multipleMatches, setMultipleMatches] = useState<Array<{
    id: number
    name: string
    card_uid: string
    class_name?: string
    student_no?: string
  }>>([])

  const loadTransactions = async (overrideParticipantId?: number) => {
    // 构建查询参数
    const params: any = {
      limit: pagination.pageSize,
      offset: (pagination.current - 1) * pagination.pageSize,
    }

    if (overrideParticipantId) {
      params.participant_id = overrideParticipantId
    } else if (searchMode === 'card_uid') {
      const uid = cardUidValue.trim()
      if (!uid) {
        message.warning('请输入卡号')
        return
      }
      params.card_uid = uid
    } else {
      const name = nameValue.trim()
      if (!name) {
        message.warning('请输入学生姓名')
        return
      }
      params.participant_name = name
      if (classValue.trim()) {
        params.class_name = classValue.trim()
      }
    }

    if (selectedType) {
      params.type = selectedType
    }

    if (dateRange) {
      params.start_date = dateRange[0].format('YYYY-MM-DD')
      params.end_date = dateRange[1].format('YYYY-MM-DD')
    }

    setLoading(true)
    try {
      const data: TransactionListResponse = await getTransactions(params)

      // 如果返回了多个匹配的参与者
      if (data?.multiple_matches && data.multiple_matches.length > 0) {
        setMultipleMatches(data.multiple_matches)
        setTransactions([])
        setTotalCount(0)
        setParticipantInfo(null)
        message.info(`找到 ${data.multiple_matches.length} 个匹配的参与者，请选择`)
        return
      }

      setMultipleMatches([])
      setTransactions(data?.transactions || [])
      setTotalCount(data?.total_count || 0)
      if (data?.participant) {
        setParticipantInfo(data.participant)
      }
    } catch (error) {
      setTransactions([])
      setTotalCount(0)
      message.error('查询失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    setPagination({ current: 1, pageSize: 50 })
    setMultipleMatches([])
    loadTransactions()
  }

  const handleSelectParticipant = (participant: typeof multipleMatches[0]) => {
    setParticipantInfo(participant)
    setMultipleMatches([])
    setPagination({ current: 1, pageSize: 50 })
    loadTransactions(participant.id)
  }

  const handleReset = () => {
    setCardUidValue('')
    setNameValue('')
    setClassValue('')
    setSelectedType(undefined)
    setDateRange(null)
    setPagination({ current: 1, pageSize: 50 })
    setTransactions([])
    setTotalCount(0)
    setParticipantInfo(null)
    setMultipleMatches([])
  }

  // 统计数据
  const totalIncome = transactions
    .filter((t) => t.type === 'recharge')
    .reduce((sum, t) => sum + t.amount, 0)

  const totalSpend = transactions
    .filter((t) => ['pay', 'cash_payment', 'stock_buy', 'loan_fee'].includes(t.type))
    .reduce((sum, t) => sum + t.amount, 0)

  const totalRefund = transactions
    .filter((t) => t.type === 'refund')
    .reduce((sum, t) => sum + t.amount, 0)

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
        const isDebit = ['pay', 'cash_payment', 'stock_buy', 'loan_fee'].includes(record.type)
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
      title: '余额变动',
      key: 'balance_change',
      width: 180,
      render: (_: any, record: Transaction) => (
        <span>
          ¥{record.balance_before.toFixed(2)} → ¥{record.balance_after.toFixed(2)}
        </span>
      ),
    },
    {
      title: '商铺',
      dataIndex: 'booth_name',
      key: 'booth_name',
      width: 130,
      render: (name: string | null, record: Transaction) => {
        if (name) return name
        if (record.booth_id) return `商铺#${record.booth_id}`
        return '-'
      },
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
      width: 200,
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
        <UserOutlined style={{ marginRight: 8 }} />
        用户流水查询
      </h2>

      {/* 搜索模式切换 */}
      <Space style={{ marginBottom: 12 }}>
        <Radio.Group
          value={searchMode}
          onChange={(e) => {
            setSearchMode(e.target.value)
            setMultipleMatches([])
          }}
          optionType="button"
          buttonStyle="solid"
        >
          <Radio.Button value="card_uid">按卡号查询</Radio.Button>
          <Radio.Button value="name">按姓名班级查询</Radio.Button>
        </Radio.Group>
      </Space>

      {/* 搜索区 */}
      <Space style={{ marginBottom: 16 }} wrap>
        {searchMode === 'card_uid' ? (
          <Input
            style={{ width: 240 }}
            placeholder="输入卡号 (card_uid)"
            value={cardUidValue}
            onChange={(e) => setCardUidValue(e.target.value)}
            onPressEnter={handleSearch}
            allowClear
          />
        ) : (
          <>
            <Input
              style={{ width: 150 }}
              placeholder="学生姓名"
              value={nameValue}
              onChange={(e) => setNameValue(e.target.value)}
              onPressEnter={handleSearch}
              allowClear
            />
            <Input
              style={{ width: 150 }}
              placeholder="班级（可选）"
              value={classValue}
              onChange={(e) => setClassValue(e.target.value)}
              onPressEnter={handleSearch}
              allowClear
            />
          </>
        )}
        <Button icon={<SearchOutlined />} type="primary" onClick={handleSearch}>
          查询
        </Button>
        <Select
          style={{ width: 150 }}
          placeholder="交易类型"
          value={selectedType}
          onChange={(value) => {
            setSelectedType(value)
            if (participantInfo) {
              setPagination({ current: 1, pageSize: 50 })
            }
          }}
          allowClear
        >
          <Select.Option value="pay">支付</Select.Option>
          <Select.Option value="recharge">充值</Select.Option>
          <Select.Option value="refund">退款</Select.Option>
          <Select.Option value="cash_payment">现金收款</Select.Option>
          <Select.Option value="stock_buy">股票买入</Select.Option>
          <Select.Option value="stock_sell">股票卖出</Select.Option>
          <Select.Option value="loan_issue">垫资发放</Select.Option>
          <Select.Option value="loan_fee">手续费</Select.Option>
        </Select>
        <RangePicker
          value={dateRange}
          onChange={(dates) => {
            setDateRange(dates as [Dayjs, Dayjs] | null)
            if (participantInfo) {
              setPagination({ current: 1, pageSize: 50 })
            }
          }}
        />
        <Button icon={<ReloadOutlined />} onClick={handleReset}>
          重置
        </Button>
      </Space>

      {/* 多个匹配结果选择 */}
      {multipleMatches.length > 0 && (
        <Card size="small" title="找到多个匹配的参与者，请选择：" style={{ marginBottom: 16 }}>
          <List
            size="small"
            dataSource={multipleMatches}
            renderItem={(item) => (
              <List.Item
                actions={[
                  <Button
                    type="link"
                    size="small"
                    onClick={() => handleSelectParticipant(item)}
                  >
                    查看流水
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  title={`${item.name} - ${item.class_name || '未知班级'}`}
                  description={`卡号: ${item.card_uid}${item.student_no ? ` | 学号: ${item.student_no}` : ''}`}
                />
              </List.Item>
            )}
          />
        </Card>
      )}

      {/* 用户信息卡片 */}
      {participantInfo && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Descriptions column={5} size="small">
            <Descriptions.Item label="姓名">{participantInfo.name || '-'}</Descriptions.Item>
            <Descriptions.Item label="卡号">{participantInfo.card_uid}</Descriptions.Item>
            <Descriptions.Item label="班级">{participantInfo.class_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="学号">{participantInfo.student_no || '-'}</Descriptions.Item>
            <Descriptions.Item label="统计">
              <Space>
                <Tag color="green">充值 ¥{totalIncome.toFixed(2)}</Tag>
                <Tag color="red">消费 ¥{totalSpend.toFixed(2)}</Tag>
                <Tag color="orange">退款 ¥{totalRefund.toFixed(2)}</Tag>
              </Space>
            </Descriptions.Item>
          </Descriptions>
        </Card>
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
            if (participantInfo) {
              loadTransactions(participantInfo.id)
            }
          },
        }}
        scroll={{ x: 1100 }}
        locale={{ emptyText: participantInfo ? '暂无交易记录' : '请输入查询条件搜索用户流水' }}
      />
    </div>
  )
}

export default ParticipantTransactions
