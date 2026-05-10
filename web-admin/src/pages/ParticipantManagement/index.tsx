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
import { PlusOutlined, EditOutlined, DollarOutlined, SafetyCertificateOutlined } from '@ant-design/icons'
import {
  getParticipants,
  createParticipant,
  updateParticipant,
  verifyParticipant,
  recharge,
  type Participant,
  type CreateParticipantRequest,
  type UpdateParticipantRequest,
  type VerifyParticipantRequest,
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
  const [verifyModalVisible, setVerifyModalVisible] = useState(false)
  const [editingParticipant, setEditingParticipant] = useState<Participant | null>(null)
  const [rechargingParticipant, setRechargingParticipant] = useState<Participant | null>(null)
  const [verifyingParticipant, setVerifyingParticipant] = useState<Participant | null>(null)
  const [selectedEventId, setSelectedEventId] = useState<number>()
  const [form] = Form.useForm()
  const [rechargeForm] = Form.useForm()
  const [verifyForm] = Form.useForm()

  useEffect(() => {
    loadEvents()
    loadParticipants() // 直接加载所有参与者
  }, [])

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

  const loadParticipants = async () => {
    setLoading(true)
    try {
      const data = await getParticipants({ limit: 1000 })
      // 处理返回的数据格式
      if (Array.isArray(data)) {
        setParticipants(data)
      } else if (data && typeof data === 'object' && 'participants' in data) {
        setParticipants((data as any).participants || [])
      } else {
        setParticipants([])
      }
    } catch (error) {
      // 错误已处理
      setParticipants([])
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingParticipant(null)
    form.resetFields()
    form.setFieldsValue({ status: 'active' })
    setModalVisible(true)
  }

  const handleEdit = (record: Participant) => {
    setEditingParticipant(record)
    form.setFieldsValue({
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

  const handleVerify = (record: Participant) => {
    setVerifyingParticipant(record)
    verifyForm.resetFields()
    verifyForm.setFieldsValue({
      name: record.is_verified ? record.name : '',
      class_name: record.class_name || '',
      student_no: record.student_no || record.student_id || '',
    })
    setVerifyModalVisible(true)
  }

  const handleVerifySubmit = async () => {
    if (!verifyingParticipant) return
    try {
      const values = await verifyForm.validateFields()
      if (!values.class_name?.trim() && !values.student_no?.trim()) {
        message.error('班级与学号至少填写一项才能完成实名审核')
        return
      }
      const data: VerifyParticipantRequest = {
        name: values.name,
        class_name: values.class_name,
        student_no: values.student_no,
      }
      await verifyParticipant(verifyingParticipant.id, data)
      message.success('实名审核通过')
      setVerifyModalVisible(false)
      loadParticipants()
    } catch (error) {
      // 错误已处理
    }
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
          card_uid: values.card_uid,
          name: values.name,
          student_id: values.student_id,
          class_name: values.class_name,
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
    if (!rechargingParticipant || !selectedEventId) return
    try {
      const values = await rechargeForm.validateFields()
      const data: RechargeRequest = {
        event_id: selectedEventId,
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
      dataIndex: 'display_name',
      key: 'display_name',
      render: (text: string, record: any) => (
        record.is_verified
          ? <span>{text || record.name}</span>
          : <Tag color="warning">审核中</Tag>
      ),
    },
    {
      title: '学号',
      dataIndex: 'student_no',
      key: 'student_no',
      render: (text: string, record: any) => text || record.student_id || '-',
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
      width: 260,
      render: (_: any, record: Participant) => (
        <Space>
          {!record.is_verified && (
            <Button
              type="link"
              size="small"
              icon={<SafetyCertificateOutlined />}
              onClick={() => handleVerify(record)}
              style={{ color: '#fa8c16' }}
            >
              审核
            </Button>
          )}
          {selectedEventId && (
            <Button
              type="link"
              size="small"
              icon={<DollarOutlined />}
              onClick={() => handleRecharge(record)}
            >
              充值
            </Button>
          )}
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
          placeholder="选择活动（充值用）"
          value={selectedEventId}
          onChange={setSelectedEventId}
          options={events.map((e) => ({ label: e.name, value: e.id }))}
          allowClear
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

      <Modal
        title="实名审核"
        open={verifyModalVisible}
        onOk={handleVerifySubmit}
        onCancel={() => setVerifyModalVisible(false)}
        okText="通过审核"
        width={500}
      >
        <Form form={verifyForm} layout="vertical">
          <Form.Item label="卡号">
            <Input value={verifyingParticipant?.card_uid} disabled />
          </Form.Item>

          <Form.Item
            name="name"
            label="姓名"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input placeholder="请输入真实姓名" />
          </Form.Item>

          <Form.Item
            name="class_name"
            label="班级"
            extra="班级与学号至少填写一项"
          >
            <Input placeholder="请输入班级" />
          </Form.Item>

          <Form.Item name="student_no" label="学号">
            <Input placeholder="请输入学号" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ParticipantManagement
