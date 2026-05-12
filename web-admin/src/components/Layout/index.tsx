import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout as AntLayout, Menu, Avatar, Dropdown, theme } from 'antd'
import {
  DashboardOutlined,
  CalendarOutlined,
  ShopOutlined,
  ShoppingOutlined,
  TeamOutlined,
  TransactionOutlined,
  CheckCircleOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BarChartOutlined,
  TrophyOutlined,
  FileExcelOutlined,
  AuditOutlined,
  FundOutlined,
  StockOutlined,
  DollarCircleOutlined,
  BankOutlined,
  AlertOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import { getUser, clearAuth, isSuperAdmin } from '@/utils/auth'
import type { MenuProps } from 'antd'

const { Header, Sider, Content } = AntLayout

const Layout = () => {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const user = getUser()
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  // 菜单项
  const menuItems: MenuProps['items'] = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '数据看板',
    },
    {
      key: '/events',
      icon: <CalendarOutlined />,
      label: '活动管理',
    },
    {
      key: '/booths',
      icon: <ShopOutlined />,
      label: '摊位管理',
    },
    {
      key: '/products',
      icon: <ShoppingOutlined />,
      label: '商品管理',
    },
    {
      key: '/participants',
      icon: <TeamOutlined />,
      label: '参与者管理',
    },
    {
      key: '/participant-balances',
      icon: <DollarCircleOutlined />,
      label: '参与者余额',
    },
    {
      key: '/transactions',
      icon: <TransactionOutlined />,
      label: '交易流水',
    },
    {
      key: '/refunds',
      icon: <CheckCircleOutlined />,
      label: '退款审批',
    },
    {
      key: '/refund-monitor',
      icon: <AlertOutlined />,
      label: '退款监控',
    },
    {
      key: '/cost-evidence-review',
      icon: <FileTextOutlined />,
      label: '凭据审核',
    },
    {
      key: 'reports',
      icon: <BarChartOutlined />,
      label: '报表中心',
      children: [
        {
          key: '/reports/dashboard',
          icon: <FundOutlined />,
          label: '总览看板',
        },
        {
          key: '/reports/booths',
          icon: <ShopOutlined />,
          label: '摊位报表',
        },
        {
          key: '/reports/booth-leaderboard',
          icon: <TrophyOutlined />,
          label: '摊位排行榜',
        },
        {
          key: '/reports/product-leaderboard',
          icon: <TrophyOutlined />,
          label: '商品排行榜',
        },
        {
          key: '/reports/audit-logs',
          icon: <AuditOutlined />,
          label: '异常审计',
        },
        {
          key: '/reports/export',
          icon: <FileExcelOutlined />,
          label: '报表导出',
        },
      ],
    },
    {
      key: 'stock-dashboard',
      icon: <StockOutlined />,
      label: '股市大屏',
    },
    {
      key: 'bank-credit-dashboard',
      icon: <BankOutlined />,
      label: '央行风控大屏',
    },
    {
      key: 'macro-economy-dashboard',
      icon: <FundOutlined />,
      label: '宏观经济大屏',
    },
    {
      key: '/investment',
      icon: <DollarCircleOutlined />,
      label: '投资管理',
    },
    ...(isSuperAdmin()
      ? [
          {
            key: '/users',
            icon: <UserOutlined />,
            label: '用户管理',
          },
        ]
      : []),
  ]

  // 用户下拉菜单
  const userMenuItems: MenuProps['items'] = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: () => {
        clearAuth()
        navigate('/login')
      },
    },
  ]

  const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
    // 股市大屏在新窗口打开
    if (key === 'stock-dashboard') {
      window.open('/stock-dashboard', '_blank')
      return
    }
    // 央行风控大屏在新窗口打开
    if (key === 'bank-credit-dashboard') {
      window.open('/bank-credit-dashboard', '_blank')
      return
    }
    // 宏观经济大屏在新窗口打开
    if (key === 'macro-economy-dashboard') {
      window.open('/macro-economy-dashboard', '_blank')
      return
    }
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
            fontSize: collapsed ? 16 : 20,
            fontWeight: 'bold',
          }}
        >
          {collapsed ? 'NFC' : 'NFC 钱包管理'}
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
              <Avatar icon={<UserOutlined />} style={{ marginRight: 8 }} />
              <span>{user?.username}</span>
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

export default Layout
