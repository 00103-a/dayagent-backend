/**
 * 用户认证与信息 Store
 * 应用唯一认证态出口，所有页面从 store 取用户信息，不走 props
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userId = ref(localStorage.getItem('userId') || '')
  const username = ref('')

  const isLoggedIn = computed(() => !!token.value)

  function login(t, uid, name) {
    token.value = t
    userId.value = String(uid)
    username.value = name
    localStorage.setItem('token', t)
    localStorage.setItem('userId', String(uid))
  }

  function logout() {
    // 清除当前用户的规划缓存
    if (userId.value) {
      sessionStorage.removeItem(`plan_${userId.value}`)
    }
    token.value = ''
    userId.value = ''
    username.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('userId')
    sessionStorage.removeItem('plan_auto_loaded')
  }

  return { token, userId, username, isLoggedIn, login, logout }
})
