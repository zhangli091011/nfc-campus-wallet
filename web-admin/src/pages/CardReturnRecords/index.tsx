import { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Input,
  Select,
  Tag,
  Space,
  Statistic,
  Row,
  Col,
  Modal,
  Descriptions,
  Timeline,
  Typography,
  message,
  Tooltip,
  Badge,
} from 'antd'
import {
  SearchOutlined,
  CreditCardOutlined,
  UserOutlined,
  DollarOutlined,
  HistoryOutlined,
  BankOutlined,
} from '@ant-design/icons'
import {
  getCardReturnRecords,
  getCardReturnDetail,
  type CardReturnRecord,
  type CardReturnDetail,
  type TransactionItem,
  type LoanItem,
} from '@/services/cardReturn'
import dayjs from 'dayjs'

const { Text, Title } = Typography

const txnTypeMap: Record<string, { label: string; color: string }> = {
  recharge: { label: '充值', color: 'green' },
  pay: { label: '消费', color: 'red' },
  refund: { label: '退款', color: 'orange' },
  correction: { label: '更正', color: 'purple' },
  loan_issue: { label: '贷款发放', color: 'blue' },
  loan_fee: { label: '贷款手续费', color: 'volcano' },
  stock_buy: { label: '购买股票', color: 'cyan' },
}

const loanStatusMap: Record<string, { label: string; color: string }> = {
  active: { label: '活跃', color: 'processing' },
  repaid: { label: '已还清', color: 'success' },
  card_returned: { label: '退卡未清', color: 'warning' },
  written_off: { label: '已核销', color: 'default' },
}

