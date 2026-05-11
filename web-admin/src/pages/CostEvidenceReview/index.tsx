import { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Select,
  Tag,
  Space,
  Statistic,
  Row,
  Col,
  Image,
  message,
  Popconfirm,
  Typography,
  Badge,
  Tooltip,
} from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  EyeOutlined,
  FileImageOutlined,
  FilePdfOutlined,
} from '@ant-design/icons'
import {
  adminGetCostEvidences,
  adminGetCostEvidenceStats,
  adminReviewCostEvidence,
  adminBatchReviewCostEvidences,
  type AdminCostEvidence,
  type AdminCostEvidenceStats,
} from '@/services/costEvidence'
import { getToken } from '@/utils/auth'
import dayjs from 'dayjs'

const { Text } = Typography

const categoryLabelMap: Record<string, string> = {
  material: '原材料',
  logistics: '物流运输',
  labor: '人工费用',
  rent: '租金',
  other: '其他',
}

const statusLabelMap: Record<string, string> = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已驳回',
}

const statusColorMap: Record<string, string> = {
  pending: 'processing',
  approved: 'success',
  rejected: 'error',
}

const categoryOptions = [
  { value: 'material', label: '原材料' },
  { value: 'logistics', label: '物流运输' },
  { value: 'labor', label: '人工费用' },
  { value: 'rent', label: '租金' },
  { value: 'other', label: '其他' },
]

