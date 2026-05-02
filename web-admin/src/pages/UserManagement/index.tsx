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
import { PlusOutlined } from '@ant-design/icons'
import {
  getUsers,
  createUser,
  updateUserStatus,
  type CreateUserRequest,
} from '@/services/user'
import { getBooths, type Booth } from '@/services/booth'
import { getEvents, type Event } from '@/services/event'
import { User } from '@/utils/auth'
import dayjs from 'dayjs'

const UserManagement = () => {
  const [users, setUsers] = useState<User[]>([])
  const [booths, setBooths] = useState<Booth[]>([])
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [selectedEventId, setSelectedEventId] = useState<number>()
  const [form] = Form.useForm()

  useEffect(() => {
    loadUsers()
    loadEvents()
  }, [])

  useEffect(() => {
    if (selectedEventId) {
      loadBooths()
    }
  }, [selectedEventId])

  const loadUsers = async () => {
    setLoading(true)
    try {
      const data = await getUsers({ limit: 100 })
      setUsers(Array.isArray(data) ? data : [])
    } catch (error) {
      // 错误已处理
      setUsers([])
    } finally {
      setLoading(false)
    }
  }

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

  const loadBooths = async () => {
    if (!selectedEventId) return
    try {
      const data = await getBooths({ event_id: selectedEventId, limit: 100 })
      setBooths(Array.isArray(data) ? data : [])
    } catch (error) {
      // 错误已处理
      setBooths([])
    }
  }

  const handleAdd = () => {
    form.resetFields()
    setModalVisible(true)
  }

  const handleUpdateStatus = async (id: number, status: 'active' | 'inactive' | 'blocked') => {
    try {
      await updateUserStatus(id, status)
      message.success('更新成功')
      loadUsers()
    } catch (error) {
      // 错误已处理
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const data: CreateUserRequest = {
        username: values.username,
        password: values.password,
        role: values.role,
        booth_id: values.booth_id || null,
      }
      await createUser(data)
      message.success('创建成功')
      setModalVisible(false)
      loadUsers()
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
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => {
        const roleMap: Record<string, { text: string; color: string }> = {
          super_admin: { text: '超级管理员', color: 'red' },
          event_admin: { text: '活动管理员', color: 'orange' },
          booth_cashier: { text: '摊位收银员', color: 'blue' },
          issuer: { text: '充值员', color: 'green' },
          reviewer: { text: '审核员', color: 'purple' },
        }
        const config = roleMap[role] || { text: role, color: 'default' }
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '摊位ID',
      dataIndex: 'booth_id',
      key: 'booth_id',
      render: (id: number | null) => id || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
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
      width: 250,
      render: (_: any, record: User) => (
        <Space>
          {record.status === 'active' && (
            <>
              <Popconfirm
                title="确定禁用此用户吗？"
                onConfirm={() => handleUpdateStatus(record.id, 'inactive')}
                okText="确定"
                cancelText="取消"
              >
                <Button type="link" size="small">
                  禁用
                </Button>
              </Popconfirm>
              <Popconfirm
                title="确定冻结此用户吗？"
                onConfirm={() => handleUpdateStatus(record.id, 'blocked')}
                okText="确定"
                cancelText="取消"
              >
                <Button type="link" size="small" danger>
                  冻结
                </Button>
              </Popconfirm>
            </>
          )}
          {record.status !== 'active' && (
            <Popconfirm
              title="确定激活此用户吗？"
              onConfirm={() => handleUpdateStatus(record.id, 'active')}
              okText="确定"
              cancelText="取消"
            >
              <Button type="link" size="small">
                激活
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新建用户
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={users}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title="新建用户"
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="请输入用户名" />
          </Form.Item>

          <Form.Item
            name="password"
            label="密码"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6位' },
            ]}
          >
            <Input.Password placeholder="请输入密码" />
          </Form.Item>

          <Form.Item
            name="role"
            label="角色"
            rules={[{ required: true, message: '请选择角色' }]}
          >
            <Select placeholder="请选择角色">
              <Select.Option value="super_admin">超级管理员</Select.Option>
              <Select.Option value="event_admin">活动管理员</Select.Option>
              <Select.Option value="booth_cashier">摊位收银员</Select.Option>
              <Select.Option value="issuer">充值员</Select.Option>
              <Select.Option value="reviewer">审核员</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues.role !== currentValues.role
            }
          >
            {({ getFieldValue }) =>
              getFieldValue('role') === 'booth_cashier' ? (
                <>
                  <Form.Item
                    name="event_id_for_booth"
                    label="选择活动"
                    rules={[{ required: true, message: '请选择活动' }]}
                  >
                    <Select
                      placeholder="请选择活动"
                      onChange={(value) => {
                        setSelectedEventId(value)
                        form.setFieldValue('booth_id', undefined)
                      }}
                    >
                      {events.map((e) => (
                        <Select.Option key={e.id} value={e.id}>
                          {e.name}
                        </Select.Option>
                      ))}
                    </Select>
                  </Form.Item>
                  <Form.Item
                    name="booth_id"
                    label="分配摊位"
                    rules={[{ required: true, message: '请选择摊位' }]}
                  >
                    <Select placeholder="请选择摊位">
                      {booths.map((b) => (
                        <Select.Option key={b.id} value={b.id}>
                          {b.name}
                        </Select.Option>
                      ))}
                    </Select>
                  </Form.Item>
                </>
              ) : null
            }
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default UserManagement
