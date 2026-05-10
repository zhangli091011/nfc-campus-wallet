/**
 * 退款监控服务
 */
import request from '@/utils/request'

// ============================================================================
// Types
// ============================================================================

export interface RefundSummary {
  total_refund_count: number
  total_refund_amount: number
  total_refund_amount_yuan: number
  total_pay_count: number
  total_pay_amount: number
  total_pay_amount_yuan: number
  overall_refund_rate: number
}

export interface BoothRefundRank {
  booth_id: number
  booth_name: string
  class_name: string
  refund_count: number
  pay_count: number
  refund_amount: number
  refund_amount_yuan: number
  refund_rate: number
}

export interface RefundAlert {
  booth_id: number
  booth_name: string
  class_name: string
  refund_count_in_window: number
  window_minutes: number
  alert_level: 'warning' | 'critical'
  latest_refund_time: string
}

export interface RefundReasonStat {
  reason: string
  count: number
  amount: number
  amount_yuan: number
  percentage: number
}

export interface RefundMonitorResponse {
  summary: RefundSummary
  top_refund_booths: BoothRefundRank[]
  alerts: RefundAlert[]
  reason_distribution: RefundReasonStat[]
}

export interface RefundDetail {
  id: number
  original_transaction_id: number | null
  amount: number
  amount_yuan: number
  booth_id: number | null
  booth_name: string | null
  participant_id: number | null
  participant_name: string | null
  card_uid: string | null
  reason: string
  operator_name: string | null
  created_at: string
}

export interface RefundDetailResponse {
  refunds: RefundDetail[]
  total_count: number
}

// ============================================================================
// API Functions
// ============================================================================

/** 获取退款监控统计 */
export const getRefundMonitorStats = (params?: {
  event_id?: number
  alert_window_minutes?: number
  alert_threshold?: number
}): Promise<RefundMonitorResponse> => {
  return request.get('/refund-monitor/stats', { params })
}

/** 获取退款明细列表 */
export const getRefundDetails = (params?: {
  event_id?: number
  booth_id?: number
  reason_keyword?: string
  start_date?: string
  end_date?: string
  limit?: number
  offset?: number
}): Promise<RefundDetailResponse> => {
  return request.get('/refund-monitor/details', { params })
}
