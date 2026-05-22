import api from './index.js'

/**
 * 从 Java 后端获取今日规划
 * 超时设 60s：Java → Python → LLM + 多源数据抓取可能较慢
 */
export function fetchPlan(userId, location = '南昌', forceRefresh = false) {
  return api
    .get('/api/plan', { params: { userId, location, forceRefresh }, timeout: 60_000 })
    .then((r) => r.data)
}
