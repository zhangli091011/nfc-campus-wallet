import request from '@/utils/request'

export interface DiscountSetting {
  configured: boolean
  id?: number
  event_id: number
  enabled: boolean
  min_discount_amount: number
  max_discount_amount: number
  probability: number
  total_pool: number
  remaining_pool: number
  max_discount_per_transaction: number | null
  min_payment_amount: number
  daily_limit_per_user: number | null
  created_at?: string
  updated_at?: string
}

export interface DiscountSettingRequest {
  event_id: number
  enabled: boolean
  min_discount_amount: number
  max_discount_amount: number
  probability: number
  total_pool: number
  max_discount_per_transaction?: number | null
  min_payment_amount: number
  daily_limit_per_user?: number | null
}

export interface DiscountStatistics {
  configured: boolean
  enabled: boolean
  total_pool: number
  remaining_pool: number
  used_pool: number
  total_discount_count: number
  total_discount_amount: number
  today_discount_count: number
  today_discount_amount: number
  min_discount_amount?: number
  max_discount_amount?: number
  probability?: number
  min_payment_amount?: number
  daily_limit_per_user?: number | null
}

export interface DiscountRecord {
  id: number
  participant_id: number
  transaction_id: number
  booth_id: number | null
  original_amount: number
  discount_amount: number
  actual_amount: number
  created_at: string
}

export interface DiscountRecordsResponse {
  records: DiscountRecord[]
  total_count: number
}

// 获取随机立减配置
export const getDiscountSetting = (eventId: number) => {
  return request.get<any, DiscountSetting>(`/random-discount/settings/${eventId}`)
}

// 创建或更新随机立减配置
export const saveDiscountSetting = (data: DiscountSettingRequest) => {
  return request.post<any, any>('/random-discount/settings', data)
}

// 重置奖池
export const resetDiscountPool = (eventId: number, newPool?: number) => {
  return request.post<any, any>(`/random-discount/settings/${eventId}/reset-pool`, {
    new_pool: newPool || null,
  })
}

// 获取统计信息
export const getDiscountStatistics = (eventId: number) => {
  return request.get<any, DiscountStatistics>(`/random-discount/statistics/${eventId}`)
}

// 获取立减记录
export const getDiscountRecords = (
  eventId: number,
  params?: { participant_id?: number; limit?: number; offset?: number }
) => {
  return request.get<any, DiscountRecordsResponse>(`/random-discount/records/${eventId}`, {
    params,
  })
}
