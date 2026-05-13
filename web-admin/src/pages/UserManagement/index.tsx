import { useState, useEffect } from 'react'
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  message,
  Tag,
  Popconfirm,
  Badge,
  Tooltip,
  Alert,
  Typography,
  Divider,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  BankOutlined,
  CrownOutlined,
  SafetyCertificateOutlined,
  TeamOutlined,
  DownloadOutlined,
} from '@ant-design/icons'
import {
  getUsers,
  createUser,
  updateUserStatus,
  updateUserBooth,
  updateUserRole,
  type CreateUserRequest,
} from '@/services/user'
import { getBooths, type Booth } from '@/services/booth'
import { getEvents, type Event } from '@/services/event'
import request from '@/utils/request'
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

  // 分配摊位相关状态
  const [boothModalVisible, setBoothModalVisible] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [boothEventId, setBoothEventId] = useState<number>()
  const [boothOptions, setBoothOptions] = useState<Booth[]>([])

  // 角色编辑相关状态
  const [roleModalVisible, setRoleModalVisible] = useState(false)
  const [roleEditingUser, setRoleEditingUser] = useState<User | null>(null)
  const [roleForm] = Form.useForm()
  const [roleEventId, setRoleEventId] = useState<number>()
  const [roleBoothOptions, setRoleBoothOptions] = useState<Booth[]>([])

  // 批量创建收银员相关状态
  const [batchModalVisible, setBatchModalVisible] = useState(false)
  const [batchResultVisible, setBatchResultVisible] = useState(false)
  const [batchResult, setBatchResult] = useState<{
    total_created: number
    accounts: Array<{
      user_id: number
      username: string
      password: string
      booth_id: number
      booth_name: string
    }>
    errors: string[]
  } | null>(null)
  const [batchForm] = Form.useForm()
  const [batchLoading, setBatchLoading] = useState(false)
  const [allBooths, setAllBooths] = useState<Booth[]>([])
  const [allBoothsLoading, setAllBoothsLoading] = useState(false)

  useEffect(() => {
    loadUsers()
    loadEvents()
  }, [])

  useEffect(() => {
    if (selectedEventId) {
      loadBooths()
    }
  }, [selectedEventId])

  useEffect(() => {
    if (boothEventId) {
      loadBoothOptions()
    }
  }, [boothEventId])

  useEffect(() => {
    if (roleEventId) {
      loadRoleBoothOptions()
    }
  }, [roleEventId])

  const loadUsers = async () => {
    setLoading(true)
    try {
      const data = await getUsers({ limit: 100 })
      setUsers(Array.isArray(data) ? data : [])
    } catch (error) {
      setUsers([])
    } finally {
      setLoading(false)
    }
  }

  const loadEvents = async () => {
    try {
      const data = await getEvents()
      const eventList = data?.events || []
      setEvents(eventList)
      if (eventList.length > 0) {
        setSelectedEventId(eventList[0].id)
      }
    } catch (error) {
      setEvents([])
    }
  }

  const loadBooths = async () => {
    if (!selectedEventId) return
    try {
      const data = await getBooths({ event_id: selectedEventId, limit: 100 })
      setBooths(Array.isArray(data) ? data : [])
    } catch (error) {
      setBooths([])
    }
  }

  const loadBoothOptions = async () => {
    if (!boothEventId) return
    try {
      const data = await getBooths({ event_id: boothEventId, limit: 100 })
      setBoothOptions(Array.isArray(data) ? data : [])
    } catch (error) {
      setBoothOptions([])
    }
  }

  const loadRoleBoothOptions = async () => {
    if (!roleEventId) return
    try {
      const data = await getBooths({ event_id: roleEventId, limit: 100 })
      setRoleBoothOptions(Array.isArray(data) ? data : [])
    } catch (error) {
      setRoleBoothOptions([])
    }
  }

  // 加载所有活动的所有摊位（批量创建收银员用）
  const loadAllBooths = async () => {
    setAllBoothsLoading(true)
    try {
      // 获取所有活动的摊位
      const allBoothsList: Booth[] = []
      for (const event of events) {
        const data = await getBooths({ event_id: event.id, limit: 500 })
        const eventBooths = Array.isArray(data) ? data : []
        allBoothsList.push(...eventBooths)
      }
      // 如果没有活动，尝试不带 event_id 获取
      if (events.length === 0) {
        const data = await getBooths({ limit: 500 })
        const fallbackBooths = Array.isArray(data) ? data : []
        allBoothsList.push(...fallbackBooths)
      }
      // 去重（按 id）
      const uniqueBooths = allBoothsList.filter(
        (booth, index, self) => self.findIndex(b => b.id === booth.id) === index
      )
      setAllBooths(uniqueBooths)
    } catch (error) {
      setAllBooths([])
    } finally {
      setAllBoothsLoading(false)
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

  // ========== 分配摊位 ==========
  const handleAssignBooth = (record: User) => {
    setEditingUser(record)
    setBoothModalVisible(true)
    if (events.length > 0) {
      setBoothEventId(events[0].id)
    }
  }

  const handleBoothAssignSubmit = async (boothId: number | null) => {
    if (!editingUser) return
    try {
      await updateUserBooth(editingUser.id, boothId)
      message.success('摊位分配成功')
      setBoothModalVisible(false)
      setEditingUser(null)
      loadUsers()
    } catch (error) {
      message.error('分配失败')
    }
  }

  // ========== 角色编辑 ==========
  const handleEditRole = (record: User) => {
    setRoleEditingUser(record)
    roleForm.setFieldsValue({ role: record.role })
    setRoleModalVisible(true)
    if (events.length > 0) {
      setRoleEventId(events[0].id)
    }
  }

  const handleRoleSubmit = async () => {
    if (!roleEditingUser) return
    try {
      const values = await roleForm.validateFields()
      const boothId = values.role === 'booth_cashier' ? values.booth_id : null
      await updateUserRole(roleEditingUser.id, values.role, boothId)
      message.success('角色更新成功')
      setRoleModalVisible(false)
      setRoleEditingUser(null)
      loadUsers()
    } catch (error) {
      // 错误已处理
    }
  }

  // ========== 批量创建收银员 ==========
  const handleBatchSubmit = async () => {
    try {
      const values = await batchForm.validateFields()
      setBatchLoading(true)
      const res = await request.post<any, any>('/users/batch-create-cashiers', {
        booth_ids: values.booth_ids,
        accounts_per_booth: values.accounts_per_booth || 1,
        username_prefix: values.username_prefix || 'cashier',
        password_length: values.password_length || 8,
      })
      setBatchResult(res)
      setBatchModalVisible(false)
      setBatchResultVisible(true)
      batchForm.resetFields()
      loadUsers()
      message.success(`成功创建 ${res.total_created} 个收银员账号`)
    } catch (error: any) {
      message.error(error?.response?.data?.message || '批量创建失败')
    } finally {
      setBatchLoading(false)
    }
  }

  // 导出账号信息为CSV
  const exportBatchResult = () => {
    if (!batchResult || !batchResult.accounts.length) return
    const header = ['用户名', '密码', '摊位ID', '摊位名称']
    const rows = batchResult.accounts.map(a => [
      a.username,
      a.password,
      a.booth_id.toString(),
      a.booth_name,
    ])
    const csv = '\ufeff' + [header, ...rows].map(row => 
      row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(',')
    ).join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `cashier_accounts_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
    message.success('导出成功')
  }

  // ========== 判断是否为特殊用户 ==========
  const isBankClerk = (record: User) => record.role === 'bank_clerk'

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
      render: (username: string, record: User) => {
        if (isBankClerk(record)) {
          return (
            <Space>
              <BankOutlined style={{ color: '#d4a017', fontSize: 16 }} />
              <span style={{ fontWeight: 600, color: '#8b6914' }}>{username}</span>
              <Tag color="gold" style={{ marginLeft: 4, fontSize: 10, lineHeight: '16px', padding: '0 4px' }}>
                特殊账户
              </Tag>
            </Space>
          )
        }
        return username
      },
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role: string, record: User) => {
        const roleMap: Record<string, { text: string; color: string; icon?: React.ReactNode }> = {
          super_admin: { text: '超级管理员', color: 'red', icon: <CrownOutlined /> },
          event_admin: { text: '活动管理员', color: 'orange' },
          booth_cashier: { text: '摊位收银员', color: 'blue' },
          issuer: { text: '充值员', color: 'green' },
          reviewer: { text: '审核员', color: 'purple' },
          bank_clerk: { text: '投资办理员', color: 'gold', icon: <BankOutlined /> },
          school_inspector: { text: '校方巡查', color: 'cyan', icon: <SafetyCertificateOutlined /> },
        }
        const config = roleMap[role] || { text: role, color: 'default' }
        if (isBankClerk(record)) {
          return (
            <Badge dot color="#d4a017" offset={[4, 0]}>
              <Tag
                color={config.color}
                icon={config.icon}
                style={{ fontWeight: 600, border: '1px solid #d4a017' }}
              >
                {config.text}
              </Tag>
            </Badge>
          )
        }
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        )
      },
    },
    {
      title: '关联摊位',
      dataIndex: 'booth_id',
      key: 'booth_id',
      render: (id: number | null, record: User) => {
        if (!id) return <Tag>无</Tag>
        const booth = booths.find((b) => b.id === id)
        if (isBankClerk(record)) {
          return booth ? (
            <Tooltip title="投资办理专用摊位（官方中央银行）">
              <Tag color="gold" icon={<BankOutlined />}>
                {booth.name} (ID:{id})
              </Tag>
            </Tooltip>
          ) : (
            <Tag color="gold">ID:{id}</Tag>
          )
        }
        return booth ? <Tag color="blue">{booth.name} (ID:{id})</Tag> : <Tag>ID:{id}</Tag>
      },
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
      width: 360,
      render: (_: any, record: User) => (
        <Space>
          <Tooltip title="修改角色">
            <Button
              type="link"
              size="small"
              icon={<SafetyCertificateOutlined />}
              onClick={() => handleEditRole(record)}
            >
              角色
            </Button>
          </Tooltip>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleAssignBooth(record)}
          >
            分配摊位
          </Button>
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

  // 对用户列表排序：bank_clerk 排在前面（特殊用户置顶）
  const sortedUsers = [...users].sort((a, b) => {
    if (a.role === 'bank_clerk' && b.role !== 'bank_clerk') return -1
    if (a.role !== 'bank_clerk' && b.role === 'bank_clerk') return 1
    if (a.role === 'super_admin' && b.role !== 'super_admin') return -1
    if (a.role !== 'super_admin' && b.role === 'super_admin') return 1
    return a.id - b.id
  })

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            新建用户
          </Button>
          <Button icon={<TeamOutlined />} onClick={() => { loadAllBooths(); setBatchModalVisible(true) }}>
            批量创建收银员
          </Button>
        </Space>
        <Alert
          message="特殊账户说明"
          description="带有 🏦 标记的「投资办理员」为系统特殊账户，用于官方中央银行投资办理终端，拥有独立的权限体系。"
          type="warning"
          showIcon
          style={{ marginLeft: 16, flex: 1, marginBottom: 0 }}
          banner
        />
      </div>

      <Table
        columns={columns}
        dataSource={sortedUsers}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
        rowClassName={(record) => {
          if (isBankClerk(record)) return 'bank-clerk-row'
          if (record.role === 'school_inspector') return 'school-inspector-row'
          return ''
        }}
      />

      {/* 新建用户 Modal */}
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
              <Select.Option value="bank_clerk">
                <Space>
                  <BankOutlined style={{ color: '#d4a017' }} />
                  <span>投资办理员（特殊）</span>
                </Space>
              </Select.Option>
              <Select.Option value="school_inspector">
                <Space>
                  <SafetyCertificateOutlined style={{ color: '#13c2c2' }} />
                  <span>校方巡查（只读）</span>
                </Space>
              </Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues.role !== currentValues.role
            }
          >
            {({ getFieldValue }) => {
              const role = getFieldValue('role')
              if (role === 'booth_cashier') {
                return (
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
                )
              }
              if (role === 'bank_clerk') {
                return (
                  <Alert
                    message="投资办理员说明"
                    description="该角色为系统特殊账户，用于官方中央银行投资办理终端。创建后将自动拥有投资相关的摊位查看和股票操作权限。"
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                )
              }
              if (role === 'school_inspector') {
                return (
                  <Alert
                    message="校方巡查说明"
                    description="该角色仅拥有只读查看权限，可以浏览所有后台数据（报表、交易流水、参与者余额、班级搜索等），但无法修改任何数据。"
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                )
              }
              return null
            }}
          </Form.Item>
        </Form>
      </Modal>

      {/* 分配摊位 Modal */}
      <Modal
        title={`分配摊位 - ${editingUser?.username || ''}`}
        open={boothModalVisible}
        onCancel={() => {
          setBoothModalVisible(false)
          setEditingUser(null)
        }}
        footer={[
          <Button
            key="unassign"
            danger
            onClick={() => handleBoothAssignSubmit(null)}
            disabled={!editingUser?.booth_id}
          >
            取消摊位关联
          </Button>,
          <Button key="cancel" onClick={() => {
            setBoothModalVisible(false)
            setEditingUser(null)
          }}>
            关闭
          </Button>,
        ]}
        width={500}
      >
        <div style={{ marginBottom: 16 }}>
          <p>当前摊位: {editingUser?.booth_id ? `ID ${editingUser.booth_id}` : '无'}</p>
        </div>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Select
            style={{ width: '100%' }}
            placeholder="选择活动"
            value={boothEventId}
            onChange={(val) => {
              setBoothEventId(val)
            }}
            options={events.map((e) => ({ label: e.name, value: e.id }))}
          />
          <Space style={{ width: '100%' }}>
            <Select
              style={{ width: 300 }}
              placeholder="选择摊位"
              showSearch
              optionFilterProp="label"
              options={boothOptions.map((b) => ({
                label: `${b.name} (${b.class_name})`,
                value: b.id,
              }))}
              onChange={(val) => handleBoothAssignSubmit(val)}
            />
          </Space>
        </Space>
      </Modal>

      {/* 角色编辑 Modal */}
      <Modal
        title={
          <Space>
            <SafetyCertificateOutlined />
            <span>修改角色 - {roleEditingUser?.username || ''}</span>
            {roleEditingUser && isBankClerk(roleEditingUser) && (
              <Tag color="gold" icon={<BankOutlined />}>特殊账户</Tag>
            )}
          </Space>
        }
        open={roleModalVisible}
        onOk={handleRoleSubmit}
        onCancel={() => {
          setRoleModalVisible(false)
          setRoleEditingUser(null)
        }}
        width={550}
      >
        {roleEditingUser && isBankClerk(roleEditingUser) && (
          <Alert
            message="注意：这是一个特殊系统账户"
            description="投资办理员账户用于官方中央银行终端。修改其角色可能影响投资办理功能的正常运行。"
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}
        <Form form={roleForm} layout="vertical">
          <Form.Item
            name="role"
            label="新角色"
            rules={[{ required: true, message: '请选择角色' }]}
          >
            <Select placeholder="请选择角色">
              <Select.Option value="super_admin">超级管理员</Select.Option>
              <Select.Option value="event_admin">活动管理员</Select.Option>
              <Select.Option value="booth_cashier">摊位收银员</Select.Option>
              <Select.Option value="issuer">充值员</Select.Option>
              <Select.Option value="reviewer">审核员</Select.Option>
              <Select.Option value="bank_clerk">
                <Space>
                  <BankOutlined style={{ color: '#d4a017' }} />
                  <span>投资办理员（特殊）</span>
                </Space>
              </Select.Option>
              <Select.Option value="school_inspector">
                <Space>
                  <SafetyCertificateOutlined style={{ color: '#13c2c2' }} />
                  <span>校方巡查（只读）</span>
                </Space>
              </Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues.role !== currentValues.role
            }
          >
            {({ getFieldValue }) => {
              const role = getFieldValue('role')
              if (role === 'booth_cashier') {
                return (
                  <>
                    <Form.Item
                      name="event_id_for_role_booth"
                      label="选择活动"
                    >
                      <Select
                        placeholder="请选择活动"
                        onChange={(value) => {
                          setRoleEventId(value)
                          roleForm.setFieldValue('booth_id', undefined)
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
                        {roleBoothOptions.map((b) => (
                          <Select.Option key={b.id} value={b.id}>
                            {b.name} ({b.class_name})
                          </Select.Option>
                        ))}
                      </Select>
                    </Form.Item>
                  </>
                )
              }
              if (role === 'bank_clerk') {
                return (
                  <Alert
                    message="投资办理员说明"
                    description="该角色为系统特殊账户，用于官方中央银行投资办理终端。设置后将自动拥有投资相关权限。"
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                )
              }
              if (role === 'school_inspector') {
                return (
                  <Alert
                    message="校方巡查说明"
                    description="该角色仅拥有只读查看权限，可以浏览所有后台数据（报表、交易流水、参与者余额、班级搜索等），但无法修改任何数据。"
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                )
              }
              return null
            }}
          </Form.Item>
        </Form>
      </Modal>

      {/* 特殊行样式 */}
      <style>{`
        .bank-clerk-row {
          background: linear-gradient(90deg, #fffbe6 0%, #fff 40%) !important;
          border-left: 3px solid #d4a017 !important;
        }
        .bank-clerk-row:hover > td {
          background: #fff8e1 !important;
        }
        .bank-clerk-row > td {
          background: transparent !important;
        }
        .school-inspector-row {
          background: linear-gradient(90deg, #e6fffb 0%, #fff 40%) !important;
          border-left: 3px solid #13c2c2 !important;
        }
        .school-inspector-row:hover > td {
          background: #e6fffb !important;
        }
        .school-inspector-row > td {
          background: transparent !important;
        }
      `}</style>

      {/* 批量创建收银员 Modal */}
      <Modal
        title="批量创建收银员账号"
        open={batchModalVisible}
        onOk={handleBatchSubmit}
        onCancel={() => setBatchModalVisible(false)}
        okText="创建"
        confirmLoading={batchLoading}
        width={600}
      >
        <Form form={batchForm} layout="vertical" initialValues={{ accounts_per_booth: 1, username_prefix: 'cashier', password_length: 8 }}>
          <Form.Item
            name="booth_ids"
            label="选择摊位（可多选，已加载所有活动的摊位）"
            rules={[{ required: true, message: '请选择至少一个摊位' }]}
          >
            <Select
              mode="multiple"
              placeholder={allBoothsLoading ? '加载摊位中...' : '选择要分配收银员的摊位'}
              loading={allBoothsLoading}
              options={allBooths.map(b => ({ label: `${b.name}${b.class_name ? ` (${b.class_name})` : ''} [ID:${b.id}]`, value: b.id }))}
              filterOption={(input, option) =>
                (option?.label as string)?.toLowerCase().includes(input.toLowerCase())
              }
            />
          </Form.Item>
          <Space size="large">
            <Form.Item name="accounts_per_booth" label="每摊位账号数">
              <InputNumber min={1} max={10} />
            </Form.Item>
            <Form.Item name="password_length" label="密码长度">
              <InputNumber min={6} max={20} />
            </Form.Item>
          </Space>
          <Form.Item name="username_prefix" label="用户名前缀">
            <Input placeholder="cashier" style={{ width: 200 }} />
          </Form.Item>
          <Alert
            message="说明"
            description="系统将为每个选中的摊位自动创建收银员账号，用户名格式为：前缀_b摊位ID。密码随机生成，创建后可导出CSV。"
            type="info"
            showIcon
          />
        </Form>
      </Modal>

      {/* 批量创建结果 Modal */}
      <Modal
        title={`创建完成 - 共 ${batchResult?.total_created || 0} 个账号`}
        open={batchResultVisible}
        onCancel={() => setBatchResultVisible(false)}
        width={700}
        footer={[
          <Button key="export" type="primary" icon={<DownloadOutlined />} onClick={exportBatchResult}>
            导出 CSV
          </Button>,
          <Button key="close" onClick={() => setBatchResultVisible(false)}>
            关闭
          </Button>,
        ]}
      >
        {batchResult && (
          <>
            {batchResult.errors.length > 0 && (
              <Alert
                message={`${batchResult.errors.length} 个账号创建失败`}
                description={batchResult.errors.join('\n')}
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}
            <Table
              dataSource={batchResult.accounts}
              rowKey="user_id"
              size="small"
              pagination={false}
              scroll={{ y: 400 }}
              columns={[
                { title: '用户名', dataIndex: 'username', key: 'username' },
                { title: '密码', dataIndex: 'password', key: 'password', render: (p: string) => <Typography.Text code copyable>{p}</Typography.Text> },
                { title: '摊位', dataIndex: 'booth_name', key: 'booth_name' },
                { title: '摊位ID', dataIndex: 'booth_id', key: 'booth_id', width: 80 },
              ]}
            />
            <Divider />
            <Typography.Text type="secondary">
              ⚠️ 密码仅显示一次，请立即导出保存。关闭此窗口后无法再次查看密码。
            </Typography.Text>
          </>
        )}
      </Modal>
    </div>
  )
}

export default UserManagement