const CostEvidenceReview = () => {
  const [evidences, setEvidences] = useState<AdminCostEvidence[]>([])
  const [stats, setStats] = useState<AdminCostEvidenceStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [totalCount, setTotalCount] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(15)
  const [filterCategory, setFilterCategory] = useState<string | undefined>()
  const [filterStatus, setFilterStatus] = useState<string | undefined>('pending')
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [previewVisible, setPreviewVisible] = useState(false)
  const [previewUrl, setPreviewUrl] = useState('')
  const [reviewingId, setReviewingId] = useState<number | null>(null)

  useEffect(() => {
    loadEvidences()
    loadStats()
  }, [currentPage, filterCategory, filterStatus])

  const loadEvidences = async () => {
    setLoading(true)
    try {
      const data = await adminGetCostEvidences({
        category: filterCategory,
        status: filterStatus,
        limit: pageSize,
        offset: (currentPage - 1) * pageSize,
      })
      setEvidences(data.evidences || [])
      setTotalCount(data.total_count || 0)
    } catch (error) {
      message.error('加载凭据列表失败')
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const data = await adminGetCostEvidenceStats()
      setStats(data)
    } catch (error) {
      // 静默
    }
  }

  const handleReview = async (id: number, action: 'approve' | 'reject') => {
    setReviewingId(id)
    try {
      await adminReviewCostEvidence(id, { action })
      message.success(action === 'approve' ? '已通过' : '已驳回')
      loadEvidences()
      loadStats()
      setSelectedRowKeys((keys) => keys.filter((k) => k !== id))
    } catch (error: any) {
      if (error?.response?.data?.message) {
        message.error(error.response.data.message)
      } else {
        message.error('审核操作失败')
      }
    } finally {
      setReviewingId(null)
    }
  }

  const handleBatchReview = async (action: 'approve' | 'reject') => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要审核的凭据')
      return
    }
    try {
      const result = await adminBatchReviewCostEvidences({
        ids: selectedRowKeys as number[],
        action,
      })
      message.success(result.message)
      setSelectedRowKeys([])
      loadEvidences()
      loadStats()
    } catch (error: any) {
      if (error?.response?.data?.message) {
        message.error(error.response.data.message)
      } else {
        message.error('批量审核失败')
      }
    }
  }

  const handlePreview = (record: AdminCostEvidence) => {
    const token = getToken()
    const url = `/api/admin/cost-evidence/${record.id}/file`
    if (record.mime_type.startsWith('image/')) {
      fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((res) => res.blob())
        .then((blob) => {
          const blobUrl = URL.createObjectURL(blob)
          setPreviewUrl(blobUrl)
          setPreviewVisible(true)
        })
        .catch(() => message.error('预览失败'))
    } else {
      fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((res) => res.blob())
        .then((blob) => {
          const blobUrl = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = blobUrl
          a.download = record.filename
          a.click()
          URL.revokeObjectURL(blobUrl)
        })
        .catch(() => message.error('下载失败'))
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }

  const columns = [
    {
      title: '文件',
      dataIndex: 'filename',
      key: 'filename',
      width: 180,
      ellipsis: true,
      render: (text: string, record: AdminCostEvidence) => (
        <Space>
          {record.mime_type.startsWith('image/') ? (
            <FileImageOutlined style={{ color: '#1890ff' }} />
          ) : (
            <FilePdfOutlined style={{ color: '#ff4d4f' }} />
          )}
          <Tooltip title={text}>
            <Text ellipsis style={{ maxWidth: 130 }}>{text}</Text>
          </Tooltip>
        </Space>
      ),
    },
    {
      title: '商铺',
      key: 'booth',
      width: 150,
      render: (_: any, record: AdminCostEvidence) => (
        <div>
          <div style={{ fontWeight: 500 }}>{record.booth_name}</div>
          <div style={{ fontSize: 12, color: '#8c8c8c' }}>{record.class_name}</div>
        </div>
      ),
    },
    {
      title: '类别',
      dataIndex: 'category',
      key: 'category',
      width: 90,
      render: (category: string) => (
        <Tag>{categoryLabelMap[category] || category}</Tag>
      ),
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 100,
      render: (amount: number | null) =>
        amount !== null ? (
          <span style={{ fontWeight: 500 }}>¥{amount.toFixed(2)}</span>
        ) : (
          '-'
        ),
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 80,
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: 150,
      ellipsis: true,
      render: (desc: string | null) => desc || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status: string) => (
        <Tag color={statusColorMap[status] || 'default'}>
          {statusLabelMap[status] || status}
        </Tag>
      ),
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right' as const,
      render: (_: any, record: AdminCostEvidence) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handlePreview(record)}
          >
            查看
          </Button>
          {record.status === 'pending' && (
            <>
              <Popconfirm
                title="确定通过该凭据？"
                onConfirm={() => handleReview(record.id, 'approve')}
                okText="确定"
                cancelText="取消"
              >
                <Button
                  type="link"
                  size="small"
                  style={{ color: '#52c41a' }}
                  icon={<CheckCircleOutlined />}
                  loading={reviewingId === record.id}
                >
                  通过
                </Button>
              </Popconfirm>
              <Popconfirm
                title="确定驳回该凭据？"
                onConfirm={() => handleReview(record.id, 'reject')}
                okText="确定"
                cancelText="取消"
              >
                <Button
                  type="link"
                  size="small"
                  danger
                  icon={<CloseCircleOutlined />}
                  loading={reviewingId === record.id}
                >
                  驳回
                </Button>
              </Popconfirm>
            </>
          )}
        </Space>
      ),
    },
  ]

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => setSelectedRowKeys(keys),
    getCheckboxProps: (record: AdminCostEvidence) => ({
      disabled: record.status !== 'pending',
    }),
  }

  return (
    <div>
      {/* 统计卡片 */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="待审核"
                value={stats.pending_count}
                suffix="份"
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic title="凭据总数" value={stats.total_count} suffix="份" />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="总金额"
                value={stats.total_amount}
                precision={2}
                prefix="¥"
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="已通过"
                value={
                  stats.by_status.find((s) => s.status === 'approved')?.count || 0
                }
                suffix="份"
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 凭据审核列表 */}
      <Card
        title={
          <Space>
            <span>成本凭据审核</span>
            {stats && stats.pending_count > 0 && (
              <Badge count={stats.pending_count} />
            )}
          </Space>
        }
        extra={
          selectedRowKeys.length > 0 && (
            <Space>
              <span style={{ color: '#8c8c8c' }}>
                已选 {selectedRowKeys.length} 项
              </span>
              <Popconfirm
                title={`确定批量通过 ${selectedRowKeys.length} 条凭据？`}
                onConfirm={() => handleBatchReview('approve')}
                okText="确定"
                cancelText="取消"
              >
                <Button type="primary" size="small" icon={<CheckCircleOutlined />}>
                  批量通过
                </Button>
              </Popconfirm>
              <Popconfirm
                title={`确定批量驳回 ${selectedRowKeys.length} 条凭据？`}
                onConfirm={() => handleBatchReview('reject')}
                okText="确定"
                cancelText="取消"
              >
                <Button danger size="small" icon={<CloseCircleOutlined />}>
                  批量驳回
                </Button>
              </Popconfirm>
            </Space>
          )
        }
      >
        {/* 筛选 */}
        <Space style={{ marginBottom: 16 }}>
          <Select
            placeholder="按类别筛选"
            allowClear
            style={{ width: 140 }}
            value={filterCategory}
            onChange={(val) => {
              setFilterCategory(val)
              setCurrentPage(1)
            }}
            options={categoryOptions}
          />
          <Select
            placeholder="按状态筛选"
            allowClear
            style={{ width: 120 }}
            value={filterStatus}
            onChange={(val) => {
              setFilterStatus(val)
              setCurrentPage(1)
            }}
            options={[
              { value: 'pending', label: '待审核' },
              { value: 'approved', label: '已通过' },
              { value: 'rejected', label: '已驳回' },
            ]}
          />
        </Space>

        <Table
          columns={columns}
          dataSource={evidences}
          rowKey="id"
          loading={loading}
          rowSelection={rowSelection}
          scroll={{ x: 1200 }}
          pagination={{
            current: currentPage,
            pageSize,
            total: totalCount,
            onChange: (page) => setCurrentPage(page),
            showTotal: (total) => `共 ${total} 条`,
            showSizeChanger: false,
          }}
          locale={{ emptyText: '暂无凭据记录' }}
        />
      </Card>

      {/* 图片预览 */}
      <Image
        style={{ display: 'none' }}
        preview={{
          visible: previewVisible,
          src: previewUrl,
          onVisibleChange: (visible) => setPreviewVisible(visible),
        }}
      />
    </div>
  )
}

export default CostEvidenceReview
