import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Form, Input, Button, Card, message, Modal, List } from 'antd'
import { UserOutlined, LockOutlined, ShopOutlined } from '@ant-design/icons'
import {
  merchantLogin,
  merchantRecoverPassword,
  getMerchantBoothsPublic,
  type MerchantBoothPublic,
} from '@/services/merchant'
import { setToken } from '@/utils/auth'
import './merchant-mobile.css'

const MERCHANT_KEY = 'nfc_merchant_info'

export const setMerchantInfo = (info: any) => {
  localStorage.setItem(MERCHANT_KEY, JSON.stringify(info))
}

export const getMerchantInfo = () => {
  const str = localStorage.getItem(MERCHANT_KEY)
  if (!str) return null
  try {
    return JSON.parse(str)
  } catch {
    return null
  }
}

export const clearMerchantAuth = () => {
  localStorage.removeItem(MERCHANT_KEY)
  localStorage.removeItem('nfc_wallet_token')
}

export const isMerchantAuthenticated = () => {
  return !!localStorage.getItem('nfc_wallet_token') && !!localStorage.getItem(MERCHANT_KEY)
}

const MerchantLogin = () => {
  const [loading, setLoading] = useState(false)
  const [recoverVisible, setRecoverVisible] = useState(false)
  const [resetVisible, setResetVisible] = useState(false)
  const [recoverLoading, setRecoverLoading] = useState(false)
  const [booths, setBooths] = useState<MerchantBoothPublic[]>([])
  const [boothsLoading, setBoothsLoading] = useState(false)
  const [selectedBooth, setSelectedBooth] = useState<MerchantBoothPublic | null>(null)
  const [resetForm] = Form.useForm()
  const navigate = useNavigate()

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const response = await merchantLogin(values)
      setToken(response.access_token)
      setMerchantInfo(response.merchant)
      message.success('登录成功')
      navigate('/merchant/dashboard')
    } catch (error: any) {
      if (error?.response?.data?.message) {
        message.error(error.response.data.message)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleOpenRecover = async () => {
    setRecoverVisible(true)
    setBoothsLoading(true)
    try {
      const data = await getMerchantBoothsPublic()
      setBooths(data?.booths || [])
    } catch {
      message.error('获取摊位列表失败')
    } finally {
      setBoothsLoading(false)
    }
  }

  const handleSelectBooth = (booth: MerchantBoothPublic) => {
    setSelectedBooth(booth)
    setRecoverVisible(false)
    setResetVisible(true)
    resetForm.resetFields()
  }

  const handleResetPassword = async () => {
    if (!selectedBooth) return
    try {
      const values = await resetForm.validateFields()
      if (values.new_password !== values.confirm_password) {
        message.error('两次输入的密码不一致')
        return
      }
      setRecoverLoading(true)
      const result = await merchantRecoverPassword({
        booth_id: selectedBooth.booth_id,
        new_password: values.new_password,
      })
      message.success(`密码重置成功！用户名: ${result.username || selectedBooth.username}`)
      setResetVisible(false)
      setSelectedBooth(null)
      resetForm.resetFields()
    } catch (error: any) {
      if (error?.response?.data?.message) {
        message.error(error.response.data.message)
      }
    } finally {
      setRecoverLoading(false)
    }
  }

  return (
    <div className="merchant-auth-mobile">
      <Card
        title={
          <div style={{ textAlign: 'center', fontSize: 20, fontWeight: 'bold' }}>
            <ShopOutlined style={{ marginRight: 8 }} />
            商户登录
          </div>
        }
      >
        <Form name="merchant-login" onFinish={onFinish} size="large">
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              登录
            </Button>
          </Form.Item>

          <div style={{ textAlign: 'center' }}>
            <span>
              还没有账号？<Link to="/merchant/register">立即注册</Link>
            </span>
            <span style={{ margin: '0 12px', color: '#ddd' }}>|</span>
            <a onClick={handleOpenRecover}>忘记密码？</a>
          </div>
        </Form>
      </Card>

      {/* 摊位列表弹窗 */}
      <Modal
        title="选择你的摊位"
        open={recoverVisible}
        onCancel={() => setRecoverVisible(false)}
        footer={null}
        width={400}
      >
        <p style={{ marginBottom: 12, color: '#666' }}>
          请点击你的摊位来重置密码
        </p>
        <List
          loading={boothsLoading}
          dataSource={booths}
          locale={{ emptyText: '暂无摊位' }}
          renderItem={(booth) => (
            <List.Item
              style={{ cursor: 'pointer', padding: '12px 16px' }}
              onClick={() => handleSelectBooth(booth)}
            >
              <List.Item.Meta
                avatar={<ShopOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
                title={booth.booth_name}
                description={
                  <span>
                    {booth.class_name && <span>{booth.class_name}</span>}
                    {booth.username && (
                      <span style={{ marginLeft: 8, color: '#999' }}>
                        账号: {booth.username}
                      </span>
                    )}
                  </span>
                }
              />
            </List.Item>
          )}
        />
      </Modal>

      {/* 重置密码弹窗 */}
      <Modal
        title={`重置密码 - ${selectedBooth?.booth_name || ''}`}
        open={resetVisible}
        onCancel={() => {
          setResetVisible(false)
          setSelectedBooth(null)
        }}
        onOk={handleResetPassword}
        confirmLoading={recoverLoading}
        okText="确认重置"
        cancelText="取消"
      >
        {selectedBooth && (
          <div style={{ marginBottom: 16, padding: '8px 12px', background: '#f5f5f5', borderRadius: 6 }}>
            <div><strong>摊位：</strong>{selectedBooth.booth_name}</div>
            {selectedBooth.class_name && <div><strong>班级：</strong>{selectedBooth.class_name}</div>}
            {selectedBooth.username && <div><strong>用户名：</strong>{selectedBooth.username}</div>}
          </div>
        )}
        <Form form={resetForm} layout="vertical">
          <Form.Item
            name="new_password"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码长度不能少于6位' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="设置新密码" />
          </Form.Item>
          <Form.Item
            name="confirm_password"
            label="确认新密码"
            rules={[
              { required: true, message: '请再次输入新密码' },
              { min: 6, message: '密码长度不能少于6位' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="再次输入新密码" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default MerchantLogin
