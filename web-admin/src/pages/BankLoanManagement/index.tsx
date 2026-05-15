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
  Button,
  Modal,
  Descriptions,
  Tabs,
  message,
} from 'antd'
import {
  BankOutlined,
  SearchOutlined,
  ExportOutlined,
  TeamOutlined,
  DollarOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import { getEvents, type Event } from '@/services/event'
import {
  getLoans,
  getCreditDashboard,
  exportLoansCSV,
  markLoanRepaid,
  batchMarkRepaid,
  type LoanRecord,
  type CreditDashboardStats,
} from '@/services/bankCredit'
import request from '@/utils/request'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'

const { Title, Text } = Typography

interface TransactionRecord {
  id: number
  type: string
  amount: number
  balance_before: number
  balance_after: number
  remark: string | null
  created_at: string
}

const BankLoanManagement = () => {
  const [events, setEvents] = useState<Event[]>([])
  const [selectedEventId, setSelectedEventId] = useState<number>()
  const [loans, setLoans] = useState<LoanRecord[]>([])
  const [stats, setStats] = useState<CreditDashboardStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [classFilter, setClassFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [searchText, setSearchText] = useState('')
  const [detailVisible, setDetailVisible] = useState(false)
  const [detailLoan, setDetailLoan] = useState<LoanRecord | null>(null)
  const [detailTransactions, setDetailTransactions] = useState<TransactionRecord[]>([])
  const [detailLoading, setDetailLoading] = useState(false)

  // 批量还款状态
  const [batchRepayVisible, setBatchRepayVisible] = useState(false)
  const [batchRepayClass, setBatchRepayClass] = useState<string>('')
  const [batchRepayRemark, setBatchRepayRemark] = useState('')
  const [batchRepayLoading, setBatchRepayLoading] = useState(false)

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

  const loadData = useCallback(async () => {
    if (!selectedEventId) return
    setLoading(true)
    try {
      const [loansData, statsData] = await Promise.all([
        getLoans(selectedEventId, {
          status: statusFilter || undefined,
          class_name: classFilter || undefined,
          limit: 500,
        }),
        getCreditDashboard(selectedEventId),
      ])
      setLoans(Array.isArray(loansData) ? loansData : [])
      setStats(statsData)
    } catch {
      setLoans([])
      setStats(null)
    } finally {
      setLoading(false)
    }
  }, [selectedEventId, statusFilter, classFilter])

  useEffect(() => {
    loadData()
  }, [loadData])

  // 查看借贷人详情（流水）
  const handleViewDetail = async (record: LoanRecord) => {
    setDetailLoan(record)
    setDetailVisible(true)
    setDetailLoading(true)
    try {
      const res = await request.get<any, any>('/transactions', {
        params: {
          event_id: selectedEventId,
          participant_id: record.participant_id,
          limit: 100,
        },
      })
      setDetailTransactions(res?.transactions || [])
    } catch {
      setDetailTransactions([])
    } finally {
      setDetailLoading(false)
    }
  }

  // 导出
  const handleExport = () => {
    if (!selectedEventId) return
    const token = localStorage.getItem('nfc_wallet_token')
    window.open(`/api/bank-credit/export/${selectedEventId}?token=${token}`, '_blank')
  }

  // 单笔登记还款
  const handleMarkRepaid = (record: LoanRecord) => {
    Modal.confirm({
      title: '确认登记还款',
      content: (
        <div>
          <p>确认将以下贷款标记为已还款？</p>
          <p><strong>姓名：</strong>{record.participant_name}</p>
          <p><strong>班级：</strong>{record.class_name || '-'}</p>
          <p><strong>借款金额：</strong>¥{record.principal_amount_yuan?.toFixed(2)}</p>
          <p style={{ color: '#fa8c16', marginTop: 8 }}>注意：此操作仅标记状态，不会扣除学生余额。</p>
        </div>
      ),
      okText: '确认还款',
      cancelText: '取消',
      onOk: async () => {
        try {
          const res = await markLoanRepaid({
            loan_id: record.id,
            remark: '管理员后台登记还款',
          })
          message.success(res.message)
          loadData()
        } catch (error: any) {
          message.error(error?.response?.data?.detail || '操作失败')
        }
      },
    })
  }

  // 批量按班级登记还款
  const handleBatchRepay = async () => {
    if (!selectedEventId || !batchRepayClass) {
      message.warning('请选择班级')
      return
    }
    setBatchRepayLoading(true)
    try {
      const res = await batchMarkRepaid({
        event_id: selectedEventId,
        class_name: batchRepayClass,
        remark: batchRepayRemark || '管理员批量登记还款',
      })
      message.success(res.message)
      setBatchRepayVisible(false)
      setBatchRepayClass('')
      setBatchRepayRemark('')
      loadData()
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '批量操作失败')
    } finally {
      setBatchRepayLoading(false)
    }
  }

  // 过滤后的数据
  const filteredLoans = loans.filter((loan) => {
    if (searchText) {
      const s = searchText.toLowerCase()
      return (
        (loan.participant_name || '').toLowerCase().includes(s) ||
        (loan.class_name || '').toLowerCase().includes(s) ||
        (loan.card_uid || '').toLowerCase().includes(s)
      )
    }
    return true
  })

  // 获取所有班级列表
  const classNames = [...new Set(loans.map((l) => l.class_name).filter(Boolean))] as string[]

  const statusMap: Record<string, { text: string; color: string }> = {
    active: { text: '未还', color: 'red' },
    repaid: { text: '已还', color: 'green' },
    written_off: { text: '核销', color: 'default' },
  }

  const columns: ColumnsType<LoanRecord> = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: '姓名',
      dataIndex: 'participant_name',
      key: 'participant_name',
      width: 100,
    },
    {
      title: '班级',
      dataIndex: 'class_name',
      key: 'class_name',
      width: 120,
      render: (text: string) => text || '-',
    },
    {
      title: '卡号',
      dataIndex: 'card_uid',
      key: 'card_uid',
      width: 120,
      render: (text: string) => text || '-',
    },
    {
      title: '借款金额',
      dataIndex: 'principal_amount_yuan',
      key: 'principal_amount_yuan',
      width: 100,
      align: 'right',
      render: (val: number) => <Text strong>¥{val?.toFixed(2)}</Text>,
    },
    {
      title: '手续费',
      dataIndex: 'fee_amount_yuan',
      key: 'fee_amount_yuan',
      width: 90,
      align: 'right',
      render: (val: number) => <Text type="warning">¥{val?.toFixed(2)}</Text>,
    },
    {
      title: '实际到账',
      dataIndex: 'disbursed_amount_yuan',
      key: 'disbursed_amount_yuan',
      width: 100,
      align: 'right',
      render: (val: number) => <Text type="success">¥{val?.toFixed(2)}</Text>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => {
        const s = statusMap[status] || { text: status, color: 'default' }
        return <Tag color={s.color}>{s.text}</Tag>
      },
    },
    {
      title: '操作员',
      dataIndex: 'operator_name',
      key: 'operator_name',
      width: 90,
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 140,
      render: (t: string) => t ? dayjs(t).format('MM-DD HH:mm') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 140,
      fixed: 'right',
      render: (_: any, record: LoanRecord) => (
        <Space size="small">
          <Button type="link" size="small" icon={<FileTextOutlined />} onClick={() => handleViewDetail(record)}>
            详情
          </Button>
          {record.status === 'active' && (
            <Button type="link" size="small" icon={<CheckCircleOutlined />} style={{ color: '#52c41a' }} onClick={() => handleMarkRepaid(record)}>
              还款
            </Button>
          )}
        </Space>
      ),
    },
  ]

  const txnColumns: ColumnsType<TransactionRecord> = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type: string) => {
        const typeMap: Record<string, { text: string; color: string }> = {
          recharge: { text: '充值', color: 'green' },
          payment: { text: '消费', color: 'blue' },
          loan_issue: { text: '借款', color: 'purple' },
          loan_fee: { text: '手续费', color: 'orange' },
          loan_repay: { text: '还款', color: 'cyan' },
          refund: { text: '退款', color: 'red' },
          correction: { text: '调整', color: 'default' },
        }
        const t = typeMap[type] || { text: type, color: 'default' }
        return <Tag color={t.color}>{t.text}</Tag>
      },
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 90,
      align: 'right',
      render: (val: number) => `¥${val?.toFixed(2)}`,
    },
    {
      title: '余额变动',
      key: 'balance_change',
      width: 150,
      render: (_: any, record: TransactionRecord) =>
        `¥${record.balance_before?.toFixed(2)} → ¥${record.balance_after?.toFixed(2)}`,
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
      ellipsis: true,
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 140,
      render: (t: string) => t ? dayjs(t).format('MM-DD HH:mm:ss') : '-',
    },
  ]

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>
        <BankOutlined /> 银行借贷管理
      </Title>

      {/* 统计卡片 */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={4}>
            <Card size="small">
              <Statistic title="总借款笔数" value={stats.total_loans} prefix={<FileTextOutlined />} />
            </Card>
          </Col>
          <Col span={5}>
            <Card size="small">
              <Statistic
                title="总借款金额"
                value={stats.total_principal_yuan}
                precision={2}
                prefix="¥"
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
          <Col span={5}>
            <Card size="small">
              <Statistic
                title="总手续费"
                value={stats.total_fee_yuan}
                precision={2}
                prefix="¥"
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
          <Col span={5}>
            <Card size="small">
              <Statistic
                title="实际放款"
                value={stats.total_disbursed_yuan}
                precision={2}
                prefix="¥"
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={5}>
            <Card size="small">
              <Statistic
                title="借款人数"
                value={stats.total_borrowers}
                suffix={`/ ${stats.total_participants}`}
                prefix={<TeamOutlined />}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 筛选栏 */}
      <Space style={{ marginBottom: 16 }} wrap>
        <Select
          style={{ width: 200 }}
          placeholder="选择活动"
          value={selectedEventId}
          onChange={(v) => { setSelectedEventId(v); setClassFilter(''); }}
          options={events.map((e) => ({ label: e.name, value: e.id }))}
        />
        <Select
          style={{ width: 150 }}
          placeholder="按班级筛选"
          value={classFilter || undefined}
          onChange={(v) => setClassFilter(v || '')}
          allowClear
          options={classNames.map((c) => ({ label: c, value: c }))}
        />
        <Select
          style={{ width: 120 }}
          placeholder="状态"
          value={statusFilter || undefined}
          onChange={(v) => setStatusFilter(v || '')}
          allowClear
          options={[
            { label: '未还', value: 'active' },
            { label: '已还', value: 'repaid' },
            { label: '核销', value: 'written_off' },
          ]}
        />
        <Input.Search
          style={{ width: 220 }}
          placeholder="搜索姓名/班级/卡号"
          prefix={<SearchOutlined />}
          allowClear
          onSearch={(v) => setSearchText(v)}
          onChange={(e) => { if (!e.target.value) setSearchText('') }}
        />
        <Button icon={<ExportOutlined />} onClick={handleExport}>
          导出 CSV
        </Button>
        <Button
          type="primary"
          icon={<CheckCircleOutlined />}
          onClick={() => setBatchRepayVisible(true)}
          disabled={!selectedEventId}
          style={{ background: '#52c41a', borderColor: '#52c41a' }}
        >
          按班级批量还款
        </Button>
      </Space>

      {/* 数据表格 */}
      <Table
        columns={columns}
        dataSource={filteredLoans}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (t) => `共 ${t} 条` }}
        scroll={{ x: 1200 }}
        size="small"
      />

      {/* 借贷人详情弹窗 */}
      <Modal
        title="借贷人详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={800}
      >
        {detailLoan && (
          <>
            <Descriptions bordered size="small" column={2} style={{ marginBottom: 16 }}>
              <Descriptions.Item label="姓名">{detailLoan.participant_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="班级">{detailLoan.class_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="卡号">{detailLoan.card_uid || '-'}</Descriptions.Item>
              <Descriptions.Item label="学号">{detailLoan.student_no || '-'}</Descriptions.Item>
              <Descriptions.Item label="借款金额">
                <Text strong style={{ color: '#cf1322' }}>¥{detailLoan.principal_amount_yuan?.toFixed(2)}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="手续费">
                ¥{detailLoan.fee_amount_yuan?.toFixed(2)} ({(detailLoan.fee_rate * 100).toFixed(1)}%)
              </Descriptions.Item>
              <Descriptions.Item label="实际到账">
                <Text type="success">¥{detailLoan.disbursed_amount_yuan?.toFixed(2)}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={statusMap[detailLoan.status]?.color}>
                  {statusMap[detailLoan.status]?.text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="操作员">{detailLoan.operator_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="借款时间">
                {detailLoan.created_at ? dayjs(detailLoan.created_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="备注" span={2}>{detailLoan.remark || '无'}</Descriptions.Item>
            </Descriptions>

            <Title level={5}>交易流水</Title>
            <Table
              columns={txnColumns}
              dataSource={detailTransactions}
              rowKey="id"
              loading={detailLoading}
              pagination={{ pageSize: 10 }}
              size="small"
              scroll={{ x: 700 }}
            />
          </>
        )}
      </Modal>
      {/* 批量还款弹窗 */}
      <Modal
        title={
          <span>
            <CheckCircleOutlined style={{ marginRight: 8, color: '#52c41a' }} />
            按班级批量登记还款
          </span>
        }
        open={batchRepayVisible}
        onOk={handleBatchRepay}
        onCancel={() => { setBatchRepayVisible(false); setBatchRepayClass(''); setBatchRepayRemark('') }}
        confirmLoading={batchRepayLoading}
        okText="确认批量还款"
        cancelText="取消"
      >
        <div style={{ marginBottom: 16 }}>
          <p style={{ color: '#fa8c16' }}>
            此操作将把选定班级下所有「未还」状态的贷款标记为「已还」。
            <br />仅标记状态，不会扣除学生余额。适用于学生线下统一还款的场景。
          </p>
        </div>
        <div style={{ marginBottom: 12 }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 'bold' }}>选择班级：</label>
          <Select
            style={{ width: '100%' }}
            placeholder="选择要批量还款的班级"
            value={batchRepayClass || undefined}
            onChange={setBatchRepayClass}
            options={classNames.map((c) => ({ label: c, value: c }))}
          />
        </div>
        {batchRepayClass && (
          <div style={{ marginBottom: 12, padding: 8, background: '#f6ffed', borderRadius: 4 }}>
            <Text>
              该班级未还贷款：
              <Text strong style={{ color: '#cf1322' }}>
                {loans.filter((l) => l.class_name === batchRepayClass && l.status === 'active').length} 笔
              </Text>
              ，合计金额：
              <Text strong style={{ color: '#cf1322' }}>
                ¥{loans
                  .filter((l) => l.class_name === batchRepayClass && l.status === 'active')
                  .reduce((sum, l) => sum + (l.principal_amount_yuan || 0), 0)
                  .toFixed(2)}
              </Text>
            </Text>
          </div>
        )}
        <div>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 'bold' }}>备注（可选）：</label>
          <Input.TextArea
            rows={2}
            placeholder="如：全班统一现金还款"
            value={batchRepayRemark}
            onChange={(e) => setBatchRepayRemark(e.target.value)}
          />
        </div>
      </Modal>
    </div>
  )
}

export default BankLoanManagement
