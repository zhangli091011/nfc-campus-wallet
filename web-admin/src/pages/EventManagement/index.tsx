import { useState, useEffect } from 'react'
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  DatePicker,
  Select,
  Switch,
  message,
  Tag,
} from 'antd'
import { PlusOutlined, EditOutlined } from '@ant-design/icons'
import {
  getEvents,
  createEvent,
  updateEvent,
  // deleteEvent,
  type Event,
  type CreateEventRequest,
  type UpdateEventRequest,
} from '@/services/event'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

const EventManagement = () => {
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingEvent, setEditingEvent] = useState<Event | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadEvents()
  }, [])

  const loadEvents = async () => {
    setLoading(true)
    try {
      const data = await getEvents({ limit: 100 })  // 移除 status 筛选，显示所有活动
      const eventList = data?.events || []
      setEvents(eventList)
    } catch (error) {
      // 错误已处理
      setEvents([])
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingEvent(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: Event) => {
    setEditingEvent(record)
    form.setFieldsValue({
      name: record.name,
      dateRange: [dayjs(record.start_time), dayjs(record.end_time)],
      status: record.status,
      recharge_enabled: record.recharge_enabled,
      consume_enabled: record.consume_enabled,
    })
    setModalVisible(true)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const [startDate, endDate] = values.dateRange

      const data: CreateEventRequest | UpdateEventRequest = {
        name: values.name,
        start_time: startDate.format('YYYY-MM-DDTHH:mm:ss') + 'Z',
        end_time: endDate.format('YYYY-MM-DDTHH:mm:ss') + 'Z',
        ...(editingEvent && { 
          status: values.status,
          recharge_enabled: values.recharge_enabled,
          consume_enabled: values.consume_enabled,
        }),
        ...(!editingEvent && {
          status: 'draft',
          recharge_enabled: true,
          consume_enabled: true,
          expire_rule: 'event_end',
        }),
      }

      if (editingEvent) {
        await updateEvent(editingEvent.id, data)
        message.success('更新成功')
      } else {
        await createEvent(data as CreateEventRequest)
        message.success('创建成功')
      }

      setModalVisible(false)
      loadEvents()
    } catch (error) {
      // 错误已处理
    }
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '活动名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '开始时间',
      dataIndex: 'start_time',
      key: 'start_time',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '结束时间',
      dataIndex: 'end_time',
      key: 'end_time',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          draft: 'default',
          active: 'success',
          paused: 'warning',
          ended: 'error',
        }
        const textMap: Record<string, string> = {
          draft: '草稿',
          active: '进行中',
          paused: '已暂停',
          ended: '已结束',
        }
        return <Tag color={colorMap[status]}>{textMap[status]}</Tag>
      },
    },
    {
      title: '充值',
      dataIndex: 'recharge_enabled',
      key: 'recharge_enabled',
      render: (enabled: boolean) => (
        <Tag color={enabled ? 'success' : 'default'}>
          {enabled ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '消费',
      dataIndex: 'consume_enabled',
      key: 'consume_enabled',
      render: (enabled: boolean) => (
        <Tag color={enabled ? 'success' : 'default'}>
          {enabled ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: Event) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新建活动
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={events}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title={editingEvent ? '编辑活动' : '新建活动'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="活动名称"
            rules={[{ required: true, message: '请输入活动名称' }]}
          >
            <Input placeholder="请输入活动名称" />
          </Form.Item>

          <Form.Item
            name="dateRange"
            label="活动时间"
            rules={[{ required: true, message: '请选择活动时间' }]}
          >
            <RangePicker showTime style={{ width: '100%' }} />
          </Form.Item>

          {editingEvent && (
            <>
              <Form.Item
                name="status"
                label="状态"
                rules={[{ required: true, message: '请选择状态' }]}
              >
                <Select>
                  <Select.Option value="draft">草稿</Select.Option>
                  <Select.Option value="active">进行中</Select.Option>
                  <Select.Option value="paused">已暂停</Select.Option>
                  <Select.Option value="ended">已结束</Select.Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="recharge_enabled"
                label="充值功能"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="consume_enabled"
                label="消费功能"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </>
          )}
        </Form>
      </Modal>
    </div>
  )
}

export default EventManagement
