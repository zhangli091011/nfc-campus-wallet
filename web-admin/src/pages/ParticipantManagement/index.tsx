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
} from 'antd'
import { PlusOutlined, EditOutlined, DollarOutlined } from '@ant-design/icons'
import {
  getParticipants,
  createParticipant,
  updateParticipant,
  recharge,
  type Participant,
  type CreateParticipantRequest,
  type UpdateParticipantRequest,
  type RechargeRequest,
} from '@/services/participant'
import { getEvents, type Event } from '@/services/event'
import dayjs from 'dayjs'

const ParticipantManagement = () => {
  const [participants, setParticipants] = useState<Participant[]>([])
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [rechargeModalVisible, setRechargeModalVisible] = useState(false)
  const [editingParticipant, setEditingParticipant] = useState<Participant | null>(null)
  const [rechargingParticipant, setRechargingParticipant] = useState<Participant | null>(null)
  const [selectedEventId, setSelectedEventId] = useState<number>()
  const [form] = Form.useForm()
  const [rechargeForm] = Form.useForm()

  useEffect(() => {
    loadEvents()
  }, [])

  useEffect(() => {
    if (selectedEventId) {
      loadParticipants()
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

  const loadParticipants = async () => {
    if (!selectedEventId) return
    setLoading(true)
    try {
      const data = await getParticipants({ event_id: selectedEventId, limit: 100 })
      setParticipants(data)
    } catch (error) {
      // 错误已处理
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingParticipant(null)
    form.resetFields()
    form.setFieldsValue({ event_id: selectedEventId, status: 'active' })
    setModalVisible(true)
  }

  const handleEdit = (record: Participant) => {
    setEditingParticipant(record)
    form.setFieldsValue({
      event_id: record.event_id,
      card_uid: record.card_uid,
      name: record.name,
      student_id: record.student_id,
      class_name: record.class_name,
      status: record.status,
    })
    setModalVisible(true)
  }

  const handleRecharge = (record: Participant) => {
    setRechargingParticipant(record)
    rechargeForm.resetFields()
    setRechargeModalVisible(true)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      if (editingParticipant) {
        const data: UpdateParticipantRequest = {
          name: values.name,
          student_id: values.student_id,
          class_name: values.class_name,
          status: values.status,
        }
        await updateParticipant(editingParticipant.id, data)
        message.success('更新成功')
      } else {
        const data: CreateParticipantRequest = {
          event_id: values.event_id,
          card_uid: values.card_uid,
          name: values.name,
          student_id: values.student_id,
          class_name: values.class_name,
          initial_balance: values.initial_balance
            ? Math.round(values.initial_balance * 100)
            : 0,
        }
        await createParticipant(data)
        message.success('创建成功')
      }

      setModalVisible(false)
      loadParticipants()
    } catch (error) {
      // 错误已处理
    }
  }

  const handleRechargeSubmit = async () => {
    if (!rechargingParticipant) return
    try {
      const values = await rechargeForm.validateFields()
      const data: RechargeRequest = {
        event_id: rechargingParticipant.event_id,
        card_uid: rechargingParticipant.card_uid,
        amount: values.amount,
        remark: values.remark,
      }
      await recharge(data)
      message.success('充值成功')
      setRechargeModalVisible(false)
      loadParticipants()
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
      title: '卡号',
      dataIndex: 'card_uid',
      key: 'card_uid',
    },
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '学号',
      dataIndex: 'student_id',
      key: 'student_id',
    },
    {
      title: '班级',
      dataIndex: 'class_name',
      key: 'class_name',
    },
    {
      title: '余额',
      dataIndex: 'balance',
      key: 'balance',
      render: (balance: number) => `¥${(balance / 100).toFixed(2)}`,
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
      width: 180,
      render: (_: any, record: Participant) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<DollarOutlined />}
            onClick={() => handleRecharge(record)}
          >
            充值
          </Button>
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
      <Space style={{ marginBottom: 16 }}>
        <Select
          style={{ width: 200 }}
          placeholder="选择活动"
          value={selectedEventId}
          onChange={setSelectedEventId}
          options={events.map((e) => ({ label: e.name, value: e.id }))}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新建参与者
        </Button>
      </Space>

      <Table
        columns={columns}
        dataSource={participants}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title={editingParticipant ? '编辑参与者' : '新建参与者'}
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
            <Select disabled={!!editingParticipant}>
              {events.map((e) => (
                <Select.Option key={e.id} value={e.id}>
                  {e.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="card_uid"
            label="卡号"
            rules={[{ required: true, message: '请输入卡号' }]}
          >
            <Input placeholder="请输入卡号" disabled={!!editingParticipant} />
          </Form.Item>

          <Form.Item
            name="name"
            label="姓名"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input placeholder="请输入姓名" />
          </Form.Item>

          <Form.Item name="student_id" label="学号">
            <Input placeholder="请输入学号" />
          </Form.Item>

          <Form.Item name="class_name" label="班级">
            <Input placeholder="请输入班级" />
          </Form.Item>

          {!editingParticipant && (
            <Form.Item name="initial_balance" label="初始余额（元）">
              <InputNumber
                min={0}
                precision={2}
                style={{ width: '100%' }}
                placeholder="请输入初始余额"
              />
            </Form.Item>
          )}

          {editingParticipant && (
            <Form.Item
              name="status"
              label="状态"
              rules={[{ required: true, message: '请选择状态' }]}
            >
              <Select>
                <Select.Option value="active">正常</Select.Option>
                <Select.Option value="inactive">未激活</Select.Option>
                <Select.Option value="blocked">已冻结</Select.Option>
              </Select>
            </Form.Item>
          )}
        </Form>
      </Modal>

      <Modal
        title="充值"
        open={rechargeModalVisible}
        onOk={handleRechargeSubmit}
        onCancel={() => setRechargeModalVisible(false)}
        width={500}
      >
        <Form form={rechargeForm} layout="vertical">
          <Form.Item label="参与者信息">
            <div>
              <p>姓名：{rechargingParticipant?.name}</p>
              <p>卡号：{rechargingParticipant?.card_uid}</p>
              <p>
                当前余额：¥
                {rechargingParticipant
                  ? (rechargingParticipant.balance / 100).toFixed(2)
                  : '0.00'}
              </p>
            </div>
          </Form.Item>

          <Form.Item
            name="amount"
            label="充值金额（元）"
            rules={[{ required: true, message: '请输入充值金额' }]}
          >
            <InputNumber
              min={0.01}
              precision={2}
              style={{ width: '100%' }}
              placeholder="请输入充值金额"
            />
          </Form.Item>

          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={3} placeholder="请输入备注" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ParticipantManagement
