import React, { useState, useEffect, useRef } from 'react'
import {
  Card,
  Table,
  Button,
  Upload,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  message,
  Tag,
  Space,
  Statistic,
  Row,
  Col,
  Image,
  Popconfirm,
  Typography,
  Empty,
  Pagination,
} from 'antd'
import {
  UploadOutlined,
  FileImageOutlined,
  FilePdfOutlined,
  DeleteOutlined,
  EyeOutlined,
  PlusOutlined,
} from '@ant-design/icons'
import type { UploadFile, UploadProps } from 'antd'
import {
  getCostEvidences,
  uploadCostEvidence,
  deleteCostEvidence,
  getCostEvidenceStats,
  type CostEvidence,
  type CostEvidenceStats,
} from '@/services/merchant'
import { useIsMobile } from '@/hooks/useIsMobile'
import { getToken } from '@/utils/auth'
import dayjs from 'dayjs'
import './merchant-mobile.css'

const { Text } = Typography
const { TextArea } = Input

const categoryOptions = [
  { value: 'material', label: '原材料' },
  { value: 'logistics', label: '物流运输' },
  { value: 'labor', label: '人工费用' },
  { value: 'rent', label: '租金' },
  { value: 'other', label: '其他' },
]

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

const MerchantCostEvidence = () => {
  const [evidences, setEvidences] = useState<CostEvidence[]>([])
  const [stats, setStats] = useState<CostEvidenceStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [totalCount, setTotalCount] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(10)
  const [uploadModalVisible, setUploadModalVisible] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [previewVisible, setPreviewVisible] = useState(false)
  const [previewUrl, setPreviewUrl] = useState('')
  const [filterCategory, setFilterCategory] = useState<string | undefined>()
  const [filterStatus, setFilterStatus] = useState<string | undefined>()
  const [form] = Form.useForm()
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const isMobile = useIsMobile()

  // 请求通知权限
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
  }, [])

  useEffect(() => {
    loadEvidences()
    loadStats()
  }, [currentPage, filterCategory, filterStatus])

  // 5秒自动刷新 + 审批结果通知
  const prevApprovedCountRef = useRef<number | null>(null)
  const prevRejectedCountRef = useRef<number | null>(null)

  useEffect(() => {
    const interval = setInterval(() => {
      loadEvidences()
      loadStats()
    }, 5000)
    return () => clearInterval(interval)
  }, [currentPage, filterCategory, filterStatus])

  // 当审批通过/驳回数量增加时发送浏览器通知
  useEffect(() => {
    if (stats === null) return
    const approvedCount = stats.by_status.find((s) => s.status === 'approved')?.count || 0
    const rejectedCount = stats.by_status.find((s) => s.status === 'rejected')?.count || 0

    if (prevApprovedCountRef.current !== null && approvedCount > prevApprovedCountRef.current) {
      const newCount = approvedCount - prevApprovedCountRef.current
      sendNotification(`${newCount} 条凭据已通过审批 ✓`, '管理员已审核通过您提交的成本凭据')
    }
    if (prevRejectedCountRef.current !== null && rejectedCount > prevRejectedCountRef.current) {
      const newCount = rejectedCount - prevRejectedCountRef.current
      sendNotification(`${newCount} 条凭据被驳回 ✗`, '管理员驳回了您提交的成本凭据，请检查后重新提交')
    }

    prevApprovedCountRef.current = approvedCount
    prevRejectedCountRef.current = rejectedCount
  }, [stats])

  const loadEvidences = async () => {
    setLoading(true)
    try {
      const data = await getCostEvidences({
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
      const data = await getCostEvidenceStats()
      setStats(data)
    } catch (error) {
      // 静默处理
    }
  }

  const handleUpload = async () => {
    try {
      const values = await form.validateFields()

      if (fileList.length === 0 || !fileList[0]) {
        message.error('请选择要上传的文件')
        return
      }

      const rawFile = (fileList[0].originFileObj || fileList[0]) as File
      if (!rawFile || !(rawFile instanceof Blob)) {
        message.error('文件无效，请重新选择')
        return
      }

      setUploading(true)

      const formData = new FormData()
      formData.append('file', rawFile, fileList[0].name)
      formData.append('category', values.category || 'other')
      if (values.amount !== undefined && values.amount !== null) {
        formData.append('amount', values.amount.toString())
      }
      if (values.description) {
        formData.append('description', values.description)
      }

      await uploadCostEvidence(formData)
      message.success('凭据上传成功')
      setUploadModalVisible(false)
      form.resetFields()
      setFileList([])
      loadEvidences()
      loadStats()
    } catch (error: any) {
      if (error?.response?.data?.message) {
        message.error(error.response.data.message)
      } else {
        message.error('上传失败，请重试')
      }
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteCostEvidence(id)
      message.success('凭据已删除')
      loadEvidences()
      loadStats()
    } catch (error: any) {
      if (error?.response?.data?.message) {
        message.error(error.response.data.message)
      } else {
        message.error('删除失败')
      }
    }
  }

  const handlePreview = (record: CostEvidence) => {
    const token = getToken()
    const url = `/api/merchant/cost-evidence/${record.id}/file`
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

  const uploadProps: UploadProps = {
    beforeUpload: (file) => {
      const allowedTypes = [
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
        'application/pdf',
      ]
      if (!allowedTypes.includes(file.type)) {
        message.error('只支持 JPG/PNG/GIF/WebP/PDF 格式')
        return Upload.LIST_IGNORE
      }
      if (file.size > 10 * 1024 * 1024) {
        message.error('文件大小不能超过 10MB')
        return Upload.LIST_IGNORE
      }
      const uploadFile: UploadFile = {
        uid: file.uid || `${Date.now()}`,
        name: file.name,
        size: file.size,
        type: file.type,
        status: 'done',
        originFileObj: file as any,
      }
      setFileList([uploadFile])
      return false
    },
    fileList,
    onRemove: () => {
      setFileList([])
    },
    maxCount: 1,
    accept: '.jpg,.jpeg,.png,.gif,.webp,.pdf',
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }

  const columns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      ellipsis: true,
      render: (text: string, record: CostEvidence) => (
        <Space>
          {record.mime_type.startsWith('image/') ? (
            <FileImageOutlined style={{ color: '#1890ff' }} />
          ) : (
            <FilePdfOutlined style={{ color: '#ff4d4f' }} />
          )}
          <Text ellipsis style={{ maxWidth: 150 }}>
            {text}
          </Text>
        </Space>
      ),
    },
    {
      title: '类别',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (category: string) => <Tag>{categoryLabelMap[category] || category}</Tag>,
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 100,
      render: (amount: number | null) =>
        amount !== null ? `¥${amount.toFixed(2)}` : '-',
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size: number) => formatFileSize(size),
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
      width: 160,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: CostEvidence) => (
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
            <Popconfirm
              title="确定删除该凭据？"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button type="link" size="small" danger icon={<DeleteOutlined />}>
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  const renderMobileList = () => {
    if (loading) {
      return <div style={{ textAlign: 'center', padding: 30 }}>加载中...</div>
    }
    if (evidences.length === 0) {
      return <Empty description="暂无凭据记录" />
    }
    return (
      <div>
        {evidences.map((ev) => (
          <div key={ev.id} className="merchant-mobile-list-item">
            <div className="merchant-mobile-list-item-header">
              <span style={{ display: 'flex', alignItems: 'center', gap: 6, maxWidth: '60%' }}>
                {ev.mime_type.startsWith('image/') ? (
                  <FileImageOutlined style={{ color: '#1890ff' }} />
                ) : (
                  <FilePdfOutlined style={{ color: '#ff4d4f' }} />
                )}
                <Text ellipsis style={{ maxWidth: '100%' }}>
                  {ev.filename}
                </Text>
              </span>
              <Tag color={statusColorMap[ev.status] || 'default'}>
                {statusLabelMap[ev.status] || ev.status}
              </Tag>
            </div>
            <div className="merchant-mobile-list-item-row">
              <span className="label">类别</span>
              <span className="value">
                <Tag>{categoryLabelMap[ev.category] || ev.category}</Tag>
              </span>
            </div>
            {ev.amount != null && (
              <div className="merchant-mobile-list-item-row">
                <span className="label">金额</span>
                <span className="value" style={{ color: '#f5576c', fontWeight: 600 }}>
                  ¥{ev.amount.toFixed(2)}
                </span>
              </div>
            )}
            <div className="merchant-mobile-list-item-row">
              <span className="label">大小</span>
              <span className="value">{formatFileSize(ev.file_size)}</span>
            </div>
            <div className="merchant-mobile-list-item-row">
              <span className="label">上传时间</span>
              <span className="value">{dayjs(ev.created_at).format('MM-DD HH:mm')}</span>
            </div>
            <div className="merchant-mobile-list-item-actions">
              <Button
                size="small"
                icon={<EyeOutlined />}
                onClick={() => handlePreview(ev)}
              >
                查看
              </Button>
              {ev.status === 'pending' && (
                <Popconfirm
                  title="确定删除该凭据？"
                  onConfirm={() => handleDelete(ev.id)}
                  okText="确定"
                  cancelText="取消"
                >
                  <Button size="small" danger icon={<DeleteOutlined />}>
                    删除
                  </Button>
                </Popconfirm>
              )}
            </div>
          </div>
        ))}
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Pagination
            current={currentPage}
            pageSize={pageSize}
            total={totalCount}
            onChange={(p) => setCurrentPage(p)}
            showSizeChanger={false}
            simple
          />
          <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 6 }}>
            共 {totalCount} 条
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      {/* 统计卡片 */}
      {stats && (
        <Row gutter={[12, 12]} style={{ marginBottom: isMobile ? 12 : 24 }}>
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
                title="待审核"
                value={stats.by_status.find((s) => s.status === 'pending')?.count || 0}
                suffix="份"
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="已通过"
                value={stats.by_status.find((s) => s.status === 'approved')?.count || 0}
                suffix="份"
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 凭据列表 */}
      <Card
        title="成本凭据"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            size={isMobile ? 'small' : 'middle'}
            onClick={() => setUploadModalVisible(true)}
          >
            {isMobile ? '上传' : '上传凭据'}
          </Button>
        }
      >
        {/* 筛选 */}
        {isMobile ? (
          <Row gutter={8} style={{ marginBottom: 12 }}>
            <Col span={12}>
              <Select
                placeholder="类别"
                allowClear
                style={{ width: '100%' }}
                value={filterCategory}
                onChange={(val) => {
                  setFilterCategory(val)
                  setCurrentPage(1)
                }}
                options={categoryOptions}
              />
            </Col>
            <Col span={12}>
              <Select
                placeholder="状态"
                allowClear
                style={{ width: '100%' }}
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
            </Col>
          </Row>
        ) : (
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
        )}

        {isMobile ? (
          renderMobileList()
        ) : (
          <Table
            columns={columns}
            dataSource={evidences}
            rowKey="id"
            loading={loading}
            pagination={{
              current: currentPage,
              pageSize,
              total: totalCount,
              onChange: (page) => setCurrentPage(page),
              showTotal: (total) => `共 ${total} 条`,
              showSizeChanger: false,
            }}
            locale={{
              emptyText: <Empty description="暂无凭据记录" />,
            }}
          />
        )}
      </Card>

      {/* 上传弹窗 */}
      <Modal
        title="上传成本凭据"
        open={uploadModalVisible}
        onOk={handleUpload}
        onCancel={() => {
          setUploadModalVisible(false)
          form.resetFields()
          setFileList([])
        }}
        confirmLoading={uploading}
        okText="上传"
        cancelText="取消"
        width={isMobile ? '94%' : 500}
        centered
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="凭据文件"
            required
            extra="支持 JPG/PNG/GIF/WebP/PDF 格式，最大 10MB"
          >
            <Upload {...uploadProps} listType="picture">
              <Button icon={<UploadOutlined />}>选择文件</Button>
            </Upload>
          </Form.Item>

          <Form.Item
            name="category"
            label="凭据类别"
            initialValue="other"
            rules={[{ required: true, message: '请选择凭据类别' }]}
          >
            <Select options={categoryOptions} />
          </Form.Item>

          <Form.Item name="amount" label="凭据金额（元）">
            <InputNumber
              min={0}
              precision={2}
              style={{ width: '100%' }}
              placeholder="请输入凭据金额"
            />
          </Form.Item>

          <Form.Item
            name="description"
            label="备注说明"
            rules={[{ max: 500, message: '最多500个字符' }]}
          >
            <TextArea rows={3} placeholder="请输入备注说明（可选）" maxLength={500} showCount />
          </Form.Item>
        </Form>
      </Modal>

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

export default MerchantCostEvidence
