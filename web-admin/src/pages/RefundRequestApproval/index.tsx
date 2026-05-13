import React, { useState, useEffect, useRef } from 'react'
import {
  Card,
  Table,
  Button,
  Tag,
  Space,
  Modal,
  Input,
  message,
  Statistic,
  Row,
  Col,
  Popconfirm,
  Typography,
  Badge,
} from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import {
  getRefundRequests,
  approveRefundRequest,
  rejectRefundRequest,
  type RefundRequestItem,
} from '@/services/refundRequest'
import dayjs from 'dayjs'

const { Text } = Typography

const statusMap: Record<string, { label: string; color: string }> = {
  pending: { label: '待审批', color: 'processing' },
  approved: { label: '已通过', color: 'success' },
  rejected: { label: '已驳回', color: 'error' },
}

// 浏览器通知
function sendNotification(title: string, body: string) {
  if (!('Notification' in window)) return
  if (Notification.permission === 'granted') {
    new Notification(title, { body, icon: '/favicon.ico' })
  } else if (Notification.permission !== 'denied') {
    Notification.requestPermission().then((permission) => {
      if (permission === 'granted') {
        new Notification(title, { body, icon: '/favicon.ico' })
      }
    })
  }
}

const RefundRequestApproval = () => {
  const [requests, setRequests] = useState<RefundRequestItem[]>([])
  const [loading, setLoading] = useState(false)
  const [totalCount, setTotalCount] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(20)
  const [statusFilter, setStatusFilter] = useState<string>('pending')

  // 驳回弹窗
  const [rejectModalVisible, setRejectModalVisible] = useState(false)
  const [rejectingId, setRejectingId] = useState<number | null>(null)
  const [rejectRemark, setRejectRemark] = useState('')

  useEffect(() => {
    loadRequests()
  }, [currentPage, statusFilter])

  // 请求通知权限
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
  }, [])

  // 5秒自动刷新 + 新退款申请通知
  const prevPendingCountRef = useRef<number | null>(null)

  useEffect(() => {
    const interval = setInterval(() => {
      loadRequests()
    }, 5000)
    return () => clearInterval(interval)
  }, [currentPage, statusFilter])

  // 当待审批数量增加时发送浏览器通知
  useEffect(() => {
    if (statusFilter !== 'pending') return
    const currentPending = totalCount
    if (prevPendingCountRef.current !== null && currentPending > prevPendingCountRef.current) {
      const newCount = currentPending - prevPendingCountRef.current
      sendNotification(`收到 ${newCount} 条新退款申请`, `当前共 ${currentPending} 条待审批`)
    }
    prevPendingCountRef.current = currentPending
  }, [totalCount, statusFilter])

  const loadRequests = async () => {
    setLoading(true)
    try {
      const data = await getRefundRequests({
        status: statusFilter || undefined,
        limit: pageSize,
        offset: (currentPage - 1) * pageSize,
      })
      setRequests(data.requests || [])
      setTotalCount(data.total_count || 0)
    } catch {
      message.error('加载退款申请失败')
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (id: number) => {
    try {
      await approveRefundRequest(id)
      message.success('退款申请已通过，退款已执行')
      loadRequests()
    } catch {
      message.error('审批失败')
    }
  }

  const handleReject = async () => {
    if (!rejectingId) return
    try {
      await rejectRefundRequest(rejectingId, rejectRemark)
      message.success('退款申请已驳回')
      setRejectModalVisible(false)
      setRejectRemark('')
      setRejectingId(null)
      loadRequests()
    } catch {
      message.error('驳回失败')
    }
  }

  const showRejectModal = (id: number) => {
    setRejectingId(id)
    setRejectRemark('')
    setRejectModalVisible(true)
  }

  const pendingCount = statusFilter === 'pending' ? totalCount : 0

  const columns = [
    {
      title: '申请时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (v: string | null) =>
        v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
    {
      title: '申请人',
      dataIndex: 'requester_name',
      key: 'requester_name',
      width: 100,
      render: (v: string) => <Text strong>{v}</Text>,
    },
    {
      title: '退款金额',
      dataIndex: 'txn_amount',
      key: 'txn_amount',
      width: 110,
      align: 'right' as const,
      render: (v: number) => (
        <Text type="danger" strong>¥{v.toFixed(2)}</Text>
      ),
    },
    {
      title: '卡号',
      dataIndex: 'card_uid',
      key: 'card_uid',
      width: 120,
      render: (v: string | null) => v || '-',
    },
    {
      title: '原交易时间',
      dataIndex: 'txn_time',
      key: 'txn_time',
      width: 160,
      render: (v: string | null) =>
        v ? dayjs(v).format('MM-DD HH:mm:ss') : '-',
    },
    {
      title: '退款原因',
      dataIndex: 'reason',
      key: 'reason',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (s: string) => {
        const info = statusMap[s] || { label: s, color: 'default' }
        return <Badge status={info.color as any} text={info.label} />
      },
    },
    {
      title: '审批人',
      dataIndex: 'approver_name',
      key: 'approver_name',
      width: 100,
      render: (v: string | null) => v || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 160,
      render: (_: any, record: RefundRequestItem) => {
        if (record.status !== 'pending') return <Text type="secondary">已处理</Text>
        return (
          <Space>
            <Popconfirm
              title="确认通过此退款申请？"
              description={`将退还 ¥${record.txn_amount.toFixed(2)} 到持卡人账户`}
              onConfirm={() => handleApprove(record.id)}
              okText="确认通过"
              cancelText="取消"
            >
              <Button type="primary" size="small" icon={<CheckCircleOutlined />}>
                通过
              </Button>
            </Popconfirm>
            <Button
              danger
              size="small"
              icon={<CloseCircleOutlined />}
              onClick={() => showRejectModal(record.id)}
            >
              驳回
            </Button>
          </Space>
        )
      },
    },
  ]

  return (
    <div>
      <Card title="退款审批" style={{ marginBottom: 16 }}>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Statistic
              title="待审批"
              value={statusFilter === 'pending' ? totalCount : '-'}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col span={18}>
            <Space>
              <Button
                type={statusFilter === 'pending' ? 'primary' : 'default'}
                onClick={() => { setStatusFilter('pending'); setCurrentPage(1) }}
              >
                待审批
              </Button>
              <Button
                type={statusFilter === 'approved' ? 'primary' : 'default'}
                onClick={() => { setStatusFilter('approved'); setCurrentPage(1) }}
              >
                已通过
              </Button>
              <Button
                type={statusFilter === 'rejected' ? 'primary' : 'default'}
                onClick={() => { setStatusFilter('rejected'); setCurrentPage(1) }}
              >
                已驳回
              </Button>
              <Button
                type={statusFilter === '' ? 'primary' : 'default'}
                onClick={() => { setStatusFilter(''); setCurrentPage(1) }}
              >
                全部
              </Button>
            </Space>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={requests}
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

      {/* 驳回弹窗 */}
      <Modal
        title="驳回退款申请"
        open={rejectModalVisible}
        onOk={handleReject}
        onCancel={() => { setRejectModalVisible(false); setRejectingId(null) }}
        okText="确认驳回"
        okButtonProps={{ danger: true }}
      >
        <Input.TextArea
          rows={3}
          placeholder="请输入驳回原因（可选）"
          value={rejectRemark}
          onChange={(e) => setRejectRemark(e.target.value)}
        />
      </Modal>
    </div>
  )
}

export default RefundRequestApproval
