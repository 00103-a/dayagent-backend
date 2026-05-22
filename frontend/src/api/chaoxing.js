import api from './index.js'

export function fetchChaoxingTasks() {
  return api.get('/api/chaoxing/tasks').then((r) => r.data)
}
