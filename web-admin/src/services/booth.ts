import request from '@/utils/request'

export interface Booth {
  id: number
  event_id: number
  name: string
  class_name: string
  status: 'active' | 'inactive' | 'closed'
  created_at: string
}

export interface CreateBoothRequest {
  event_id: number
  name: string
  class_name: string
}

export interface UpdateBoothRequest {
  name?: string
  class_name?: string
  status?: 'active' | 'inactive' | 'closed'
}

export interface BoothCredential {
  booth_id: number
  booth_name: string
  username: string
  password: string | null
  user_id: number | null
  user_status: string | null
}

export interface BoothCashier {
  id: number
  username: string
  status: string
  created_at: string
}

export interface GenerateCredentialRequest {
  username?: string
  password?: string
}

// 获取摊位列表
export const getBooths = (params?: {
  event_id?: number
  status?: string
  limit?: number
  offset?: number
}) => {
  return request.get<any, Booth[]>('/booths', { params })
}

// 获取摊位详情
export const getBooth = (id: number) => {
  return request.get<any, Booth>(`/booths/${id}`)
}

// 创建摊位
export const createBooth = (data: CreateBoothRequest) => {
  return request.post<any, Booth>('/booths', data)
}

// 更新摊位
export const updateBooth = (id: number, data: UpdateBoothRequest) => {
  return request.patch<any, Booth>(`/booths/${id}`, data)
}

// 获取摊位登录凭据
export const getBoothCredentials = (boothId: number) => {
  return request.get<any, BoothCredential>(`/booths/${boothId}/credentials`)
}

// 生成/重置摊位登录凭据
export const generateBoothCredentials = (boothId: number, data?: GenerateCredentialRequest) => {
  return request.post<any, BoothCredential>(`/booths/${boothId}/credentials`, data || {})
}

// 获取摊位收银员列表
export const getBoothCashiers = (boothId: number) => {
  return request.get<any, BoothCashier[]>(`/booths/${boothId}/cashiers`)
}

// 指定收银员到摊位
export const assignCashierToBooth = (boothId: number, userId: number) => {
  return request.post<any, any>(`/booths/${boothId}/cashiers`, { user_id: userId })
}
