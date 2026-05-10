import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout as AntLayout, Menu, Avatar, Dropdown, theme, Typography } from 'antd'
import {
  ShopOutlined,
  DollarOutlined,
  UnorderedListOutlined,
  ShoppingOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import { getMerchantInfo, clearMerchantAuth } from './MerchantLogin'
import type { MenuProps } from 'antd'

const { Header, Sider, Content } = AntLayout

const MerchantLayout = () => {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const merchant = getMerchantInfo()
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  const menuItems: MenuProps['items'] = [
    {
      key: '/merchant/dashboard',
      icon: <DollarOutlined />,
      label: '收入概览',
    },
    {
      key: '/merchant/booth',
      icon: <ShopOutlined />,
      label: '商铺信息',
    },
    {
      key: '/merchant/products',
      icon: <ShoppingOutlined />,
      label: '商品管理',
    },
    {
      key: '/merchant/transactions',
      icon: <UnorderedListOutlined />,
      label: '交易记录',
    },
    {
      key: '/merchant/cost-evidence',
      icon: <FileTextOutlined />,
      label: '成本凭据',
    },
  ]

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: () => {
        clearMerchantAuth()
        navigate('/merchant/login')
      },
    },
  ]

  const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
    navigate(key)
  }

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider trigger={null} collapsible collapsed={collapsed}>
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: collapsed ? 14 : 18,
            fontWeight: 'bold',
            padding: '0 8px',
            textAlign: 'center',
          }}
        >
          {collapsed ? <ShopOutlined /> : '商户管理中心'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <AntLayout>
        <Header
          style={{
            padding: '0 24px',
            background: colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div
            style={{ fontSize: 20, cursor: 'pointer' }}
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </div>
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <div style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} style={{ marginRight: 8, backgroundColor: '#f5576c' }} />
              <span>{merchant?.booth_name || merchant?.username || '商户'}</span>
            </div>
          </Dropdown>
        </Header>
        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            minHeight: 280,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
          }}
        >
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  )
}

export default MerchantLayout
