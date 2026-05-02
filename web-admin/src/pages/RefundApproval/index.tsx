import { useState, useEffect } from 'react'
import {
  Table,
  Space,
  Select,
  Button,
  Tag,
  Modal,
  Form,
  Input,
  message,
} from 'antd'
import { CheckOutlined, CloseOutlined } from '@ant-design/icons'
import {
  getTransactions,
  refund,
  type Transaction,
  type TransactionListResponse,
} from '@/services/transaction'
import { getEvents, type Event } from '@/services/event'
import dayjs from 'dayjs'

const RefundApproval = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null)
  const [selectedEventId, setSelectedEventId] = useState<number>()
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20 })
  const [form] = Form.useForm()

  useEffect(() => {
    loadEvents()
  }, [])

  useEffect(() => {
    if (selectedEventId) {
      loadTransactions()
    }
  }, [selectedEventId, pagination.current])

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

  const loadTransactions = async () => {
    if (!selectedEventId) return
    setLoading(true)
    try {
      const params = {
        event_id: selectedEventId,
        type: 'pay', // 只显示支付交易，可以退款
        limit: pagination.pageSize,
        offset: (pagination.current - 1) * pagination.pageSize,
      }

      const data: TransactionListResponse = await getTransactions(params)
      setTransactions(data?.transactions || [])
      setTotalCount(data?.total_count || 0)
    } catch (error) {
      // 错误已处理
    } finally {
      setLoading(false)
    }
  }

  const handleRefund = (record: Transaction) => {
    setSelectedTransaction(record)
    form.resetFields()
    setModalVisible(true)
  }

  const handleSubmit = async () => {
    if (!selectedTransaction) return
    try {
      const values = await form.validateFields()
      await refund({
        transaction_id: selectedTransaction.id,
        reason: values.reason,
      })
      message.success('退款成功')
      setModalVisible(false)
      loadTransactions()
    } catch (error) {
      // 错误已处理
    }
  }

  const columns = [
    {
      title: '交易ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      render: (amount: number) => (
        <span style={{ color: '#ff4d4f' }}>-¥{(amount / 100).toFixed(2)}</span>
      ),
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
    {
      title: '状态',
      dataIndex: 'related_txn_id',
      key: 'status',
      width: 100,
      render: (relatedId: number | null) => (
        <Tag color={relatedId ? 'default' : 'success'}>
          {relatedId ? '已退款' : '正常'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: Transaction) => (
        <Space>
          {!record.related_txn_id && (
            <Button
              type="link"
              size="small"
              icon={<CheckOutlined />}
              onClick={() => handleRefund(record)}
            >
              退款
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Select
          style={{ width: 200 }}
          placeholder="选择活动"
          value={selectedEventId}
          onChange={(value) => {
            setSelectedEventId(value)
            setPagination({ current: 1, pageSize: 20 })
          }}
          options={events.map((e) => ({ label: e.name, value: e.id }))}
        />
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
        scroll={{ x: 1200 }}
      />

      <Modal
        title="退款确认"
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={500}
      >
        <Form form={form} layout="vertical">
          <Form.Item label="交易信息">
            <div>
              <p>交易ID：{selectedTransaction?.id}</p>
              <p>
                金额：¥
                {selectedTransaction
                  ? (selectedTransaction.amount / 100).toFixed(2)
                  : '0.00'}
              </p>
              <p>卡号：{selectedTransaction?.card_uid}</p>
              <p>
                交易时间：
                {selectedTransaction
                  ? dayjs(selectedTransaction.created_at).format('YYYY-MM-DD HH:mm:ss')
                  : '-'}
              </p>
            </div>
          </Form.Item>

          <Form.Item
            name="reason"
            label="退款原因"
            rules={[{ required: true, message: '请输入退款原因' }]}
          >
            <Input.TextArea rows={4} placeholder="请输入退款原因" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default RefundApproval
