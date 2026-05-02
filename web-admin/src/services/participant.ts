import request from '@/utils/request'

export interface Participant {
  id: number
  card_uid: string
  name: string
  student_id?: string
  class_name?: string
  status: 'active' | 'inactive' | 'blocked'
  created_at: string
}

export interface CreateParticipantRequest {
  card_uid: string
  name: string
  student_id?: string
  class_name?: string
}

export interface UpdateParticipantRequest {
  name?: string
  student_id?: string
  class_name?: string
  status?: 'active' | 'inactive' | 'blocked'
}

export interface RechargeRequest {
  event_id: number
  card_uid: string
  amount: number
  remark?: string
}

// 获取参与者列表
export const getParticipants = (params?: {
  event_id?: number
  status?: string
  search?: string
  limit?: number
  offset?: number
}) => {
  return request.get<any, Participant[]>('/participants', { params })
}

// 获取参与者详情
export const getParticipant = (id: number) => {
  return request.get<any, Participant>(`/participants/${id}`)
}

// 创建参与者
export const createParticipant = (data: CreateParticipantRequest) => {
  return request.post<any, Participant>('/participants', data)
}

// 更新参与者
export const updateParticipant = (id: number, data: UpdateParticipantRequest) => {
  return request.patch<any, Participant>(`/participants/${id}`, data)
}

// 充值
export const recharge = (data: RechargeRequest) => {
  return request.post('/recharge', data)
}

// 查询余额
export const getBalance = (params: { event_id: number; card_uid: string }) => {
  return request.get('/balance', { params })
}