const CardReturnRecords = () => {
  const [records, setRecords] = useState<CardReturnRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [totalCount, setTotalCount] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(20)
  const [searchText, setSearchText] = useState('')
  const [eventId, setEventId] = useState<number>(1)

  // 明细弹窗
  const [detailVisible, setDetailVisible] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detail, setDetail] = useState<CardReturnDetail | null>(null)
  const [selectedRecord, setSelectedRecord] = useState<CardReturnRecord | null>(null)

  useEffect(() => {
    loadRecords()
  }, [currentPage, eventId])

  const loadRecords = async () => {
    setLoading(true)
    try {
      const data = await getCardReturnRecords({
        event_id: eventId,
        search: searchText || undefined,
        limit: pageSize,
        offset: (currentPage - 1) * pageSize,
      })
      setRecords(data.records || [])
      setTotalCount(data.total_count || 0)
    } catch {
      message.error('加载退卡记录失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    setCurrentPage(1)
    loadRecords()
  }

  const handleViewDetail = async (record: CardReturnRecord) => {
    setSelectedRecord(record)
    setDetailVisible(true)
    setDetailLoading(true)
    try {
      const data = await getCardReturnDetail(record.id, eventId)
      setDetail(data)
    } catch {
      message.error('加载明细失败')
    } finally {
      setDetailLoading(false)
    }
  }

  // 统计数据
  const totalRefunded = records.reduce((sum, r) => sum + r.refunded_amount, 0)
  const totalWithDebt = records.filter(r => r.loan_remaining_debt > 0).length

  const columns = [
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
      width: 100,
      render: (name: string) => <Text strong>{name}</Text>,
    },
    {
      title: '班级',
      dataIndex: 'class_name',
      key: 'class_name',
      width: 100,
      render: (v: string | null) => v || '-',
    },
    {
      title: '学号',
      dataIndex: 'student_no',
      key: 'student_no',
      width: 100,
      render: (v: string | null) => v || '-',
    },
    {
      title: '原卡号',
      dataIndex: 'original_card_uid',
      key: 'original_card_uid',
      width: 130,
      render: (uid: string) => (
        <Tooltip title={uid}>
          <Tag icon={<CreditCardOutlined />} color="blue">
            {uid.length > 10 ? uid.slice(0, 10) + '...' : uid}
          </Tag>
        </Tooltip>
      ),
    },
    {
      title: '退卡时余额',
      dataIndex: 'balance_at_return',
      key: 'balance_at_return',
      width: 110,
      align: 'right' as const,
      render: (v: number) => <Text>¥{v.toFixed(2)}</Text>,
    },
    {
      title: '退款金额',
      dataIndex: 'refunded_amount',
      key: 'refunded_amount',
      width: 110,
      align: 'right' as const,
      render: (v: number) => (
        <Text type={v > 0 ? 'success' : undefined}>¥{v.toFixed(2)}</Text>
      ),
    },
    {
      title: '未清贷款',
      key: 'loan_debt',
      width: 110,
      align: 'right' as const,
      render: (_: any, record: CardReturnRecord) =>
        record.loan_remaining_debt > 0 ? (
          <Text type="danger">¥{record.loan_remaining_debt.toFixed(2)}</Text>
        ) : (
          <Text type="secondary">无</Text>
        ),
    },
    {
      title: '操作员',
      dataIndex: 'operator_name',
      key: 'operator_name',
      width: 90,
      render: (v: string | null) => v || '-',
    },
    {
      title: '退卡时间',
      dataIndex: 'return_time',
      key: 'return_time',
      width: 160,
      render: (v: string | null) =>
        v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: CardReturnRecord) => (
        <a onClick={() => handleViewDetail(record)}>查看明细</a>
      ),
    },
  ]

  // 流水表格列
  const txnColumns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (v: string | null) =>
        v ? dayjs(v).format('MM-DD HH:mm:ss') : '-',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type: string) => {
        const info = txnTypeMap[type] || { label: type, color: 'default' }
        return <Tag color={info.color}>{info.label}</Tag>
      },
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 90,
      align: 'right' as const,
      render: (v: number) => `¥${v.toFixed(2)}`,
    },
    {
      title: '交易前余额',
      dataIndex: 'balance_before',
      key: 'balance_before',
      width: 100,
      align: 'right' as const,
      render: (v: number) => `¥${v.toFixed(2)}`,
    },
    {
      title: '交易后余额',
      dataIndex: 'balance_after',
      key: 'balance_after',
      width: 100,
      align: 'right' as const,
      render: (v: number) => `¥${v.toFixed(2)}`,
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
      ellipsis: true,
      render: (v: string | null) => v || '-',
    },
  ]

  // 贷款表格列
  const loanColumns = [
    {
      title: '贷款时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (v: string | null) =>
        v ? dayjs(v).format('MM-DD HH:mm:ss') : '-',
    },
    {
      title: '本金',
      dataIndex: 'principal_amount',
      key: 'principal_amount',
      width: 90,
      align: 'right' as const,
      render: (v: number) => `¥${v.toFixed(2)}`,
    },
    {
      title: '手续费',
      dataIndex: 'fee_amount',
      key: 'fee_amount',
      width: 90,
      align: 'right' as const,
      render: (v: number) => `¥${v.toFixed(2)}`,
    },
    {
      title: '实际到账',
      dataIndex: 'disbursed_amount',
      key: 'disbursed_amount',
      width: 90,
      align: 'right' as const,
      render: (v: number) => `¥${v.toFixed(2)}`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const info = loanStatusMap[status] || { label: status, color: 'default' }
        return <Badge status={info.color as any} text={info.label} />
      },
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
      ellipsis: true,
      render: (v: string | null) => v || '-',
    },
  ]

  return (
    <div>
      <Card title="退卡记录" style={{ marginBottom: 16 }}>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Statistic
              title="退卡总数"
              value={totalCount}
              prefix={<CreditCardOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="退款总额"
              value={totalRefunded}
              precision={2}
              prefix={<DollarOutlined />}
              suffix="元"
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="有未清贷款"
              value={totalWithDebt}
              prefix={<BankOutlined />}
              valueStyle={{ color: totalWithDebt > 0 ? '#cf1322' : undefined }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="当前页显示"
              value={records.length}
              suffix={`/ ${totalCount}`}
            />
          </Col>
        </Row>

        <Space style={{ marginBottom: 16 }}>
          <Select
            value={eventId}
            onChange={(v) => { setEventId(v); setCurrentPage(1) }}
            style={{ width: 120 }}
            options={[
              { value: 1, label: '活动 1' },
              { value: 2, label: '活动 2' },
              { value: 3, label: '活动 3' },
            ]}
          />
          <Input
            placeholder="搜索姓名/卡号/学号"
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: 220 }}
            allowClear
          />
        </Space>

        <Table
          columns={columns}
          dataSource={records}
          rowKey="id"
          loading={loading}
          pagination={{
            current: currentPage,
            pageSize,
            total: totalCount,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page) => setCurrentPage(page),
          }}
          scroll={{ x: 1100 }}
          size="middle"
        />
      </Card>

      {/* 明细弹窗 */}
      <Modal
        title={
          <Space>
            <UserOutlined />
            <span>退卡明细 - {selectedRecord?.name}</span>
            <Tag color="blue">{selectedRecord?.original_card_uid}</Tag>
          </Space>
        }
        open={detailVisible}
        onCancel={() => { setDetailVisible(false); setDetail(null) }}
        footer={null}
        width={900}
        destroyOnClose
      >
        {detailLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>加载中...</div>
        ) : detail ? (
          <div>
            {/* 基本信息 */}
            <Descriptions
              bordered
              size="small"
              column={3}
              style={{ marginBottom: 16 }}
            >
              <Descriptions.Item label="姓名">
                {detail.participant.name}
              </Descriptions.Item>
              <Descriptions.Item label="班级">
                {detail.participant.class_name || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="学号">
                {detail.participant.student_no || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="原卡号">
                <Tag color="blue">{detail.participant.original_card_uid}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color="red">已退卡</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="注册时间">
                {detail.participant.created_at
                  ? dayjs(detail.participant.created_at).format('YYYY-MM-DD HH:mm')
                  : '-'}
              </Descriptions.Item>
              {detail.account && (
                <>
                  <Descriptions.Item label="当前余额">
                    ¥{detail.account.balance.toFixed(2)}
                  </Descriptions.Item>
                  <Descriptions.Item label="累计借贷">
                    ¥{detail.account.credit_borrowed.toFixed(2)}
                  </Descriptions.Item>
                  <Descriptions.Item label="累计手续费">
                    ¥{detail.account.credit_fee_paid.toFixed(2)}
                  </Descriptions.Item>
                </>
              )}
            </Descriptions>

            {/* 贷款记录 */}
            {detail.loans.length > 0 && (
              <Card
                title={<><BankOutlined /> 贷款记录 ({detail.loan_count})</>}
                size="small"
                style={{ marginBottom: 16 }}
              >
                <Table
                  columns={loanColumns}
                  dataSource={detail.loans}
                  rowKey="id"
                  pagination={false}
                  size="small"
                  scroll={{ x: 600 }}
                />
              </Card>
            )}

            {/* 交易流水 */}
            <Card
              title={<><HistoryOutlined /> 交易流水 ({detail.transaction_count})</>}
              size="small"
            >
              <Table
                columns={txnColumns}
                dataSource={detail.transactions}
                rowKey="id"
                pagination={{ pageSize: 10, size: 'small' }}
                size="small"
                scroll={{ x: 700 }}
              />
            </Card>
          </div>
        ) : null}
      </Modal>
    </div>
  )
}

export default CardReturnRecords
