import api from './index.js'

export function submitSummary(userId, content, moodScore) {
  const body = { userId, content }
  if (moodScore !== undefined && moodScore !== null) body.moodScore = moodScore
  return api.post('/api/summary', body).then((r) => r.data)
}

export function getSummaries(userId) {
  return api.get('/api/summary', { params: { userId } }).then((r) => r.data)
}

export function updateSummary(id, content, moodScore) {
  const body = { content }
  if (moodScore !== undefined && moodScore !== null) body.moodScore = moodScore
  return api.put(`/api/summary/${id}`, body).then((r) => r.data)
}

export function deleteSummary(id) {
  return api.delete(`/api/summary/${id}`).then((r) => r.data)
}
