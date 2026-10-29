import axios from 'axios'
import { ElMessage } from 'element-plus'

export const API_BASE = import.meta.env.VITE_API_BASE || ''

const http = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = 'Bearer ' + token
  return config
})

http.interceptors.response.use(
  (res) => {
    const body = res.data
    if (body && typeof body.code === 'number' && body.code !== 0) {
      ElMessage.error(body.message || '请求失败')
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    return body
  },
  (err) => {
    const status = err.response?.status
    const msg = err.response?.data?.message || err.message || '网络错误'
    if (status === 401) {
      localStorage.removeItem('token')
      if (location.pathname !== '/login') location.href = '/login'
    }
    ElMessage.error(msg)
    return Promise.reject(err)
  },
)

export default http
