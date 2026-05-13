import { useState, useEffect } from 'react'
import {
  Card,
  Form,
  InputNumber,
  Switch,
  Button,
  message,
  Statistic,
  Row,
  Col,
  Table,
  Select,
  Space,
  Modal,
  Tag,
  Progress,
  Divider,
} from 'antd'
import {
  GiftOutlined,
  ReloadOutlined,
  DollarOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import {
  getDiscountSetting,
  saveDiscountSetting,
  resetDiscountPool,
  getDiscountStatistics,
  getDiscountRecords,
  type DiscountSetting,
  type DiscountStatistics,
  type DiscountRecord,
} from '@/services/randomDiscount'
import { getEvents, type Event } from '@/services/event'
import dayjs from 'dayjs'

const RandomDiscount = () => {
  const [events, setEvents] = useState<Event[]>([])
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null)
  const [setting, setSetting] = useState<DiscountSetting | null>(null)
  const [statistics, setStatistics] = useState<DiscountStatistics | null>(null)
  const [records, setRecords] = useState<DiscountRecord[]>([])
  const [recordsTotal, setRecordsTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    loadEvents()
  }, [])

  useEffect(() => {
    if (selectedEventId) {
      loadData()
    }
  }, [selectedEventId])

  const loadEvents = async () => {
    try {
      const data = await getEvents({ limit: 100 })
      const eventList = data?.events || []
      setEvents(eventList)
      // 自动选择第一个活跃的活动
      const activeEvent = eventList.find((e: Event) => e.status === 'active')
      if (activeEvent) {
        setSelectedEventId(activeEvent.id)
      } else if (eventList.length > 0) {
        setSelectedEventId(eventList[0].id)
      }
    } catch {
      setEvents([])
    }
  }

  const loadData = async () => {
    if (!selectedEventId) return
    setLoading(true)
    try {
      const [settingData, statsData, recordsData] = await Promise.all([
        getDiscountSetting(selectedEventId),
        getDiscountStatistics(selectedEventId),
        getDiscountRecords(selectedEventId, { limit: 20 }),
      ])

      setSetting(settingData)
      setStatistics(statsData)
      setRecords(recordsData?.records || [])
      setRecordsTotal(recordsData?.total_count || 0)

      // 填充表单
      if (settingData?.configured) {
        form.setFieldsValue({
          enabled: settingData.enabled,
          min_discount_amount: settingData.min_discount_amount,
          max_discount_amount: settingData.max_discount_amount,
          probability: settingData.probability,
          total_pool: settingData.total_pool,
          max_discount_per_transaction: settingData.max_discount_per_transaction,
          min_payment_amount: settingData.min_payment_amount,
          daily_limit_per_user: settingData.daily_limit_per_user,
        })
      } else {
        form.resetFields()
      }
    } catch {
      // 错误已处理
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!selectedEventId) return
    try {
      const values = await form.validateFields()
      setSaving(true)

      await saveDiscountSetting({
        event_id: selectedEventId,
        enabled: values.enabled || false,
        min_discount_amount: values.min_discount_amount,
        max_discount_amount: values.max_discount_amount,
        probability: values.probability,
        total_pool: values.total_pool,
        max_discount_per_transaction: values.max_discount_per_transaction || null,
        min_payment_amount: values.min_payment_amount,
        daily_limit_per_user: values.daily_limit_per_user || null,
      })

      message.success('配置保存成功')
      loadData()
    } catch {
      // 错误已处理
    } finally {
      setSaving(false)
    }
  }

  const handleResetPool = () => {
    if (!selectedEventId) return
    Modal.confirm({
      title: '确认重置奖池',
      content: '重置后奖池金额将恢复为总奖池金额，确定继续？',
      onOk: async () => {
        try {
          await resetDiscountPool(selectedEventId)
          message.success('奖池已重置')
          loadData()
        } catch {
          // 错误已处理
        }
      },
    })
  }

  const poolPercent =
    statistics && statistics.total_pool > 0
      ? Math.round((statistics.remaining_pool / statistics.total_pool) * 100)
      : 0

  const recordColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '参与者ID',
      dataIndex: 'participant_id',
      key: 'participant_id',
      width: 90,
    },
    {
      title: '交易ID',
      dataIndex: 'transaction_id',
      key: 'transaction_id',
      width: 80,
    },
    {
      title: '摊位ID',
      dataIndex: 'booth_id',
      key: 'booth_id',
      width: 80,
      render: (v: number | null) => v ?? '-',
    },
    {
      title: '原价（元）',
      dataIndex: 'original_amount',
      key: 'original_amount',
      width: 100,
      render: (v: number) => `¥${v.toFixed(2)}`,
    },
    {
      title: '立减（元）',
      dataIndex: 'discount_amount',
      key: 'discount_amount',
      width: 100,
      render: (v: number) => (
        <Tag color="red">-¥{v.toFixed(2)}</Tag>
      ),
    },
    {
      title: '实付（元）',
      dataIndex: 'actual_amount',
      key: 'actual_amount',
      width: 100,
      render: (v: number) => `¥${v.toFixed(2)}`,
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v: string) => v ? dayjs(v).format('MM-DD HH:mm:ss') : '-',
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <span>选择活动：</span>
          <Select
            style={{ width: 300 }}
            value={selectedEventId}
            onChange={(v) => setSelectedEventId(v)}
            placeholder="请选择活动"
          >
            {events.map((event) => (
              <Select.Option key={event.id} value={event.id}>
                {event.name}
                {event.status === 'active' && (
                  <Tag color="success" style={{ marginLeft: 8 }}>
                    进行中
                  </Tag>
                )}
              </Select.Option>
            ))}
          </Select>
          <Button icon={<ReloadOutlined />} onClick={loadData} loading={loading}>
            刷新
          </Button>
        </Space>
      </div>

      {selectedEventId && (
        <>
          {/* 统计卡片 */}
          {statistics && statistics.configured && (
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={4}>
                <Card>
                  <Statistic
                    title="状态"
                    value={statistics.enabled ? '已启用' : '已禁用'}
                    valueStyle={{ color: statistics.enabled ? '#52c41a' : '#999' }}
                    prefix={<ThunderboltOutlined />}
                  />
                </Card>
              </Col>
              <Col span={5}>
                <Card>
                  <Statistic
                    title="奖池剩余"
                    value={statistics.remaining_pool}
                    precision={2}
                    prefix={<DollarOutlined />}
                    suffix="元"
                  />
                  <Progress
                    percent={poolPercent}
                    size="small"
                    status={poolPercent < 20 ? 'exception' : 'active'}
                  />
                </Card>
              </Col>
              <Col span={5}>
                <Card>
                  <Statistic
                    title="已发放总额"
                    value={statistics.used_pool}
                    precision={2}
                    prefix={<GiftOutlined />}
                    suffix="元"
                  />
                </Card>
              </Col>
              <Col span={5}>
                <Card>
                  <Statistic
                    title="累计立减次数"
                    value={statistics.total_discount_count}
                    suffix="次"
                  />
                </Card>
              </Col>
              <Col span={5}>
                <Card>
                  <Statistic
                    title="今日立减"
                    value={statistics.today_discount_count}
                    suffix={`次 / ¥${statistics.today_discount_amount.toFixed(2)}`}
                  />
                </Card>
              </Col>
            </Row>
          )}

          {/* 配置表单 */}
          <Card
            title="随机立减配置"
            extra={
              setting?.configured && (
                <Button danger onClick={handleResetPool}>
                  重置奖池
                </Button>
              )
            }
          >
            <Form
              form={form}
              layout="vertical"
              initialValues={{
                enabled: false,
                min_discount_amount: 0.01,
                max_discount_amount: 5.0,
                probability: 100,
                total_pool: 1000,
                min_payment_amount: 1.0,
              }}
            >
              <Row gutter={24}>
                <Col span={6}>
                  <Form.Item
                    name="enabled"
                    label="启用随机立减"
                    valuePropName="checked"
                  >
                    <Switch checkedChildren="开" unCheckedChildren="关" />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item
                    name="probability"
                    label="触发概率（%）"
                    rules={[{ required: true, message: '请输入触发概率' }]}
                  >
                    <InputNumber min={1} max={100} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item
                    name="min_payment_amount"
                    label="最低消费门槛（元）"
                    rules={[{ required: true, message: '请输入最低消费金额' }]}
                  >
                    <InputNumber min={0} step={0.1} precision={2} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item
                    name="daily_limit_per_user"
                    label="每人每日限次"
                    tooltip="留空表示不限制"
                  >
                    <InputNumber min={1} style={{ width: '100%' }} placeholder="不限" />
                  </Form.Item>
                </Col>
              </Row>

              <Divider>立减金额范围</Divider>

              <Row gutter={24}>
                <Col span={6}>
                  <Form.Item
                    name="min_discount_amount"
                    label="最小立减金额（元）"
                    rules={[{ required: true, message: '请输入最小立减金额' }]}
                  >
                    <InputNumber min={0.01} step={0.1} precision={2} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item
                    name="max_discount_amount"
                    label="最大立减金额（元）"
                    rules={[{ required: true, message: '请输入最大立减金额' }]}
                  >
                    <InputNumber min={0.01} step={0.5} precision={2} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item
                    name="max_discount_per_transaction"
                    label="单笔最大立减（元）"
                    tooltip="留空表示不限制"
                  >
                    <InputNumber min={0.01} step={0.5} precision={2} style={{ width: '100%' }} placeholder="不限" />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item
                    name="total_pool"
                    label="总奖池金额（元）"
                    rules={[{ required: true, message: '请输入总奖池金额' }]}
                  >
                    <InputNumber min={1} step={100} precision={2} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Button type="primary" onClick={handleSave} loading={saving}>
                  保存配置
                </Button>
              </Form.Item>
            </Form>
          </Card>

          {/* 立减记录 */}
          <Card title="立减记录" style={{ marginTop: 16 }}>
            <Table
              columns={recordColumns}
              dataSource={records}
              rowKey="id"
              loading={loading}
              pagination={{
                total: recordsTotal,
                pageSize: 20,
                showTotal: (total) => `共 ${total} 条记录`,
              }}
              size="small"
            />
          </Card>
        </>
      )}
    </div>
  )
}

export default RandomDiscount
