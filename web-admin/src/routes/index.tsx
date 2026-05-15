import { Routes, Route, Navigate } from 'react-router-dom'
import { isAuthenticated } from '@/utils/auth'
import Login from '@/pages/Login'
import Layout from '@/components/Layout'
import Dashboard from '@/pages/Dashboard'
import EventManagement from '@/pages/EventManagement'
import BoothManagement from '@/pages/BoothManagement'
import ProductManagement from '@/pages/ProductManagement'
import ParticipantManagement from '@/pages/ParticipantManagement'
import ParticipantBalances from '@/pages/ParticipantBalances'
import ClassSearch from '@/pages/ClassSearch'
import TransactionHistory from '@/pages/TransactionHistory'
import BoothTransactions from '@/pages/BoothTransactions'
import ParticipantTransactions from '@/pages/ParticipantTransactions'
import RefundApproval from '@/pages/RefundApproval'
import RefundMonitor from '@/pages/RefundMonitor'
import UserManagement from '@/pages/UserManagement'
import CostEvidenceReview from '@/pages/CostEvidenceReview'
import StockDashboard from '@/pages/StockDashboard'
import StockBreakdown from '@/pages/StockBreakdown'
import InvestmentManagement from '@/pages/Investment'
import {
  ReportsDashboard,
  BoothReport,
  BoothLeaderboard,
  ProductLeaderboard,
  AuditLogs,
  ExportPage,
} from '@/pages/Reports'
import BankCreditDashboard from '@/pages/BankCreditDashboard'
import MacroEconomyDashboard from '@/pages/MacroEconomyDashboard'
import AppUpdate from '@/pages/AppUpdate'
import BankLoanManagement from '@/pages/BankLoanManagement'
import CardReturnRecords from '@/pages/CardReturnRecords'
import RefundRequestApproval from '@/pages/RefundRequestApproval'
import RandomDiscount from '@/pages/RandomDiscount'
import {
  MerchantLogin,
  MerchantRegister,
  MerchantLayout,
  MerchantDashboard,
  MerchantBooth,
  MerchantProducts,
  MerchantTransactions,
  MerchantCostEvidence,
  isMerchantAuthenticated,
} from '@/pages/Merchant'

// 路由守卫组件
const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  return isAuthenticated() ? <>{children}</> : <Navigate to="/login" replace />
}

// 商户路由守卫
const MerchantPrivateRoute = ({ children }: { children: React.ReactNode }) => {
  return isMerchantAuthenticated() ? <>{children}</> : <Navigate to="/merchant/login" replace />
}

const AppRoutes = () => {
  return (
    <Routes>
      {/* 登录页 */}
      <Route path="/login" element={<Login />} />

      {/* 股市大屏（全屏，无Layout，无需登录） */}
      <Route
        path="/stock-dashboard"
        element={<StockDashboard />}
      />

      {/* 央行信用风险看板（全屏，无Layout） */}
      <Route
        path="/bank-credit-dashboard"
        element={
          <PrivateRoute>
            <BankCreditDashboard />
          </PrivateRoute>
        }
      />

      {/* 宏观经济与风控审计大屏（全屏，无Layout） */}
      <Route
        path="/macro-economy-dashboard"
        element={
          <PrivateRoute>
            <MacroEconomyDashboard />
          </PrivateRoute>
        }
      />

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
        <Route path="participant-balances" element={<ParticipantBalances />} />
        <Route path="class-search" element={<ClassSearch />} />
        <Route path="transactions" element={<TransactionHistory />} />
        <Route path="booth-transactions" element={<BoothTransactions />} />
        <Route path="participant-transactions" element={<ParticipantTransactions />} />
        <Route path="refunds" element={<RefundApproval />} />
        <Route path="refund-monitor" element={<RefundMonitor />} />
        <Route path="cost-evidence-review" element={<CostEvidenceReview />} />
        <Route path="users" element={<UserManagement />} />
        
        {/* 投资管理 */}
        <Route path="investment" element={<InvestmentManagement />} />
        
        {/* 股价计算公示 */}
        <Route path="stock-breakdown" element={<StockBreakdown />} />
        
        {/* 应用版本管理 */}
        <Route path="app-update" element={<AppUpdate />} />
        
        {/* 银行借贷管理 */}
        <Route path="bank-loans" element={<BankLoanManagement />} />
        
        {/* 退卡记录 */}
        <Route path="card-returns" element={<CardReturnRecords />} />
        
        {/* 退款审批 */}
        <Route path="refund-requests" element={<RefundRequestApproval />} />
        
        {/* 随机立减管理 */}
        <Route path="random-discount" element={<RandomDiscount />} />
        
        {/* 报表相关路由 */}
        <Route path="reports/dashboard" element={<ReportsDashboard />} />
        <Route path="reports/booths" element={<BoothReport />} />
        <Route path="reports/booth-leaderboard" element={<BoothLeaderboard />} />
        <Route path="reports/product-leaderboard" element={<ProductLeaderboard />} />
        <Route path="reports/audit-logs" element={<AuditLogs />} />
        <Route path="reports/export" element={<ExportPage />} />
      </Route>

      {/* 商户系统 */}
      <Route path="/merchant/login" element={<MerchantLogin />} />
      <Route path="/merchant/register" element={<MerchantRegister />} />
      <Route
        path="/merchant"
        element={
          <MerchantPrivateRoute>
            <MerchantLayout />
          </MerchantPrivateRoute>
        }
      >
        <Route index element={<Navigate to="/merchant/dashboard" replace />} />
        <Route path="dashboard" element={<MerchantDashboard />} />
        <Route path="booth" element={<MerchantBooth />} />
        <Route path="products" element={<MerchantProducts />} />
        <Route path="transactions" element={<MerchantTransactions />} />
        <Route path="cost-evidence" element={<MerchantCostEvidence />} />
      </Route>

      {/* 404 */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default AppRoutes
