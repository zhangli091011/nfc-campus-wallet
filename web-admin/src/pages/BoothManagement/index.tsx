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
  Descriptions,
  Typography,
  Divider,
  List,
  Switch,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  KeyOutlined,
  UserAddOutlined,
  CopyOutlined,
} from '@ant-design/icons'
import {
  getBooths,
  createBooth,
  updateBooth,
  deleteBooth,
  getBoothCredentials,
  generateBoothCredentials,
  getBoothCashiers,
  assignCashierToBooth,
  updateBoothStockEnabled,
  type Booth,
  type CreateBoothRequest,
  type UpdateBoothRequest,
  type BoothCredential,
  type BoothCashier,
} from '@/services/booth'
import { getUsers } from '@/services/user'
import { getEvents, type Event } from '@/services/event'
import { User } from '@/utils/auth'
import dayjs from 'dayjs'

const { Text } = Typography

const BoothManagement = () => {
  const [booths, setBooths] = useState<Booth[]>([])
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingBooth, setEditingBooth] = useState<Booth | null>(null)
  const [selectedEventId, setSelectedEventId] = useState<number>()
  const [form] = Form.useForm()

  // 凭据相关状态
  const [credentialModalVisible, setCredentialModalVisible] = useState(false)
  const [currentCredential, setCurrentCredential] = useState<BoothCredential | null>(null)
  const [credentialLoading, setCredentialLoading] = useState(false)
  const [selectedBoothForCredential, setSelectedBoothForCredential] = useState<Booth | null>(null)

  // 收银员管理相关状态
  const [cashierModalVisible, setCashierModalVisible] = useState(false)
  const [cashiers, setCashiers] = useState<BoothCashier[]>([])
  const [allUsers, setAllUsers] = useState<User[]>([])
  const [selectedBoothForCashier, setSelectedBoothForCashier] = useState<Booth | null>(null)
  const [assignUserId, setAssignUserId] = useState<number>()

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
    setLoading(true)
    try {
      const data = await getBooths({ event_id: selectedEventId, limit: 100 })
      setBooths(Array.isArray(data) ? data : [])
    } catch (error) {
      setBooths([])
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

  const handleDeleteBooth = (record: Booth) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除摊位「${record.name}」吗？此操作不可撤销，关联的商品将被一并删除。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await deleteBooth(record.id)
          message.success('摊位已删除')
          loadBooths()
        } catch (error) {
          message.error('删除失败')
        }
      },
    })
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

  // ========== 凭据管理 ==========
  const handleViewCredentials = async (booth: Booth) => {
    setSelectedBoothForCredential(booth)
    setCredentialLoading(true)
    setCredentialModalVisible(true)
    try {
      const data = await getBoothCredentials(booth.id)
      setCurrentCredential(data)
    } catch (error) {
      setCurrentCredential(null)
    } finally {
      setCredentialLoading(false)
    }
  }

  const handleGenerateCredentials = async () => {
    if (!selectedBoothForCredential) return
    setCredentialLoading(true)
    try {
      const data = await generateBoothCredentials(selectedBoothForCredential.id)
      setCurrentCredential(data)
      message.success('凭据生成成功，请妥善保存密码！')
    } catch (error) {
      message.error('生成凭据失败')
    } finally {
      setCredentialLoading(false)
    }
  }

  const handleCopyCredentials = () => {
    if (!currentCredential) return
    const text = `用户名: ${currentCredential.username}\n密码: ${currentCredential.password || '(已隐藏)'}`
    navigator.clipboard.writeText(text).then(() => {
      message.success('已复制到剪贴板')
    }).catch(() => {
      message.error('复制失败')
    })
  }

  // ========== 收银员管理 ==========
  const handleManageCashiers = async (booth: Booth) => {
    setSelectedBoothForCashier(booth)
    setCashierModalVisible(true)
    try {
      const [cashierData, userData] = await Promise.all([
        getBoothCashiers(booth.id),
        getUsers({ limit: 100 }),
      ])
      setCashiers(Array.isArray(cashierData) ? cashierData : [])
      setAllUsers(Array.isArray(userData) ? userData : [])
    } catch (error) {
      setCashiers([])
      setAllUsers([])
    }
  }

  const handleAssignCashier = async () => {
    if (!selectedBoothForCashier || !assignUserId) return
    try {
      await assignCashierToBooth(selectedBoothForCashier.id, assignUserId)
      message.success('收银员分配成功')
      setAssignUserId(undefined)
      // 刷新收银员列表
      const cashierData = await getBoothCashiers(selectedBoothForCashier.id)
      setCashiers(Array.isArray(cashierData) ? cashierData : [])
    } catch (error) {
      message.error('分配失败')
    }
  }

  // ========== 股票参与控制 ==========
  const handleToggleStockEnabled = async (booth: Booth, enabled: boolean) => {
    try {
      const res = await updateBoothStockEnabled(booth.id, enabled)
      message.success(res.message || (enabled ? '已开启股票权限' : '已关闭股票权限'))
      loadBooths()
    } catch (error) {
      message.error('操作失败')
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
      title: '股票',
      dataIndex: 'stock_enabled',
      key: 'stock_enabled',
      width: 80,
      render: (stockEnabled: boolean, record: Booth) => (
        <Switch
          checked={stockEnabled !== false}
          size="small"
          onChange={(checked) => handleToggleStockEnabled(record, checked)}
        />
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
      width: 340,
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
          <Button
            type="link"
            size="small"
            icon={<KeyOutlined />}
            onClick={() => handleViewCredentials(record)}
          >
            凭据
          </Button>
          <Button
            type="link"
            size="small"
            icon={<UserAddOutlined />}
            onClick={() => handleManageCashiers(record)}
          >
            收银员
          </Button>
          <Button
            type="link"
            size="small"
            danger
            onClick={() => handleDeleteBooth(record)}
          >
            删除
          </Button>
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

      {/* 新建/编辑摊位 Modal */}
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

      {/* 凭据管理 Modal */}
      <Modal
        title={`摊位凭据 - ${selectedBoothForCredential?.name || ''}`}
        open={credentialModalVisible}
        onCancel={() => {
          setCredentialModalVisible(false)
          setCurrentCredential(null)
        }}
        footer={[
          <Button key="close" onClick={() => {
            setCredentialModalVisible(false)
            setCurrentCredential(null)
          }}>
            关闭
          </Button>,
          currentCredential?.password && (
            <Button key="copy" icon={<CopyOutlined />} onClick={handleCopyCredentials}>
              复制凭据
            </Button>
          ),
          <Button
            key="generate"
            type="primary"
            icon={<KeyOutlined />}
            loading={credentialLoading}
            onClick={handleGenerateCredentials}
          >
            {currentCredential?.user_id ? '重置密码' : '生成凭据'}
          </Button>,
        ]}
        width={500}
      >
        {credentialLoading ? (
          <div style={{ textAlign: 'center', padding: 20 }}>加载中...</div>
        ) : currentCredential ? (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="摊位">{currentCredential.booth_name}</Descriptions.Item>
            <Descriptions.Item label="登录账号">
              {currentCredential.username ? (
                <Text strong copyable>{currentCredential.username}</Text>
              ) : (
                <Text type="secondary">未生成</Text>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="密码">
              {currentCredential.password ? (
                <Text strong copyable type="success">{currentCredential.password}</Text>
              ) : currentCredential.username ? (
                <Text type="secondary">已隐藏（点击"重置密码"可重新生成）</Text>
              ) : (
                <Text type="secondary">未生成</Text>
              )}
            </Descriptions.Item>
            {currentCredential.user_status && (
              <Descriptions.Item label="账号状态">
                <Tag color={currentCredential.user_status === 'active' ? 'success' : 'default'}>
                  {currentCredential.user_status === 'active' ? '正常' : currentCredential.user_status}
                </Tag>
              </Descriptions.Item>
            )}
          </Descriptions>
        ) : (
          <div style={{ textAlign: 'center', padding: 20 }}>
            <Text type="secondary">该摊位尚未生成登录凭据</Text>
          </div>
        )}
        {currentCredential?.password && (
          <div style={{ marginTop: 12, padding: 8, background: '#fff7e6', borderRadius: 4 }}>
            <Text type="warning">⚠️ 密码仅显示一次，请妥善保存！关闭后将无法再次查看。</Text>
          </div>
        )}
      </Modal>

      {/* 收银员管理 Modal */}
      <Modal
        title={`收银员管理 - ${selectedBoothForCashier?.name || ''}`}
        open={cashierModalVisible}
        onCancel={() => {
          setCashierModalVisible(false)
          setCashiers([])
          setAssignUserId(undefined)
        }}
        footer={[
          <Button key="close" onClick={() => {
            setCashierModalVisible(false)
            setCashiers([])
            setAssignUserId(undefined)
          }}>
            关闭
          </Button>,
        ]}
        width={600}
      >
        <Divider orientation="left">当前收银员</Divider>
        {cashiers.length > 0 ? (
          <List
            size="small"
            dataSource={cashiers}
            renderItem={(item) => (
              <List.Item>
                <Space>
                  <Text strong>{item.username}</Text>
                  <Tag color={item.status === 'active' ? 'success' : 'default'}>
                    {item.status === 'active' ? '正常' : item.status}
                  </Tag>
                  <Text type="secondary">
                    创建于 {dayjs(item.created_at).format('YYYY-MM-DD')}
                  </Text>
                </Space>
              </List.Item>
            )}
          />
        ) : (
          <Text type="secondary">暂无收银员</Text>
        )}

        <Divider orientation="left">指定收银员</Divider>
        <Space>
          <Select
            style={{ width: 300 }}
            placeholder="选择用户"
            value={assignUserId}
            onChange={setAssignUserId}
            showSearch
            optionFilterProp="label"
            options={allUsers
              .filter((u) => u.role !== 'super_admin')
              .map((u) => ({
                label: `${u.username} (${u.role})`,
                value: u.id,
              }))}
          />
          <Button
            type="primary"
            icon={<UserAddOutlined />}
            disabled={!assignUserId}
            onClick={handleAssignCashier}
          >
            分配
          </Button>
        </Space>
      </Modal>
    </div>
  )
}

export default BoothManagement
