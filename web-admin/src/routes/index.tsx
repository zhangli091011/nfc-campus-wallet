import { Routes, Route, Navigate } from 'react-router-dom'
import { isAuthenticated } from '@/utils/auth'
import Login from '@/pages/Login'
import Layout from '@/components/Layout'
import Dashboard from '@/pages/Dashboard'
import EventManagement from '@/pages/EventManagement'
import BoothManagement from '@/pages/BoothManagement'
import ProductManagement from '@/pages/ProductManagement'
import ParticipantManagement from '@/pages/ParticipantManagement'
import TransactionHistory from '@/pages/TransactionHistory'
import RefundApproval from '@/pages/RefundApproval'
import UserManagement from '@/pages/UserManagement'
import {
  ReportsDashboard,
  BoothReport,
  BoothLeaderboard,
  ProductLeaderboard,
  AuditLogs,
  ExportPage,
} from '@/pages/Reports'

// 路由守卫组件
const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  return isAuthenticated() ? <>{children}</> : <Navigate to="/login" replace />
}

const AppRoutes = () => {
  return (
    <Routes>
      {/* 登录页 */}
      <Route path="/login" element={<Login />} />

      {/* 主应用 */}
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="events" element={<EventManagement />} />
        <Route path="booths" element={<BoothManagement />} />
        <Route path="products" element={<ProductManagement />} />
        <Route path="participants" element={<ParticipantManagement />} />
        <Route path="transactions" element={<TransactionHistory />} />
        <Route path="refunds" element={<RefundApproval />} />
        <Route path="users" element={<UserManagement />} />
        
        {/* 报表相关路由 */}
        <Route path="reports/dashboard" element={<ReportsDashboard />} />
        <Route path="reports/booths" element={<BoothReport />} />
        <Route path="reports/booth-leaderboard" element={<BoothLeaderboard />} />
        <Route path="reports/product-leaderboard" element={<ProductLeaderboard />} />
        <Route path="reports/audit-logs" element={<AuditLogs />} />
        <Route path="reports/export" element={<ExportPage />} />
      </Route>

      {/* 404 */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default AppRoutes
