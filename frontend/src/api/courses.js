import api from './index.js'

export function fetchCourses(weekFilter = null) {
  const params = {}
  if (weekFilter) params.week = weekFilter
  return api.get('/api/courses', { params }).then((r) => r.data)
}

export async function importCourses() {
  if (!window.electronAPI?.importCoursesFromJwc) {
    throw new Error('Please use the Electron desktop app to import courses')
  }
  const payload = await window.electronAPI.importCoursesFromJwc()
  const data = await api.post('/api/courses/browser-import', payload, { timeout: 60_000 }).then((r) => r.data)
  if (data?.status === 'error') {
    throw new Error(data.message || 'Import failed')
  }
  return data
}

export function clearCourses() {
  return api.delete('/api/courses').then((r) => r.data)
}
