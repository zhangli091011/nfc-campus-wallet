import { useState, useEffect } from 'react'
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  InputNumber,
  Switch,
  message,
  Tag,
  Popconfirm,
  Card,
  Empty,
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import {
  getMerchantBooth,
  addMerchantProduct,
  updateMerchantProduct,
  deleteMerchantProduct,
  type MerchantProduct,
} from '@/services/merchant'
import { useIsMobile } from '@/hooks/useIsMobile'
import dayjs from 'dayjs'
import './merchant-mobile.css'

const MerchantProducts = () => {
  const [products, setProducts] = useState<MerchantProduct[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingProduct, setEditingProduct] = useState<MerchantProduct | null>(null)
  const [submitLoading, setSubmitLoading] = useState(false)
  const [form] = Form.useForm()
  const isMobile = useIsMobile()

  useEffect(() => {
    loadProducts()
  }, [])

  const loadProducts = async () => {
    setLoading(true)
    try {
      const data = await getMerchantBooth()
      setProducts(data.products || [])
    } catch (error) {
      message.error('加载商品列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingProduct(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (product: MerchantProduct) => {
    setEditingProduct(product)
    form.setFieldsValue({
      name: product.name,
      price: product.price,
      cost_price: product.cost_price,
      stock: product.stock,
      enabled: product.enabled,
    })
    setModalVisible(true)
  }

  const handleDelete = async (productId: number) => {
    try {
      await deleteMerchantProduct(productId)
      message.success('商品已删除')
      loadProducts()
    } catch (error: any) {
      if (error?.response?.data?.message) {
        message.error(error.response.data.message)
      }
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setSubmitLoading(true)

      if (editingProduct) {
        await updateMerchantProduct(editingProduct.id, {
          name: values.name,
          price: values.price,
          cost_price: values.cost_price || undefined,
          stock: values.stock ?? undefined,
          enabled: values.enabled,
        })
        message.success('商品更新成功')
      } else {
        await addMerchantProduct({
          name: values.name,
          price: values.price,
          cost_price: values.cost_price || undefined,
          stock: values.stock ?? undefined,
        })
        message.success('商品添加成功')
      }

      setModalVisible(false)
      loadProducts()
    } catch (error: any) {
      if (error?.response?.data?.message) {
        message.error(error.response.data.message)
      }
    } finally {
      setSubmitLoading(false)
    }
  }

  const columns = [
    { title: '商品名称', dataIndex: 'name', key: 'name' },
    {
      title: '定价（元）',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `¥${price.toFixed(2)}`,
    },
    {
      title: '成本价（元）',
      dataIndex: 'cost_price',
      key: 'cost_price',
      render: (price: number | null) => (price != null ? `¥${price.toFixed(2)}` : '-'),
    },
    {
      title: '库存',
      dataIndex: 'stock',
      key: 'stock',
      render: (stock: number | null) => (stock != null ? stock : '无限'),
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled: boolean) => (
        <Tag color={enabled ? 'green' : 'red'}>{enabled ? '上架' : '下架'}</Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => dayjs(time).format('MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: MerchantProduct) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确定删除该商品？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // 移动端卡片渲染
  const renderMobileList = () => {
    if (loading) {
      return <div style={{ textAlign: 'center', padding: 30 }}>加载中...</div>
    }
    if (products.length === 0) {
      return <Empty description="暂无商品，点击上方按钮添加" />
    }
    return (
      <div>
        {products.map((p) => (
          <div key={p.id} className="merchant-mobile-list-item">
            <div className="merchant-mobile-list-item-header">
              <span>{p.name}</span>
              <Tag color={p.enabled ? 'green' : 'red'}>
                {p.enabled ? '上架' : '下架'}
              </Tag>
            </div>
            <div className="merchant-mobile-list-item-row">
              <span className="label">定价</span>
              <span className="value" style={{ color: '#f5576c', fontWeight: 600 }}>
                ¥{p.price.toFixed(2)}
              </span>
            </div>
            <div className="merchant-mobile-list-item-row">
              <span className="label">成本价</span>
              <span className="value">
                {p.cost_price != null ? `¥${p.cost_price.toFixed(2)}` : '-'}
              </span>
            </div>
            <div className="merchant-mobile-list-item-row">
              <span className="label">库存</span>
              <span className="value">{p.stock != null ? p.stock : '无限'}</span>
            </div>
            <div className="merchant-mobile-list-item-row">
              <span className="label">创建时间</span>
              <span className="value">{dayjs(p.created_at).format('MM-DD HH:mm')}</span>
            </div>
            <div className="merchant-mobile-list-item-actions">
              <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(p)}>
                编辑
              </Button>
              <Popconfirm
                title="确定删除该商品？"
                onConfirm={() => handleDelete(p.id)}
                okText="确定"
                cancelText="取消"
              >
                <Button size="small" danger icon={<DeleteOutlined />}>
                  删除
                </Button>
              </Popconfirm>
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <Card
      title="商品管理"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd} size={isMobile ? 'small' : 'middle'}>
          {isMobile ? '添加' : '添加商品'}
        </Button>
      }
    >
      {isMobile ? (
        renderMobileList()
      ) : (
        <Table
          columns={columns}
          dataSource={products}
          rowKey="id"
          loading={loading}
          pagination={false}
          locale={{ emptyText: '暂无商品，点击上方按钮添加' }}
        />
      )}

      <Modal
        title={editingProduct ? '编辑商品' : '添加商品'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        confirmLoading={submitLoading}
        okText={editingProduct ? '保存' : '添加'}
        cancelText="取消"
        destroyOnClose
        width={isMobile ? '94%' : 520}
        centered
      >
        <Form form={form} layout="vertical" initialValues={{ enabled: true }}>
          <Form.Item
            name="name"
            label="商品名称"
            rules={[
              { required: true, message: '请输入商品名称' },
              { max: 100, message: '最多100个字符' },
            ]}
          >
            <Input placeholder="如：珍珠奶茶" />
          </Form.Item>

          <Form.Item
            name="price"
            label="定价（元）"
            rules={[{ required: true, message: '请输入定价' }]}
          >
            <InputNumber
              min={0.01}
              step={0.5}
              precision={2}
              style={{ width: '100%' }}
              placeholder="如：8.00"
              addonAfter="元"
            />
          </Form.Item>

          <Form.Item name="cost_price" label="成本价（元，可选）">
            <InputNumber
              min={0}
              step={0.5}
              precision={2}
              style={{ width: '100%' }}
              placeholder="如：3.50"
              addonAfter="元"
            />
          </Form.Item>

          <Form.Item name="stock" label="库存数量（不填表示无限）">
            <InputNumber
              min={0}
              step={1}
              precision={0}
              style={{ width: '100%' }}
              placeholder="如：50（不填表示无限库存）"
            />
          </Form.Item>

          {editingProduct && (
            <Form.Item name="enabled" label="上架状态" valuePropName="checked">
              <Switch checkedChildren="上架" unCheckedChildren="下架" />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </Card>
  )
}

export default MerchantProducts
