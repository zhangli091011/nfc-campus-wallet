import request from '@/utils/request'

export interface Product {
  id: number
  booth_id: number
  name: string
  price: number // 单位：分
  cost_price?: number // 单位：分
  stock?: number | null
  enabled: boolean
  created_at: string
}

export interface CreateProductRequest {
  booth_id: number
  name: string
  price: number
  cost_price?: number
  stock?: number | null
}

export interface UpdateProductRequest {
  name?: string
  price?: number
  cost_price?: number
  stock?: number | null
  enabled?: boolean
}

// 获取商品列表
export const getProducts = (params?: {
  booth_id?: number
  enabled?: boolean
  limit?: number
  offset?: number
}) => {
  return request.get<any, Product[]>('/products', { params })
}

// 获取商品详情
export const getProduct = (id: number) => {
  return request.get<any, Product>(`/products/${id}`)
}

// 创建商品
export const createProduct = (data: CreateProductRequest) => {
  return request.post<any, Product>('/products', data)
}

// 更新商品
export const updateProduct = (id: number, data: UpdateProductRequest) => {
  return request.patch<any, Product>(`/products/${id}`, data)
}

// 删除商品 - 后端暂不支持
// export const deleteProduct = (id: number) => {
//   return request.delete(`/products/${id}`)
// }
