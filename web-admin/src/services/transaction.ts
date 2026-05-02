import request from '@/utils/request'

export interface Transaction {
  id: number
  type: 'recharge' | 'pay' | 'refund' | 'correction'
  amount: number // 单位：分
  balance_before: number
  balance_after: number
  participant_id: number
  card_uid: string
  booth_id?: number | null
  product_id?: number | null
  operator_id?: number | null
  merchant_id?: string | null
  related_txn_id?: number | null
  remark?: string
  created_at: string
}

export interface TransactionListResponse {
  transactions: Transaction[]
  total_count: number
}

// 获取交易列表
export const getTransactions = (params: {
  event_id?: number
  booth_id?: number
  product_id?: number
  type?: string
  start_date?: string
  end_date?: string
  limit?: number
  offset?: number
}) => {
  return request.get<any, TransactionListResponse>('/transactions', { params })
}

// 获取交易详情
export const getTransaction = (id: number) => {
  return request.get<any, Transaction>(`/transactions/${id}`)
}

// 退款
export const refund = (data: {
  transaction_id: number
  reason: string
}) => {
  return request.post('/refund', data)
}

// 更正
export const correction = (data: {
  participant_id: number
  amount: number
  reason: string
}) => {
  return request.post('/correction', data)
}
