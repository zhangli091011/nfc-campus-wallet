import request from '@/utils/request'

export interface RefundRequestItem {
  id: number
  original_transaction_id: number
  requester_id: number
  requester_name: string
  booth_id: number | null
  reason: string
  status: 'pending' | 'approved' | 'rejected'
  approver_name: string | null
  approve_remark: string | null
  txn_amount: number
  card_uid: string | null
  txn_time: string | null
  created_at: string | null
  approved_at: string | null
}

export interface RefundRequestListResponse {
  requests: RefundRequestItem[]
  total_count: number
}

// 获取退款申请列表
export const getRefundRequests = (params: {
  status?: string
  limit?: number
  offset?: number
}) => {
  return request.get<any, RefundRequestListResponse>('/refund/requests', { params })
}

// 审批通过
export const approveRefundRequest = (id: number, remark?: string) => {
  return request.post<any, any>(`/refund/requests/${id}/approve`, { remark: remark || '' })
}

// 驳回
export const rejectRefundRequest = (id: number, remark?: string) => {
  return request.post<any, any>(`/refund/requests/${id}/reject`, { remark: remark || '' })
}
