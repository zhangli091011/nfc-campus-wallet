// 认证工具函数

const TOKEN_KEY = 'nfc_wallet_token'
const USER_KEY = 'nfc_wallet_user'

export interface User {
  id: number
  username: string
  role: 'super_admin' | 'event_admin' | 'booth_cashier' | 'issuer' | 'reviewer' | 'bank_clerk' | 'school_inspector'
  booth_id: number | null
  status: string
  created_at: string
}

// 保存 token
export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token)
}

// 获取 token
export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY)
}

// 移除 token
export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY)
}

// 保存用户信息
export const setUser = (user: User): void => {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

// 获取用户信息
export const getUser = (): User | null => {
  const userStr = localStorage.getItem(USER_KEY)
  if (!userStr) return null
  try {
    return JSON.parse(userStr)
  } catch {
    return null
  }
}

// 移除用户信息
export const removeUser = (): void => {
  localStorage.removeItem(USER_KEY)
}

// 清除所有认证信息
export const clearAuth = (): void => {
  removeToken()
  removeUser()
}

// 检查是否已登录
export const isAuthenticated = (): boolean => {
  return !!getToken()
}

// 检查用户角色
export const hasRole = (roles: string[]): boolean => {
  const user = getUser()
  if (!user) return false
  return roles.includes(user.role)
}

// 检查是否是管理员
export const isAdmin = (): boolean => {
  return hasRole(['super_admin', 'event_admin'])
}

// 检查是否是超级管理员
export const isSuperAdmin = (): boolean => {
  return hasRole(['super_admin'])
}

// 检查是否是校方巡查（只读角色）
export const isSchoolInspector = (): boolean => {
  return hasRole(['school_inspector'])
}

// 检查是否拥有写入权限（非只读角色）
export const canWrite = (): boolean => {
  return !isSchoolInspector()
}
