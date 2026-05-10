import request from '@/utils/request'

// ============================================================================
// 商户 API 接口类型定义
// ============================================================================

export interface MerchantInfo {
  user_id: number
  username: string
  booth_id: number
  booth_name: string
  class_name: string
  status: string
}

export interface MerchantLoginResponse {
  access_token: string
  token_type: string
  merchant: MerchantInfo
}

export interface MerchantRegisterRequest {
  username: string
  password: string
  booth_name: string
  class_name: string
}

export interface MerchantLoginRequest {
  username: string
  password: string
}

export interface MerchantProduct {
  id: number
  name: string
  price: number
  cost_price: number | null
  stock: number | null
  enabled: boolean
  created_at: string
}

export interface MerchantBoothInfo {
  booth_id: number
  booth_name: string
  class_name: string
  status: string
  event_id: number
  created_at: string
  products: MerchantProduct[]
}

export interface MerchantBoothUpdateRequest {
  booth_name?: string
  class_name?: string
}

export interface MerchantProductCreateRequest {
  name: string
  price: number
  cost_price?: number
  stock?: number
}

export interface MerchantProductUpdateRequest {
  name?: string
  price?: number
  cost_price?: number
  stock?: number
  enabled?: boolean
}

export interface MerchantIncomeStats {
  booth_id: number
  booth_name: string
  total_income: number
  total_transactions: number
  today_income: number
  today_transactions: number
}

export interface MerchantTransaction {
  id: number
  type: string
  amount: number
  product_name: string | null
  remark: string | null
  created_at: string
}

export interface MerchantTransactionHistory {
  transactions: MerchantTransaction[]
  total_count: number
}

// ============================================================================
// 商户 API 调用
// ============================================================================

// 商户注册
export const merchantRegister = (data: MerchantRegisterRequest) => {
  return request.post<any, MerchantLoginResponse>('/merchant/register', data)
}

// 商户登录
export const merchantLogin = (data: MerchantLoginRequest) => {
  return request.post<any, MerchantLoginResponse>('/merchant/login', data)
}

// 获取商铺信息
export const getMerchantBooth = () => {
  return request.get<any, MerchantBoothInfo>('/merchant/booth')
}

// 更新商铺信息
export const updateMerchantBooth = (data: MerchantBoothUpdateRequest) => {
  return request.put<any, MerchantBoothInfo>('/merchant/booth', data)
}

// 添加商品
export const addMerchantProduct = (data: MerchantProductCreateRequest) => {
  return request.post<any, MerchantProduct>('/merchant/products', data)
}

// 更新商品
export const updateMerchantProduct = (id: number, data: MerchantProductUpdateRequest) => {
  return request.put<any, MerchantProduct>(`/merchant/products/${id}`, data)
}

// 删除商品
export const deleteMerchantProduct = (id: number) => {
  return request.delete<any, void>(`/merchant/products/${id}`)
}

// 获取收入统计
export const getMerchantIncome = () => {
  return request.get<any, MerchantIncomeStats>('/merchant/income')
}

// 获取交易记录
export const getMerchantTransactions = (params?: {
  limit?: number
  offset?: number
  start_date?: string
  end_date?: string
}) => {
  return request.get<any, MerchantTransactionHistory>('/merchant/transactions', { params })
}

// ============================================================================
// 成本凭据 API
// ============================================================================

export interface CostEvidence {
  id: number
  booth_id: number
  filename: string
  file_size: number
  mime_type: string
  category: string
  amount: number | null
  description: string | null
  status: string
  reviewed_by?: number | null
  reviewed_at?: string | null
  created_at: string
}

export interface CostEvidenceListResponse {
  evidences: CostEvidence[]
  total_count: number
}

export interface CostEvidenceStats {
  booth_id: number
  total_count: number
  total_amount: number
  by_category: Array<{
    category: string
    count: number
    total_amount: number
  }>
  by_status: Array<{
    status: string
    count: number
  }>
}

// 上传成本凭据
export const uploadCostEvidence = (formData: FormData) => {
  // 注意：不要手动设置 Content-Type，让浏览器自动设置包含 boundary 的 multipart/form-data
  return request.post<any, CostEvidence>('/merchant/cost-evidence', formData)
}

// 获取成本凭据列表
export const getCostEvidences = (params?: {
  category?: string
  status?: string
  limit?: number
  offset?: number
}) => {
  return request.get<any, CostEvidenceListResponse>('/merchant/cost-evidence', { params })
}

// 获取单个凭据详情
export const getCostEvidenceDetail = (id: number) => {
  return request.get<any, CostEvidence>(`/merchant/cost-evidence/${id}`)
}

// 删除凭据
export const deleteCostEvidence = (id: number) => {
  return request.delete<any, void>(`/merchant/cost-evidence/${id}`)
}

// 获取凭据统计
export const getCostEvidenceStats = () => {
  return request.get<any, CostEvidenceStats>('/merchant/cost-evidence/stats/summary')
}

// 获取凭据文件下载URL
export const getCostEvidenceFileUrl = (id: number) => {
  return `/api/merchant/cost-evidence/${id}/file`
}
