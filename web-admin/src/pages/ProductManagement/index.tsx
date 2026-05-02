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
  Switch,
  message,
  Tag,
  Popconfirm,
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import {
  getProducts,
  createProduct,
  updateProduct,
  deleteProduct,
  type Product,
  type CreateProductRequest,
  type UpdateProductRequest,
} from '@/services/product'
import { getBooths, type Booth } from '@/services/booth'
import { getEvents, type Event } from '@/services/event'
import dayjs from 'dayjs'

const ProductManagement = () => {
  const [products, setProducts] = useState<Product[]>([])
  const [booths, setBooths] = useState<Booth[]>([])
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)
  const [selectedEventId, setSelectedEventId] = useState<number>()
  const [selectedBoothId, setSelectedBoothId] = useState<number>()
  const [form] = Form.useForm()

  useEffect(() => {
    loadEvents()
  }, [])

  useEffect(() => {
    if (selectedEventId) {
      loadBooths()
    }
  }, [selectedEventId])

  useEffect(() => {
    if (selectedBoothId) {
      loadProducts()
    }
  }, [selectedBoothId])

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
    try {
      const data = await getBooths({ event_id: selectedEventId, limit: 100 })
      setBooths(data)
      if (data.length > 0) {
        setSelectedBoothId(data[0].id)
      }
    } catch (error) {
      // 错误已处理
    }
  }

  const loadProducts = async () => {
    if (!selectedBoothId) return
    setLoading(true)
    try {
      const data = await getProducts({ booth_id: selectedBoothId, limit: 100 })
      setProducts(data)
    } catch (error) {
      // 错误已处理
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingProduct(null)
    form.resetFields()
    form.setFieldsValue({ booth_id: selectedBoothId, enabled: true })
    setModalVisible(true)
  }

  const handleEdit = (record: Product) => {
    setEditingProduct(record)
    form.setFieldsValue({
      booth_id: record.booth_id,
      name: record.name,
      price: record.price / 100, // 转换为元
      cost_price: record.cost_price ? record.cost_price / 100 : undefined,
      stock: record.stock,
      enabled: record.enabled,
    })
    setModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteProduct(id)
      message.success('删除成功')
      loadProducts()
    } catch (error) {
      // 错误已处理
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      const data = {
        name: values.name,
        price: Math.round(values.price * 100), // 转换为分
        cost_price: values.cost_price ? Math.round(values.cost_price * 100) : undefined,
        stock: values.stock,
        enabled: values.enabled,
      }

      if (editingProduct) {
        await updateProduct(editingProduct.id, data as UpdateProductRequest)
        message.success('更新成功')
      } else {
        await createProduct({
          booth_id: values.booth_id,
          ...data,
        } as CreateProductRequest)
        message.success('创建成功')
      }

      setModalVisible(false)
      loadProducts()
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
      title: '商品名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '售价',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `¥${(price / 100).toFixed(2)}`,
    },
    {
      title: '成本价',
      dataIndex: 'cost_price',
      key: 'cost_price',
      render: (price: number | null) =>
        price ? `¥${(price / 100).toFixed(2)}` : '-',
    },
    {
      title: '库存',
      dataIndex: 'stock',
      key: 'stock',
      render: (stock: number | null) => (stock === null ? '无限' : stock),
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
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
      width: 150,
      render: (_: any, record: Product) => (
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
            title="确定删除此商品吗？"
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
        <Select
          style={{ width: 200 }}
          placeholder="选择摊位"
          value={selectedBoothId}
          onChange={setSelectedBoothId}
          options={booths.map((b) => ({ label: b.name, value: b.id }))}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新建商品
        </Button>
      </Space>

      <Table
        columns={columns}
        dataSource={products}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title={editingProduct ? '编辑商品' : '新建商品'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="booth_id"
            label="所属摊位"
            rules={[{ required: true, message: '请选择所属摊位' }]}
          >
            <Select disabled={!!editingProduct}>
              {booths.map((b) => (
                <Select.Option key={b.id} value={b.id}>
                  {b.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="name"
            label="商品名称"
            rules={[{ required: true, message: '请输入商品名称' }]}
          >
            <Input placeholder="请输入商品名称" />
          </Form.Item>

          <Form.Item
            name="price"
            label="售价（元）"
            rules={[{ required: true, message: '请输入售价' }]}
          >
            <InputNumber
              min={0}
              precision={2}
              style={{ width: '100%' }}
              placeholder="请输入售价"
            />
          </Form.Item>

          <Form.Item name="cost_price" label="成本价（元）">
            <InputNumber
              min={0}
              precision={2}
              style={{ width: '100%' }}
              placeholder="请输入成本价"
            />
          </Form.Item>

          <Form.Item name="stock" label="库存（留空表示无限）">
            <InputNumber
              min={0}
              style={{ width: '100%' }}
              placeholder="请输入库存数量"
            />
          </Form.Item>

          <Form.Item name="enabled" label="启用" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ProductManagement
