import { useState, useRef, useCallback } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Form, Input, Button, message } from 'antd'
import { UserOutlined, LockOutlined, ShopOutlined, TeamOutlined } from '@ant-design/icons'
import { merchantRegister } from '@/services/merchant'
import { setToken } from '@/utils/auth'
import { setMerchantInfo } from './MerchantLogin'
import TermsModal from './TermsModal'
import './merchant-register.css'

const MerchantRegister = () => {
  const [loading, setLoading] = useState(false)
  const [isAgreed, setIsAgreed] = useState(false)
  const [showTermsModal, setShowTermsModal] = useState(false)
  const navigate = useNavigate()

  const onFinish = async (values: {
    username: string
    password: string
    confirm_password: string
    booth_name: string
    class_name: string
  }) => {
    if (!isAgreed) {
      message.warning('请先阅读并同意《宇华校园沙盒市场商家服务条款》')
      return
    }
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

  const handleTermsConfirm = useCallback(() => {
    setIsAgreed(true)
    setShowTermsModal(false)
  }, [])

  const handleCheckboxToggle = () => {
    setIsAgreed(prev => !prev)
  }

  const handleOpenTerms = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setShowTermsModal(true)
  }

  return (
    <div className="merchant-register-dark">
      {/* 背景装饰 */}
      <div className="register-bg-grid" />
      <div className="register-bg-glow" />

      <div className="register-card">
        {/* 顶部标题 */}
        <div className="register-header">
          <div className="register-header-icon">
            <ShopOutlined />
          </div>
          <h1 className="register-title">商户注册</h1>
          <p className="register-subtitle">宇华校园沙盒经济平台</p>
        </div>

        {/* 表单 */}
        <Form name="merchant-register" onFinish={onFinish} size="large" className="register-form">
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

          {/* 条款复选框区域 */}
          <div className="terms-checkbox-area">
            <label className="terms-checkbox-label" onClick={handleCheckboxToggle}>
              <span className={`terms-checkbox ${isAgreed ? 'checked' : ''}`}>
                {isAgreed && (
                  <svg viewBox="0 0 12 10" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M1 5L4.5 8.5L11 1.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                )}
              </span>
              <span className="terms-text">
                我已阅读并同意{' '}
                <span className="terms-link" onClick={handleOpenTerms}>
                  《宇华校园沙盒市场商家服务条款》
                </span>
              </span>
            </label>
          </div>

          {/* 注册按钮 */}
          <Form.Item style={{ marginBottom: 16 }}>
            <button
              type="submit"
              className={`register-submit-btn ${isAgreed ? 'active' : 'disabled'}`}
              disabled={!isAgreed || loading}
            >
              {loading ? (
                <span className="btn-loading">
                  <span className="btn-loading-dot" />
                  <span className="btn-loading-dot" />
                  <span className="btn-loading-dot" />
                </span>
              ) : (
                '注 册'
              )}
            </button>
          </Form.Item>

          <div className="register-footer-link">
            已有账号？<Link to="/merchant/login">去登录</Link>
          </div>
        </Form>
      </div>

      {/* 条款弹窗 */}
      <TermsModal
        visible={showTermsModal}
        onClose={() => setShowTermsModal(false)}
        onConfirm={handleTermsConfirm}
      />
    </div>
  )
}

export default MerchantRegister
