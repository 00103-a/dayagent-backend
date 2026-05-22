import api from './index.js'

export function login(username, password) {
  return api.post('/api/user/login', { username, password }).then((r) => r.data)
}

export function register(username, password) {
  return api.post('/api/user/register', { username, password }).then((r) => r.data)
}
