import request from '@/utils/request'

// ============================================================================
// Types
// ============================================================================

export interface StockOrder {
  id: number
  event_id: number
  participant_id: number
  booth_id: number
  booth_name: string
  class_name: string
  shares: number
  buy_price: number
  buy_price_yuan: number
  total_amount: number
  total_amount_yuan: number
  status: 'holding' | 'settled'
  settlement_price?: number | null
  settlement_price_yuan?: number | null
  settlement_amount?: number | null
  settlement_amount_yuan?: number | null
  profit_loss?: number | null
  profit_loss_yuan?: number | null
  created_at: string
  settled_at?: string | null
}

export interface MarketStats {
  event_id: number
  total_investment: number
  total_investment_yuan: number
  global_pool: number
  global_pool_yuan: number
  fee_collected: number
  fee_collected_yuan: number
  total_orders: number
  total_investors: number
  total_booths: number
  is_settled: boolean
}

export interface BoothStockStats {
  booth_id: number
  booth_name: string
  class_name: string
  sold_shares: number
  total_investment: number
  total_investment_yuan: number
  investor_count: number
  current_price: number
  is_settled: boolean
  final_price?: number | null
}

export interface SettlementRequest {
  event_id: number
  fee_rate?: number
}

export interface SettlementResponse {
  success: boolean
  event_id: number
  global_pool: number
  global_pool_yuan: number
  total_investment: number
  total_investment_yuan: number
  fee_collected: number
  fee_collected_yuan: number
  total_score: number
  booth_count: number
  booths: Array<{
    booth_id: number
    booth_name: string
    class_name: string
    revenue: number
    revenue_yuan: number
    profit: number
    profit_yuan: number
    order_count: number
    score: number
    ratio: number
    sold_shares: number
    total_investment: number
    total_investment_yuan: number
    final_price: number
    final_price_yuan: number
  }>
  settled_at: string
  message: string
}

// ============================================================================
// API calls
// ============================================================================

/** 获取活动的股市统计 */
export const getMarketStats = (eventId: number) =>
  request.get<any, MarketStats>(`/api/stock/stats/${eventId}`)

/** 获取摊位股票统计 */
export const getBoothStockStats = (boothId: number, eventId: number) =>
  request.get<any, BoothStockStats>(`/api/stock/booth-stats/${boothId}`, {
    params: { event_id: eventId },
  })

/** 查询参与者股票订单 */
export const getParticipantOrders = (participantId: number, eventId?: number) =>
  request.get<any, StockOrder[]>(`/api/stock/orders/${participantId}`, {
    params: eventId ? { event_id: eventId } : undefined,
  })

/** 执行期末结算 */
export const settleStockMarket = (data: SettlementRequest) =>
  request.post<any, SettlementResponse>(`/api/stock/settle`, data)
