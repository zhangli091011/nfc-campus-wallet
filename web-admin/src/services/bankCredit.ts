import request from '@/utils/request'

// ============================================================================
// Types
// ============================================================================

export interface LoanRecord {
  id: number
  event_id: number
  participant_id: number
  participant_name: string | null
  class_name: string | null
  student_id: string | null
  operator_name: string | null
  principal_amount: number
  principal_amount_yuan: number
  fee_rate: number
  fee_amount: number
  fee_amount_yuan: number
  disbursed_amount: number
  disbursed_amount_yuan: number
  status: 'active' | 'repaid' | 'written_off'
  remark: string | null
  created_at: string
}

export interface ClassDistribution {
  class_name: string
  total_amount: number
  total_amount_yuan: number
  loan_count: number
  borrower_count: number
}

export interface LendingTrend {
  time: string
  amount: number
  amount_yuan: number
  count: number
}

export interface TopDebtor {
  class_name: string
  student_id: string
  participant_name: string
  total_principal: number
  total_principal_yuan: number
  total_disbursed: number
  total_disbursed_yuan: number
  operator_name: string
  last_loan_time: string | null
  loan_count: number
}

export interface CreditDashboardStats {
  total_principal: number
  total_principal_yuan: number
  total_fee: number
  total_fee_yuan: number
  total_disbursed: number
  total_disbursed_yuan: number
  total_loans: number
  total_borrowers: number
  total_participants: number
  penetration_rate: number
  credit_limit: number
  credit_limit_yuan: number
  credit_utilization: number
  class_distribution: ClassDistribution[]
  lending_trend: LendingTrend[]
  top_debtors: TopDebtor[]
}

export interface CreditConfig {
  event_id: number
  max_total_credit: number
  max_total_credit_yuan: number
  max_per_person: number
  max_per_person_yuan: number
  fee_rate: number
  is_enabled: boolean
}

// ============================================================================
// API Calls
// ============================================================================

/** 获取央行风控看板数据 */
export const getCreditDashboard = (eventId: number) =>
  request.get<any, CreditDashboardStats>(`/api/bank-credit/dashboard/${eventId}`)

/** 获取贷款列表 */
export const getLoans = (eventId: number, params?: {
  status?: string
  class_name?: string
  limit?: number
  offset?: number
}) =>
  request.get<any, LoanRecord[]>(`/api/bank-credit/loans/${eventId}`, { params })

/** 获取信贷配置 */
export const getCreditConfig = (eventId: number) =>
  request.get<any, CreditConfig>(`/api/bank-credit/config/${eventId}`)

/** 导出对账单 CSV */
export const exportLoansCSV = (eventId: number) => {
  const token = localStorage.getItem('token')
  // Use relative URL - Vite proxy handles routing to backend
  window.open(`/api/bank-credit/export/${eventId}?token=${token}`, '_blank')
}
