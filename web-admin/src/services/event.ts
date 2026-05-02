import request from '@/utils/request'

export interface Event {
  id: number
  name: string
  description?: string
  start_date: string
  end_date: string
  status: 'pending' | 'active' | 'ended' | 'cancelled'
  created_at: string
}

export interface CreateEventRequest {
  name: string
  description?: string
  start_date: string
  end_date: string
}

export interface UpdateEventRequest {
  name?: string
  description?: string
  start_date?: string
  end_date?: string
  status?: 'pending' | 'active' | 'ended' | 'cancelled'
}

// 获取活动列表
export const getEvents = (params?: {
  status?: string
  limit?: number
  offset?: number
}) => {
  return request.get<any, Event[]>('/events', { params })
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

// 删除活动
export const deleteEvent = (id: number) => {
  return request.delete(`/events/${id}`)
}
