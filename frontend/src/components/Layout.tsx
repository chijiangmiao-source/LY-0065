import { useState } from 'react'
import { Layout as AntLayout, Menu, Avatar, Dropdown } from 'antd'
import {
  DashboardOutlined,
  TeamOutlined,
  ScissorOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
  InboxOutlined,
  FileTextOutlined,
  LogoutOutlined,
  UserOutlined,
  AppstoreOutlined,
  CrownOutlined,
} from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { removeToken, getUsername } from '../utils/auth'

const { Header, Sider, Content } = AntLayout

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '统计看板' },
  { key: '/member', icon: <CrownOutlined />, label: '会员管理' },
  { key: '/employee', icon: <TeamOutlined />, label: '员工管理' },
  { key: '/service', icon: <ScissorOutlined />, label: '服务项目' },
  { key: '/service-consumable-template', icon: <AppstoreOutlined />, label: '服务耗材模板' },
  { key: '/appointment', icon: <CalendarOutlined />, label: '预约登记' },
  { key: '/schedule', icon: <ClockCircleOutlined />, label: '排班管理' },
  { key: '/consumable', icon: <InboxOutlined />, label: '耗材台账' },
  { key: '/usage', icon: <FileTextOutlined />, label: '领用登记' },
]

const Layout = () => {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    removeToken()
    navigate('/login')
  }

  const userMenuItems = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <AntLayout className="layout">
      <Sider trigger={null} collapsible collapsed={collapsed}>
        <div className="logo">{collapsed ? '理发店' : '理发店管理系统'}</div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <AntLayout className="site-layout">
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            display: 'flex',
            justifyContent: 'flex-end',
            alignItems: 'center',
          }}
        >
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Avatar icon={<UserOutlined />} />
              <span>{getUsername()}</span>
            </div>
          </Dropdown>
        </Header>
        <Content className="site-layout-content">
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  )
}

export default Layout
