import request from '@/utils/request'
import { User } from '@/utils/auth'

export interface CreateUserRequest {
  username: string
  password: string
  role: 'super_admin' | 'event_admin' | 'booth_cashier' | 'issuer' | 'reviewer'
  booth_id?: number | null
}

// 获取用户列表
export const getUsers = (params?: {
  role?: string
  booth_id?: number
  status?: string
  limit?: number
  offset?: number
}) => {
  return request.get<any, User[]>('/users', { params })
}

// 获取用户详情
export const getUser = (id: number) => {
  return request.get<any, User>(`/users/${id}`)
}

// 创建用户
export const createUser = (data: CreateUserRequest) => {
  return request.post<any, User>('/users', data)
}

// 更新用户状态
export const updateUserStatus = (id: number, status: 'active' | 'inactive' | 'blocked') => {
  return request.patch<any, User>(`/users/${id}/status`, null, {
    params: { status }
  })
}
