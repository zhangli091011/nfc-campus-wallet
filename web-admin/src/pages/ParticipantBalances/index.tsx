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
  Form,
  InputNumber,
  message,
} from 'antd'
import {
  WalletOutlined,
  TeamOutlined,
  SearchOutlined,
  PlusOutlined,
  MinusOutlined,
  BankOutlined,
  RollbackOutlined,
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
  const [adjustModalVisible, setAdjustModalVisible] = useState(false)
  const [loanModalVisible, setLoanModalVisible] = useState(false)
  const [operatingParticipant, setOperatingParticipant] = useState<ParticipantBalance | null>(null)
  const [adjustForm] = Form.useForm()
  const [loanForm] = Form.useForm()

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

  // 充值/扣款操作
  const handleAdjust = (record: ParticipantBalance, type: 'recharge' | 'deduct') => {
    setOperatingParticipant(record)
    adjustForm.resetFields()
    adjustForm.setFieldsValue({ type })
    setAdjustModalVisible(true)
  }

  const handleAdjustSubmit = async () => {
    if (!operatingParticipant || !selectedEventId) return
    try {
      const values = await adjustForm.validateFields()
      const amount = values.type === 'deduct' ? -Math.abs(values.amount) : Math.abs(values.amount)
      await request.post('/admin/participants/adjust-balance', {
        event_id: selectedEventId,
        participant_id: operatingParticipant.id,
        amount,
        remark: values.remark || '',
      })
      message.success(values.type === 'deduct' ? '扣款成功' : '充值成功')
      setAdjustModalVisible(false)
      loadBalances()
    } catch (error: any) {
      message.error(error?.response?.data?.message || '操作失败')
    }
  }

  // 发放贷款操作
  const handleLoan = (record: ParticipantBalance) => {
    setOperatingParticipant(record)
    loanForm.resetFields()
    loanForm.setFieldsValue({ fee_rate: 5 })
    setLoanModalVisible(true)
  }

  const handleLoanSubmit = async () => {
    if (!operatingParticipant || !selectedEventId) return
    try {
      const values = await loanForm.validateFields()
      const res = await request.post<any, any>('/admin/participants/issue-loan', {
        event_id: selectedEventId,
        participant_id: operatingParticipant.id,
        amount: values.amount,
        fee_rate: values.fee_rate / 100,
        remark: values.remark || '',
      })
      message.success(`贷款发放成功，实际到账 ¥${res.actual_grant?.toFixed(2)}`)
      setLoanModalVisible(false)
      loadBalances()
    } catch (error: any) {
      message.error(error?.response?.data?.message || '贷款发放失败')
    }
  }

  // 退卡操作
  const handleReturnCard = (record: ParticipantBalance) => {
    Modal.confirm({
      title: '退卡确认',
      width: 480,
      content: (
        <div>
          <p><strong>参与者：</strong>{record.name} ({record.card_uid})</p>
          <p><strong>当前余额：</strong>¥{record.balance.toFixed(2)}</p>
          {record.credit_borrowed > 0 && (
            <p style={{ color: '#ff4d4f' }}>
              <strong>⚠️ 借款记录：</strong>¥{record.credit_borrowed.toFixed(2)}
            </p>
          )}
          <p style={{ marginTop: 12 }}>退卡将：</p>
          <ul>
            <li>退还卡内剩余余额</li>
            <li>解除卡片与该参与者的绑定</li>
            <li>保留所有交易流水记录</li>
            <li>卡片可重新分配给其他人</li>
          </ul>
          {record.credit_borrowed > 0 && (
            <p style={{ color: '#ff4d4f', fontWeight: 'bold' }}>
              如有未清贷款，系统将拒绝退卡！
            </p>
          )}
        </div>
      ),
      okText: '确认退卡',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        if (!selectedEventId) return
        try {
          const res = await request.post<any, any>('/admin/participants/return-card', {
            event_id: selectedEventId,
            participant_id: record.id,
            refund_balance: true,
            remark: '管理员退卡',
          })
          message.success(`退卡成功，已退还 ¥${res.balance_refunded?.toFixed(2) || '0.00'}`)
          loadBalances()
        } catch (error: any) {
          const errMsg = error?.response?.data?.message || '退卡失败'
          message.error(errMsg)
        }
      },
    })
  }

  // 登记还款操作
  const handleRepay = (record: ParticipantBalance) => {
    Modal.confirm({
      title: '登记还款',
      width: 450,
      content: (
        <div>
          <p><strong>参与者：</strong>{record.name} ({record.card_uid})</p>
          <p><strong>当前余额：</strong>¥{record.balance.toFixed(2)}</p>
          <p><strong>借款总额：</strong>¥{record.credit_borrowed.toFixed(2)}</p>
          <p style={{ marginTop: 12, color: '#13c2c2' }}>
            将从余额中扣除全部借款金额作为还款。
          </p>
        </div>
      ),
      okText: '确认全额还款',
      cancelText: '取消',
      onOk: async () => {
        if (!selectedEventId) return
        const repayAmount = Math.min(record.balance, record.credit_borrowed)
        if (repayAmount <= 0) {
          message.warning('余额不足或无借款')
          return
        }
        try {
          const res = await request.post<any, any>('/bank/repay_loan', {
            event_id: selectedEventId,
            card_uid: record.card_uid,
            amount: repayAmount,
            remark: '管理员后台登记还款',
          })
          message.success(res.message || `还款成功 ¥${repayAmount.toFixed(2)}`)
          loadBalances()
        } catch (error: any) {
          message.error(error?.response?.data?.detail || '还款失败')
        }
      },
    })
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
    {
      title: '操作',
      key: 'action',
      width: 340,
      fixed: 'right',
      render: (_: any, record: ParticipantBalance) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<PlusOutlined />}
            onClick={() => handleAdjust(record, 'recharge')}
          >
            充值
          </Button>
          <Button
            type="link"
            size="small"
            danger
            icon={<MinusOutlined />}
            onClick={() => handleAdjust(record, 'deduct')}
          >
            扣款
          </Button>
          <Button
            type="link"
            size="small"
            icon={<BankOutlined />}
            style={{ color: '#722ed1' }}
            onClick={() => handleLoan(record)}
          >
            贷款
          </Button>
          {record.credit_borrowed > 0 && (
            <Button
              type="link"
              size="small"
              style={{ color: '#13c2c2' }}
              onClick={() => handleRepay(record)}
            >
              还款
            </Button>
          )}
          <Button
            type="link"
            size="small"
            danger
            icon={<RollbackOutlined />}
            onClick={() => handleReturnCard(record)}
          >
            退卡
          </Button>
        </Space>
      ),
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
        scroll={{ x: 1200 }}
      />

      {/* 充值/扣款弹窗 */}
      <Modal
        title={adjustForm.getFieldValue('type') === 'deduct' ? '扣款' : '充值'}
        open={adjustModalVisible}
        onOk={handleAdjustSubmit}
        onCancel={() => setAdjustModalVisible(false)}
        okText="确认"
        width={480}
      >
        <Form form={adjustForm} layout="vertical">
          <Form.Item label="参与者">
            <Input value={`${operatingParticipant?.name || ''} (${operatingParticipant?.card_uid || ''})`} disabled />
          </Form.Item>
          <Form.Item name="type" hidden>
            <Input />
          </Form.Item>
          <Form.Item
            name="amount"
            label="金额（元）"
            rules={[{ required: true, message: '请输入金额' }]}
          >
            <InputNumber min={0.01} precision={2} style={{ width: '100%' }} placeholder="请输入金额" />
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={2} placeholder="操作原因说明（可选）" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 发放贷款弹窗 */}
      <Modal
        title="发放贷款"
        open={loanModalVisible}
        onOk={handleLoanSubmit}
        onCancel={() => setLoanModalVisible(false)}
        okText="确认发放"
        width={520}
      >
        <Form form={loanForm} layout="vertical">
          <Form.Item label="参与者">
            <Input value={`${operatingParticipant?.name || ''} (${operatingParticipant?.card_uid || ''})`} disabled />
          </Form.Item>
          <Form.Item
            name="amount"
            label="贷款金额（元）"
            rules={[{ required: true, message: '请输入贷款金额' }]}
          >
            <InputNumber min={1} precision={2} style={{ width: '100%' }} placeholder="名义借款金额" />
          </Form.Item>
          <Form.Item
            name="fee_rate"
            label="手续费率（%）"
            rules={[{ required: true, message: '请输入手续费率' }]}
          >
            <InputNumber min={0} max={100} precision={1} style={{ width: '100%' }} placeholder="默认5%" />
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={2} placeholder="贷款用途说明（可选）" />
          </Form.Item>
          <Form.Item>
            <Card size="small" style={{ background: '#f6ffed' }}>
              <Typography.Text type="secondary">
                实际到账 = 贷款金额 × (1 - 手续费率)
              </Typography.Text>
            </Card>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ParticipantBalances
