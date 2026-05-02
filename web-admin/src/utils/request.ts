import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios'
import { message } from 'antd'
import { getToken, clearAuth } from './auth'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 添加 token
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error: AxiosError<any>) => {
    // 处理错误响应
    if (error.response) {
      const { status, data } = error.response

      // 401 未授权 - 清除登录信息并跳转到登录页
      if (status === 401) {
        message.error(data?.message || '登录已过期，请重新登录')
        clearAuth()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      // 403 权限不足
      if (status === 403) {
        message.error(data?.message || '权限不足')
        return Promise.reject(error)
      }

      // 404 资源不存在
      if (status === 404) {
        message.error(data?.message || '请求的资源不存在')
        return Promise.reject(error)
      }

      // 400 请求错误
      if (status === 400) {
        message.error(data?.message || '请求参数错误')
        return Promise.reject(error)
      }

      // 500 服务器错误
      if (status === 500) {
        message.error(data?.message || '服务器错误，请稍后重试')
        return Promise.reject(error)
      }

      // 其他错误
      message.error(data?.message || '请求失败')
    } else if (error.request) {
      // 请求已发出但没有收到响应
      message.error('网络错误，请检查网络连接')
    } else {
      // 其他错误
      message.error('请求失败')
    }

    return Promise.reject(error)
  }
)

export default request
