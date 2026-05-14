import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Form, Input, Button, Card, message, Modal } from 'antd'
import { UserOutlined, LockOutlined, ShopOutlined } from '@ant-design/icons'
import { merchantLogin, merchantRecoverPassword } from '@/services/merchant'
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
  const [recoverLoading, setRecoverLoading] = useState(false)
  const [recoverForm] = Form.useForm()
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

  const handleRecover = async () => {
    try {
      const values = await recoverForm.validateFields()
      if (values.new_password !== values.confirm_password) {
        message.error('两次输入的密码不一致')
        return
      }
      setRecoverLoading(true)
      await merchantRecoverPassword({
        username: values.username,
        booth_name: values.booth_name,
        new_password: values.new_password,
      })
      message.success('密码重置成功，请使用新密码登录')
      setRecoverVisible(false)
      recoverForm.resetFields()
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
            <a onClick={() => setRecoverVisible(true)}>忘记密码？</a>
          </div>
        </Form>
      </Card>

      <Modal
        title="找回密码"
        open={recoverVisible}
        onCancel={() => setRecoverVisible(false)}
        onOk={handleRecover}
        confirmLoading={recoverLoading}
        okText="重置密码"
        cancelText="取消"
      >
        <p style={{ marginBottom: 16, color: '#666' }}>
          请输入注册时的用户名和商铺名称来验证身份
        </p>
        <Form form={recoverForm} layout="vertical">
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="注册时的用户名" />
          </Form.Item>
          <Form.Item
            name="booth_name"
            label="商铺名称"
            rules={[{ required: true, message: '请输入商铺名称' }]}
          >
            <Input prefix={<ShopOutlined />} placeholder="注册时填写的商铺名称" />
          </Form.Item>
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
