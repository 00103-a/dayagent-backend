<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { login, register } from '@/api/auth'

const router = useRouter()
const userStore = useUserStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const isRegister = ref(false)

async function handleSubmit() {
  if (!username.value.trim() || !password.value.trim()) {
    error.value = '请填写用户名和密码'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const fn = isRegister.value ? register : login
    const data = await fn(username.value.trim(), password.value.trim())
    if (isRegister.value) {
      const loginData = await login(username.value.trim(), password.value.trim())
      userStore.login(loginData.token, loginData.userId, loginData.username)
    } else {
      userStore.login(data.token, data.userId, data.username)
    }
    router.replace('/report')
  } catch (e) {
    error.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}

function toggleMode() {
  isRegister.value = !isRegister.value
  error.value = ''
}
</script>

<template>
  <div class="login-page">
    <!-- Ambient glow -->
    <div class="login-glow" />

    <!-- Logo -->
    <div class="login-hero">
      <div class="login-dot" />
      <h1 class="login-title">DayAgent</h1>
      <p class="login-sub">你的 AI 每日状态空间</p>
    </div>

    <!-- Form -->
    <div class="login-card anim-enter anim-enter--1">
      <div v-if="error" class="banner banner--err" style="margin-bottom:var(--space-4)">{{ error }}</div>

      <div class="login-fields">
        <input
          v-model="username"
          class="input"
          placeholder="用户名"
          :disabled="loading"
          autocomplete="username"
          @keyup.enter="handleSubmit"
        />
        <input
          v-model="password"
          class="input"
          type="password"
          placeholder="密码"
          :disabled="loading"
          autocomplete="current-password"
          @keyup.enter="handleSubmit"
        />
      </div>

      <button
        class="login-btn"
        :disabled="!username.trim() || !password.trim() || loading"
        @click="handleSubmit"
      >
        <span v-if="loading" class="login-btn__spinner" />
        <span v-else>{{ isRegister ? '创建账号' : '登录' }}</span>
      </button>

      <p class="login-toggle">
        {{ isRegister ? '已有账号？' : '没有账号？' }}
        <a href="#" @click.prevent="toggleMode">{{ isRegister ? '去登录' : '去注册' }}</a>
      </p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 48px 24px;
  gap: 40px;
  max-width: 400px;
  margin: 0 auto;
  position: relative;
}

/* ── Ambient glow ──────────────────────────────────────── */
.login-glow {
  position: fixed;
  top: -20%;
  left: 50%;
  transform: translateX(-50%);
  width: 500px;
  height: 400px;
  background: radial-gradient(ellipse at center, rgba(224, 112, 48, 0.06) 0%, transparent 70%);
  pointer-events: none;
}

/* ── Hero ──────────────────────────────────────────────── */
.login-hero {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.login-dot {
  width: 9px;
  height: 9px;
  image-rendering: pixelated;
  background: var(--orange);
  box-shadow: 0 0 12px var(--orange-glow), 0 0 28px rgba(224, 112, 48, 0.2);
  animation: logoBreathe 3.5s ease-in-out infinite;
}

.login-title {
  font-family: var(--font-display);
  font-size: var(--text-3xl);
  font-weight: 600;
  image-rendering: pixelated;
  color: var(--text);
  letter-spacing: -1.5px;
  margin: 0;
}

.login-sub {
  font-size: var(--text-base);
  font-weight: 400;
  color: var(--text-dim);
  margin: 0;
}

/* ── Card ──────────────────────────────────────────────── */
.login-card {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 28px;
  background: var(--card);
  border: 1px solid var(--card-border);
  image-rendering: pixelated;
}

.login-fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ── Button ────────────────────────────────────────────── */
.login-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 400;
  color: #fff;
  background: var(--orange);
  border: none;
  image-rendering: pixelated;
  padding: 12px 24px;
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-out), box-shadow var(--duration-fast) var(--ease-out), transform var(--duration-fast) var(--ease-out);
  box-shadow: 0 2px 8px rgba(224, 112, 48, 0.3);
}
.login-btn:hover:not(:disabled) {
  box-shadow: 0 4px 16px rgba(224, 112, 48, 0.3);
  transform: translateY(-1px);
}
.login-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.login-btn__spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  image-rendering: pixelated;
  animation: spin 0.7s linear infinite;
}

/* ── Toggle ────────────────────────────────────────────── */
.login-toggle {
  text-align: center;
  font-size: var(--text-sm);
  font-weight: 400;
  color: var(--text-dim);
  margin: 0;
}

.login-toggle a {
  color: var(--orange);
  text-decoration: none;
  font-weight: 400;
}
.login-toggle a:hover {
  color: var(--orange-hover);
}

</style>
