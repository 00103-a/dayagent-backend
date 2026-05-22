/**
 * Axios 实例 — 应用唯一 HTTP 入口
 * 统一注入 JWT token、规范化错误、处理 401
 */
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '',
  timeout: 30_000,
})

/* ── 请求拦截：统一注入 token ────────────────────────────────────────────────── */
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/* ── 响应拦截：解包 Result 包装器 + 统一错误归一化 ───────────────────────────── */
api.interceptors.response.use(
  (res) => {
    const d = res.data
    // Java 后端统一返回 Result<T> = {code, message, data}
    // 自动解包，前端只拿到 data 字段
    if (d && typeof d === 'object' && 'code' in d) {
      if (d.code === 200) {
        return { ...res, data: d.data }
      }
      // 业务错误
      // code=401: token 过期/无效，清除登录态并跳转
      if (d.code === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('userId')
        window.location.hash = '#/login'
        return Promise.reject(new Error(d.message || 'Token 已过期，请重新登录'))
      }
      return Promise.reject(new Error(d.message || '请求失败'))
    }
    // 非 Result 包装的响应（如 Python 服务返回）原样透传
    return res
  },
  (err) => {
    // HTTP 401（JWT 过期/无效）
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('userId')
      window.location.hash = '#/login'
    }

    const message =
      err.response?.data?.message ||
      err.response?.data?.error ||
      err.response?.data?.detail ||
      err.message ||
      '网络错误'

    return Promise.reject(new Error(message))
  }
)

export default api
