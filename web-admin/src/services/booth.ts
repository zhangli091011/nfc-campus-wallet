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

// 删除摊位 - 后端暂不支持
// export const deleteBooth = (id: number) => {
//   return request.delete(`/booths/${id}`)
// }
