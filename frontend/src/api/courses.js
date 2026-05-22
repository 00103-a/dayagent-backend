import api from './index.js'

export function fetchCourses(weekFilter = null) {
  const params = {}
  if (weekFilter) params.week = weekFilter
  return api.get('/api/courses', { params }).then((r) => r.data)
}

export function importCourses() {
  return api.post('/api/courses/browser-import', {}, { timeout: 300_000 }).then((r) => r.data)
}

export function clearCourses() {
  return api.delete('/api/courses').then((r) => r.data)
}
