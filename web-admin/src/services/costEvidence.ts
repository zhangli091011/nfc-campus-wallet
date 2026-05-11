import request from '@/utils/request'

// ============================================================================
// 管理员成本凭据审核 API
// ============================================================================

export interface AdminCostEvidence {
  id: number
  booth_id: number
  booth_name: string
  class_name: string
  uploader_id: number
  filename: string
  file_size: number
  mime_type: string
  category: string
  amount: number | null
  description: string | null
  status: string
  reviewed_by: number | null
  reviewed_at: string | null
  created_at: string
}

export interface AdminCostEvidenceListResponse {
  evidences: AdminCostEvidence[]
  total_count: number
}

export interface AdminCostEvidenceStats {
  total_count: number
  total_amount: number
  pending_count: number
  by_status: Array<{
    status: string
    count: number
    total_amount: number
  }>
  by_category: Array<{
    category: string
    count: number
    total_amount: number
  }>
}

export interface ReviewRequest {
  action: 'approve' | 'reject'
  remark?: string
}

export interface BatchReviewRequest {
  ids: number[]
  action: 'approve' | 'reject'
}

export interface BatchReviewResponse {
  action: string
  requested_count: number
  updated_count: number
  message: string
}

// 获取所有凭据列表（管理员）
export const adminGetCostEvidences = (params?: {
  booth_id?: number
  category?: string
  status?: string
  limit?: number
  offset?: number
}) => {
  return request.get<any, AdminCostEvidenceListResponse>('/admin/cost-evidence', { params })
}

// 获取全局统计（管理员）
export const adminGetCostEvidenceStats = () => {
  return request.get<any, AdminCostEvidenceStats>('/admin/cost-evidence/stats')
}

// 获取单个凭据详情（管理员）
export const adminGetCostEvidenceDetail = (id: number) => {
  return request.get<any, AdminCostEvidence>(`/admin/cost-evidence/${id}`)
}

// 审核凭据（管理员）
export const adminReviewCostEvidence = (id: number, data: ReviewRequest) => {
  return request.post<any, any>(`/admin/cost-evidence/${id}/review`, data)
}

// 批量审核（管理员）
export const adminBatchReviewCostEvidences = (data: BatchReviewRequest) => {
  return request.post<any, BatchReviewResponse>('/admin/cost-evidence/batch-review', data)
}

// 获取凭据文件下载URL（管理员）
export const adminGetCostEvidenceFileUrl = (id: number) => {
  return `/api/admin/cost-evidence/${id}/file`
}
