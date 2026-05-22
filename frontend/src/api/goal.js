import api from './index.js'

export function createGoal(userId, type, content, startDate, endDate) {
  return api.post('/api/goal', { userId, type, content, startDate, endDate }).then((r) => r.data)
}

export function getGoals(userId) {
  return api.get('/api/goal', { params: { userId } }).then((r) => r.data)
}

export function updateGoalStatus(goalId, status) {
  return api.put(`/api/goal/${goalId}`, { status }).then((r) => r.data)
}

export function updateGoal(goalId, data) {
  return api.put(`/api/goal/${goalId}`, data).then((r) => r.data)
}

export function deleteGoal(id) {
  return api.delete(`/api/goal/${id}`).then((r) => r.data)
}
