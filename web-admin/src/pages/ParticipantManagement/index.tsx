import { useState, useEffect, useCallback } from 'react'
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
import { PlusOutlined, EditOutlined, DollarOutlined, SafetyCertificateOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons'
import {
  createParticipant,
  updateParticipant,
  verifyParticipant,
  recharge,
  deleteParticipant,
  clearAllParticipants,
  type Participant,
  type CreateParticipantRequest,
  type UpdateParticipantRequest,
  type VerifyParticipantRequest,
  type RechargeRequest,
} from '@/services/participant'
import { getEvents, type Event } from '@/services/event'
import request from '@/utils/request'
import dayjs from 'dayjs'

interface ParticipantWithBalance extends Participant {
  balance?: number
  credit_borrowed?: number
  credit_fee_paid?: number
}

const ParticipantManagement = () => {
  const [participants, setParticipants] = useState<ParticipantWithBalance[]>([])
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [rechargeModalVisible, setRechargeModalVisible] = useState(false)
  const [verifyModalVisible, setVerifyModalVisible] = useState(false)
  const [editingParticipant, setEditingParticipant] = useState<ParticipantWithBalance | null>(null)
  const [rechargingParticipant, setRechargingParticipant] = useState<ParticipantWithBalance | null>(null)
  const [verifyingParticipant, setVerifyingParticipant] = useState<ParticipantWithBalance | null>(null)
  const [selectedEventId, setSelectedEventId] = useState<number>()
  const [searchText, setSearchText] = useState('')
  const [totalCount, setTotalCount] = useState(0)
  const [form] = Form.useForm()
  const [rechargeForm] = Form.useForm()
  const [verifyForm] = Form.useForm()

  useEffect(() => {
    loadEvents()
  }, [])

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

  const loadParticipants = useCallback(async () => {
    setLoading(true)
    try {
      if (selectedEventId) {
        // 使用 admin 接口获取带余额的参与者列表，支持搜索
        const res = await request.get<any, any>('/admin/participants/balances', {
          params: {
            event_id: selectedEventId,
            search: searchText || undefined,
            sort_by: 'balance_desc',
            limit: 1000,
          },
        })
        setParticipants(res.participants || [])
        setTotalCount(res.total_count || 0)
      } else {
        // 没有选择活动时，使用基础接口
        const res = await request.get<any, any>('/participants', {
          params: { limit: 1000 },
        })
        if (Array.isArray(res)) {
          setParticipants(res)
          setTotalCount(res.length)
        } else if (res && typeof res === 'object' && 'participants' in res) {
          setParticipants(res.participants || [])
          setTotalCount(res.total_count || res.participants?.length || 0)
        } else {
          setParticipants([])
          setTotalCount(0)
        }
      }
    } catch (error) {
      setParticipants([])
      setTotalCount(0)
    } finally {
      setLoading(false)
    }
  }, [selectedEventId, searchText])

  useEffect(() => {
    loadParticipants()
  }, [loadParticipants])

  const handleSearch = (value: string) => {
    setSearchText(value)
  }

  const handleAdd = () => {
    setEditingParticipant(null)
    form.resetFields()
    form.setFieldsValue({ status: 'active' })
    setModalVisible(true)
  }

  const handleEdit = (record: ParticipantWithBalance) => {
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

  const handleDeleteParticipant = (record: ParticipantWithBalance) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除用户「${record.name || record.card_uid}」吗？此操作不可撤销，关联的账户数据将被一并删除。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await deleteParticipant(record.id)
          message.success('用户已删除')
          loadParticipants()
        } catch (error) {
          message.error('删除失败')
        }
      },
    })
  }

  const handleClearAll = () => {
    Modal.confirm({
      title: '⚠️ 危险操作：清除所有参与者',
      content: (
        <div>
          <p style={{ color: '#ff4d4f', fontWeight: 'bold' }}>
            此操作将永久删除所有参与者及其关联的账户数据！
          </p>
          <p>• 所有参与者记录将被删除</p>
          <p>• 所有账户余额将被清零并删除</p>
          <p>• 交易记录将保留用于审计</p>
          <p style={{ marginTop: 8, color: '#faad14' }}>此操作不可撤销，请确认！</p>
        </div>
      ),
      okText: '确认清除全部',
      okType: 'danger',
      cancelText: '取消',
      width: 480,
      onOk: async () => {
        try {
          const result = await clearAllParticipants()
          message.success(result?.message || '已清除所有参与者')
          loadParticipants()
        } catch (error) {
          message.error('清除失败，请重试')
        }
      },
    })
  }

  const handleRecharge = (record: ParticipantWithBalance) => {
    setRechargingParticipant(record)
    rechargeForm.resetFields()
    setRechargeModalVisible(true)
  }

  const handleVerify = (record: ParticipantWithBalance) => {
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
      width: 70,
    },
    {
      title: '卡号',
      dataIndex: 'card_uid',
      key: 'card_uid',
      width: 140,
    },
    {
      title: '姓名',
      dataIndex: 'display_name',
      key: 'display_name',
      width: 120,
      render: (text: string, record: any) => (
        record.is_verified || record.name
          ? <span>{text || record.name}</span>
          : <Tag color="warning">审核中</Tag>
      ),
    },
    {
      title: '学号',
      dataIndex: 'student_no',
      key: 'student_no',
      width: 120,
      render: (text: string, record: any) => text || record.student_id || '-',
    },
    {
      title: '班级',
      dataIndex: 'class_name',
      key: 'class_name',
      width: 120,
      render: (text: string) => text || '-',
    },
    {
      title: '余额（元）',
      dataIndex: 'balance',
      key: 'balance',
      width: 120,
      align: 'right' as const,
      render: (balance: number | undefined) => {
        if (balance === undefined || balance === null) return '-'
        return (
          <span style={{ color: balance > 0 ? '#52c41a' : balance < 0 ? '#ff4d4f' : '#999', fontWeight: 600 }}>
            ¥{balance.toFixed(2)}
          </span>
        )
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
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
        return <Tag color={colorMap[status]}>{textMap[status] || status}</Tag>
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 280,
      render: (_: any, record: ParticipantWithBalance) => (
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
          <Button
            type="link"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteParticipant(record)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Space style={{ marginBottom: 16 }} wrap>
        <Select
          style={{ width: 200 }}
          placeholder="选择活动"
          value={selectedEventId}
          onChange={(val) => setSelectedEventId(val)}
          options={events.map((e) => ({ label: e.name, value: e.id }))}
          allowClear
        />
        <Input.Search
          style={{ width: 260 }}
          placeholder="搜索姓名 / 卡号 / 学号"
          prefix={<SearchOutlined />}
          allowClear
          onSearch={handleSearch}
          enterButton
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新建参与者
        </Button>
        <Button
          danger
          icon={<DeleteOutlined />}
          onClick={handleClearAll}
          disabled={participants.length === 0}
        >
          清除所有参与者
        </Button>
      </Space>

      <Table
        columns={columns}
        dataSource={participants}
        rowKey="id"
        loading={loading}
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          showQuickJumper: true,
          total: totalCount,
          showTotal: (total) => `共 ${total} 条`,
          pageSizeOptions: ['10', '20', '50', '100'],
        }}
        scroll={{ x: 1100 }}
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
              {rechargingParticipant?.balance !== undefined && (
                <p>当前余额：¥{rechargingParticipant.balance.toFixed(2)}</p>
              )}
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
