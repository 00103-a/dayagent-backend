import api from './index.js'

export function fetchNews(goals = '', summary = '') {
  return api.get('/api/news', { params: { goals, summary } }).then((r) => r.data)
}
