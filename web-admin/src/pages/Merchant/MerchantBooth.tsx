import { useState, useEffect } from 'react'
import { Card, Descriptions, Button, Modal, Form, Input, message, Tag, Spin } from 'antd'
import { EditOutlined, ShopOutlined } from '@ant-design/icons'
import {
  getMerchantBooth,
  updateMerchantBooth,
  type MerchantBoothInfo,
} from '@/services/merchant'
import { useIsMobile } from '@/hooks/useIsMobile'
import dayjs from 'dayjs'
import './merchant-mobile.css'

const MerchantBooth = () => {
  const [booth, setBooth] = useState<MerchantBoothInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [editLoading, setEditLoading] = useState(false)
  const [form] = Form.useForm()
  const isMobile = useIsMobile()

  useEffect(() => {
    loadBooth()
  }, [])

  const loadBooth = async () => {
    setLoading(true)
    try {
      const data = await getMerchantBooth()
      setBooth(data)
    } catch (error) {
      message.error('加载商铺信息失败')
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = () => {
    if (booth) {
      form.setFieldsValue({
        booth_name: booth.booth_name,
        class_name: booth.class_name,
      })
      setEditModalVisible(true)
    }
  }

  const handleEditSubmit = async () => {
    try {
      const values = await form.validateFields()
      setEditLoading(true)
      await updateMerchantBooth(values)
      message.success('商铺信息更新成功')
      setEditModalVisible(false)
      loadBooth()
    } catch (error: any) {
      if (error?.response?.data?.message) {
        message.error(error.response.data.message)
      }
    } finally {
      setEditLoading(false)
    }
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!booth) {
    return <div>商铺信息不存在</div>
  }

  const statusColorMap: Record<string, string> = {
    active: 'green',
    inactive: 'orange',
    closed: 'red',
  }
  const statusLabelMap: Record<string, string> = {
    active: '营业中',
    inactive: '暂停营业',
    closed: '已关闭',
  }

  return (
    <div>
      <Card
        title={
          <span>
            <ShopOutlined style={{ marginRight: 8 }} />
            商铺信息
          </span>
        }
        extra={
          <Button
            type="primary"
            icon={<EditOutlined />}
            onClick={handleEdit}
            size={isMobile ? 'small' : 'middle'}
          >
            编辑
          </Button>
        }
      >
        <Descriptions
          column={isMobile ? 1 : { xs: 1, sm: 2 }}
          bordered
          size={isMobile ? 'small' : 'default'}
          labelStyle={isMobile ? { width: 90 } : undefined}
        >
          <Descriptions.Item label="商铺名称">{booth.booth_name}</Descriptions.Item>
          <Descriptions.Item label="班级">{booth.class_name}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusColorMap[booth.status] || 'default'}>
              {statusLabelMap[booth.status] || booth.status}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="商铺ID">{booth.booth_id}</Descriptions.Item>
          <Descriptions.Item label="活动ID">{booth.event_id}</Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {dayjs(booth.created_at).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
          <Descriptions.Item label="商品数量">{booth.products.length} 个</Descriptions.Item>
        </Descriptions>
      </Card>

      <Modal
        title="编辑商铺信息"
        open={editModalVisible}
        onOk={handleEditSubmit}
        onCancel={() => setEditModalVisible(false)}
        confirmLoading={editLoading}
        okText="保存"
        cancelText="取消"
        width={isMobile ? '94%' : 520}
        centered
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="booth_name"
            label="商铺名称"
            rules={[
              { required: true, message: '请输入商铺名称' },
              { max: 100, message: '最多100个字符' },
            ]}
          >
            <Input placeholder="请输入商铺名称" />
          </Form.Item>
          <Form.Item
            name="class_name"
            label="班级名称"
            rules={[
              { required: true, message: '请输入班级名称' },
              { max: 100, message: '最多100个字符' },
            ]}
          >
            <Input placeholder="请输入班级名称" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default MerchantBooth
