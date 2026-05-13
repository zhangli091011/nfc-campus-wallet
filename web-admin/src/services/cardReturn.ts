import request from '@/utils/request'

export interface CardReturnRecord {
  id: number
  name: string
  class_name: string | null
  student_no: string | null
  original_card_uid: string
  balance_at_return: number
  refunded_amount: number
  return_time: string | null
  operator_name: string | null
  loan_count: number
  loan_total_principal: number
  loan_remaining_debt: number
  created_at: string | null
}

export interface CardReturnListResponse {
  records: CardReturnRecord[]
  total_count: number
  event_id: number
}

export interface TransactionItem {
  id: number
  type: string
  amount: number
  balance_before: number
  balance_after: number
  remark: string | null
  operator_id: string | null
  booth_id: number | null
  merchant_id: string | null
  created_at: string | null
}

export interface LoanItem {
  id: number
  principal_amount: number
  fee_amount: number
  disbursed_amount: number
  status: string
  remark: string | null
  created_at: string | null
  repaid_at: string | null
}

export interface CardReturnDetail {
  participant: {
    id: number
    name: string
    class_name: string | null
    student_no: string | null
    original_card_uid: string
    status: string
    created_at: string | null
  }
  account: {
    balance: number
    credit_borrowed: number
    credit_fee_paid: number
  } | null
  transactions: TransactionItem[]
  loans: LoanItem[]
  transaction_count: number
  loan_count: number
}

// 获取退卡记录列表
export const getCardReturnRecords = (params: {
  event_id: number
  search?: string
  limit?: number
  offset?: number
}) => {
  return request.get<any, CardReturnListResponse>('/admin/card-returns', { params })
}

// 获取退卡记录明细（含全部流水）
export const getCardReturnDetail = (participantId: number, eventId: number) => {
  return request.get<any, CardReturnDetail>(`/admin/card-returns/${participantId}/detail`, {
    params: { event_id: eventId },
  })
}
