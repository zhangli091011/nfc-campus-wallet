import request from '@/utils/request'

export interface Event {
  id: number
  name: string
  start_time: string
  end_time: string
  status: 'draft' | 'active' | 'paused' | 'ended'
  recharge_enabled: boolean
  consume_enabled: boolean
  expire_rule: string
  created_at: string
  updated_at: string
}

export interface CreateEventRequest {
  name: string
  start_time: string
  end_time: string
  status?: 'draft' | 'active' | 'paused' | 'ended'
  recharge_enabled?: boolean
  consume_enabled?: boolean
  expire_rule?: string
}

export interface UpdateEventRequest {
  name?: string
  start_time?: string
  end_time?: string
  status?: 'draft' | 'active' | 'paused' | 'ended'
  recharge_enabled?: boolean
  consume_enabled?: boolean
  expire_rule?: string
}

export interface EventListResponse {
  events: Event[]
  total_count: number
}

// 获取活动列表
export const getEvents = (params?: {
  status?: string
  limit?: number
  offset?: number
}) => {
  return request.get<any, EventListResponse>('/events', { params })
}

// 获取活动详情
export const getEvent = (id: number) => {
  return request.get<any, Event>(`/events/${id}`)
}

// 创建活动
export const createEvent = (data: CreateEventRequest) => {
  return request.post<any, Event>('/events', data)
}

// 更新活动
export const updateEvent = (id: number, data: UpdateEventRequest) => {
  return request.patch<any, Event>(`/events/${id}`, data)
}

// 删除活动 - 后端暂不支持
// export const deleteEvent = (id: number) => {
//   return request.delete(`/events/${id}`)
// }
