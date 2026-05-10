import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  Layout as AntLayout,
  Menu,
  Avatar,
  Dropdown,
  theme,
  Drawer,
  Button,
} from 'antd'
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
  MenuOutlined,
} from '@ant-design/icons'
import { getMerchantInfo, clearMerchantAuth } from './MerchantLogin'
import { useIsMobile } from '@/hooks/useIsMobile'
import type { MenuProps } from 'antd'
import './merchant-mobile.css'

const { Header, Sider, Content } = AntLayout

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

// 移动端底部 Tab Bar 配置（保留5个核心菜单）
const tabBarItems = [
  { key: '/merchant/dashboard', icon: <DollarOutlined />, label: '概览' },
  { key: '/merchant/booth', icon: <ShopOutlined />, label: '商铺' },
  { key: '/merchant/products', icon: <ShoppingOutlined />, label: '商品' },
  { key: '/merchant/transactions', icon: <UnorderedListOutlined />, label: '交易' },
  { key: '/merchant/cost-evidence', icon: <FileTextOutlined />, label: '凭据' },
]

const MerchantLayout = () => {
  const [collapsed, setCollapsed] = useState(false)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const merchant = getMerchantInfo()
  const isMobile = useIsMobile()
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

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
    setDrawerOpen(false)
  }

  const getPageTitle = () => {
    const item = menuItems.find((m: any) => m?.key === location.pathname) as any
    return item?.label || '商户管理中心'
  }

  // ===== 移动端布局 =====
  if (isMobile) {
    return (
      <div className="merchant-mobile">
        {/* 顶部栏 */}
        <div className="merchant-mobile-header">
          <Button
            type="text"
            icon={<MenuOutlined style={{ color: '#fff', fontSize: 20 }} />}
            onClick={() => setDrawerOpen(true)}
            style={{ color: '#fff' }}
          />
          <span className="merchant-mobile-header-title">{getPageTitle()}</span>
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Avatar
              size="small"
              icon={<UserOutlined />}
              style={{ backgroundColor: 'rgba(255,255,255,0.3)', cursor: 'pointer' }}
            />
          </Dropdown>
        </div>

        {/* 内容区 */}
        <div className="merchant-mobile-content">
          <Outlet />
        </div>

        {/* 底部 Tab Bar */}
        <div className="merchant-mobile-tabbar">
          {tabBarItems.map((item) => (
            <div
              key={item.key}
              className={`merchant-mobile-tabbar-item ${
                location.pathname === item.key ? 'active' : ''
              }`}
              onClick={() => navigate(item.key)}
            >
              <span className="icon">{item.icon}</span>
              <span>{item.label}</span>
            </div>
          ))}
        </div>

        {/* 侧边抽屉菜单（作为额外入口） */}
        <Drawer
          title={
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <Avatar
                icon={<UserOutlined />}
                style={{ backgroundColor: '#f5576c', marginRight: 12 }}
              />
              <div>
                <div style={{ fontWeight: 600 }}>
                  {merchant?.booth_name || '商户'}
                </div>
                <div style={{ fontSize: 12, color: '#8c8c8c' }}>
                  {merchant?.username}
                </div>
              </div>
            </div>
          }
          placement="left"
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          width={260}
          className="merchant-mobile-drawer"
        >
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={handleMenuClick}
            style={{ borderRight: 'none' }}
          />
          <div style={{ padding: '16px', borderTop: '1px solid #f0f0f0', marginTop: 20 }}>
            <Button
              block
              danger
              icon={<LogoutOutlined />}
              onClick={() => {
                clearMerchantAuth()
                navigate('/merchant/login')
              }}
            >
              退出登录
            </Button>
          </div>
        </Drawer>
      </div>
    )
  }

  // ===== 桌面端布局 =====
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
              <Avatar
                icon={<UserOutlined />}
                style={{ marginRight: 8, backgroundColor: '#f5576c' }}
              />
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
