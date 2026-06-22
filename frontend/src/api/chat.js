import api from './index.js'

export function sendChat(message, context = {}) {
  // 前端只发送用户输入和少量页面补充信息。
  // 真正可信的个人上下文由 Java 后端按登录用户重新查询。
  return api.post('/api/chat', { message, context }, { timeout: 75_000 }).then((r) => r.data)
}
