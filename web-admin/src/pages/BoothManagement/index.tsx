import { useState, useEffect } from 'react'
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  message,
  Tag,
  Popconfirm,
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import {
  getBooths,
  createBooth,
  updateBooth,
  deleteBooth,
  type Booth,
  type CreateBoothRequest,
  type UpdateBoothRequest,
} from '@/services/booth'
import { getEvents, type Event } from '@/services/event'
import dayjs from 'dayjs'

const BoothManagement = () => {
  const [booths, setBooths] = useState<Booth[]>([])
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingBooth, setEditingBooth] = useState<Booth | null>(null)
  const [selectedEventId, setSelectedEventId] = useState<number>()
  const [form] = Form.useForm()

  useEffect(() => {
    loadEvents()
  }, [])

  useEffect(() => {
    if (selectedEventId) {
      loadBooths()
    }
  }, [selectedEventId])

  const loadEvents = async () => {
    try {
      const data = await getEvents({ status: 'active' })
      setEvents(data)
      if (data.length > 0) {
        setSelectedEventId(data[0].id)
      }
    } catch (error) {
      // 错误已处理
    }
  }

  const loadBooths = async () => {
    if (!selectedEventId) return
    setLoading(true)
    try {
      const data = await getBooths({ event_id: selectedEventId, limit: 100 })
      setBooths(data)
    } catch (error) {
      // 错误已处理
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingBooth(null)
    form.resetFields()
    form.setFieldsValue({ event_id: selectedEventId })
    setModalVisible(true)
  }

  const handleEdit = (record: Booth) => {
    setEditingBooth(record)
    form.setFieldsValue({
      event_id: record.event_id,
      name: record.name,
      class_name: record.class_name,
      status: record.status,
    })
    setModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteBooth(id)
      message.success('删除成功')
      loadBooths()
    } catch (error) {
      // 错误已处理
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      if (editingBooth) {
        const data: UpdateBoothRequest = {
          name: values.name,
          class_name: values.class_name,
          status: values.status,
        }
        await updateBooth(editingBooth.id, data)
        message.success('更新成功')
      } else {
        const data: CreateBoothRequest = {
          event_id: values.event_id,
          name: values.name,
          class_name: values.class_name,
        }
        await createBooth(data)
        message.success('创建成功')
      }

      setModalVisible(false)
      loadBooths()
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
      title: '摊位名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '班级',
      dataIndex: 'class_name',
      key: 'class_name',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          active: 'success',
          inactive: 'default',
          closed: 'error',
        }
        const textMap: Record<string, string> = {
          active: '营业中',
          inactive: '未营业',
          closed: '已关闭',
        }
        return <Tag color={colorMap[status]}>{textMap[status]}</Tag>
      },
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
      width: 150,
      render: (_: any, record: Booth) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除此摊位吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
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
          onChange={setSelectedEventId}
          options={events.map((e) => ({ label: e.name, value: e.id }))}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新建摊位
        </Button>
      </Space>

      <Table
        columns={columns}
        dataSource={booths}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title={editingBooth ? '编辑摊位' : '新建摊位'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="event_id"
            label="所属活动"
            rules={[{ required: true, message: '请选择所属活动' }]}
          >
            <Select disabled={!!editingBooth}>
              {events.map((e) => (
                <Select.Option key={e.id} value={e.id}>
                  {e.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="name"
            label="摊位名称"
            rules={[{ required: true, message: '请输入摊位名称' }]}
          >
            <Input placeholder="请输入摊位名称" />
          </Form.Item>

          <Form.Item
            name="class_name"
            label="班级"
            rules={[{ required: true, message: '请输入班级' }]}
          >
            <Input placeholder="请输入班级" />
          </Form.Item>

          {editingBooth && (
            <Form.Item
              name="status"
              label="状态"
              rules={[{ required: true, message: '请选择状态' }]}
            >
              <Select>
                <Select.Option value="active">营业中</Select.Option>
                <Select.Option value="inactive">未营业</Select.Option>
                <Select.Option value="closed">已关闭</Select.Option>
              </Select>
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  )
}

export default BoothManagement
