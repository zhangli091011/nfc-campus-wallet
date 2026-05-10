import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Form, Input, Button, Card, message } from 'antd'
import { UserOutlined, LockOutlined, ShopOutlined } from '@ant-design/icons'
import { merchantLogin } from '@/services/merchant'
import { setToken } from '@/utils/auth'

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

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    }}>
      <Card
        style={{ width: 420, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}
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
            还没有账号？<Link to="/merchant/register">立即注册</Link>
          </div>
        </Form>
      </Card>
    </div>
  )
}

export default MerchantLogin
