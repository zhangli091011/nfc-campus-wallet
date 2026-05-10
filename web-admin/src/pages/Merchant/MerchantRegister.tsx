import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Form, Input, Button, Card, message } from 'antd'
import { UserOutlined, LockOutlined, ShopOutlined, TeamOutlined } from '@ant-design/icons'
import { merchantRegister } from '@/services/merchant'
import { setToken } from '@/utils/auth'
import { setMerchantInfo } from './MerchantLogin'

const MerchantRegister = () => {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const onFinish = async (values: {
    username: string
    password: string
    confirm_password: string
    booth_name: string
    class_name: string
  }) => {
    setLoading(true)
    try {
      const response = await merchantRegister({
        username: values.username,
        password: values.password,
        booth_name: values.booth_name,
        class_name: values.class_name,
      })
      setToken(response.access_token)
      setMerchantInfo(response.merchant)
      message.success('注册成功！')
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
        style={{ width: 460, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}
        title={
          <div style={{ textAlign: 'center', fontSize: 20, fontWeight: 'bold' }}>
            <ShopOutlined style={{ marginRight: 8 }} />
            商户注册
          </div>
        }
      >
        <Form name="merchant-register" onFinish={onFinish} size="large">
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少3个字符' },
              { max: 50, message: '用户名最多50个字符' },
              { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线' },
            ]}
          >
            <Input prefix={<UserOutlined />} placeholder="用户名（字母、数字、下划线）" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6个字符' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码（至少6位）" />
          </Form.Item>

          <Form.Item
            name="confirm_password"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'))
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="确认密码" />
          </Form.Item>

          <Form.Item
            name="booth_name"
            rules={[
              { required: true, message: '请输入商铺名称' },
              { max: 100, message: '商铺名称最多100个字符' },
            ]}
          >
            <Input prefix={<ShopOutlined />} placeholder="商铺名称" />
          </Form.Item>

          <Form.Item
            name="class_name"
            rules={[
              { required: true, message: '请输入班级名称' },
              { max: 100, message: '班级名称最多100个字符' },
            ]}
          >
            <Input prefix={<TeamOutlined />} placeholder="班级名称（如：高一(3)班）" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              注册
            </Button>
          </Form.Item>

          <div style={{ textAlign: 'center' }}>
            已有账号？<Link to="/merchant/login">去登录</Link>
          </div>
        </Form>
      </Card>
    </div>
  )
}

export default MerchantRegister
