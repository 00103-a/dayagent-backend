<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useKeepAliveEnter } from '@/composables/useKeepAliveEnter'

const userStore = useUserStore()
const router = useRouter()
const { animateEnter } = useKeepAliveEnter()

function doLogout() {
  userStore.logout()
  router.replace('/login')
}
</script>

<template>
  <div class="page">
    <!-- Header -->
    <header class="page__header">
      <h1 class="page__title">设置</h1>
      <p class="page__sub">账号与偏好设置。</p>
    </header>

    <!-- User info -->
    <section :class="animateEnter ? 'page__section anim-enter anim-enter--1' : 'page__section'">
      <h2 class="section__label">用户信息</h2>
      <div class="info-list">
        <div class="info-row">
          <span class="info-l">用户名</span>
          <span class="info-v">{{ userStore.username || '未登录' }}</span>
        </div>
        <div class="info-row">
          <span class="info-l">ID</span>
          <span class="info-v info-v--mono">{{ userStore.userId }}</span>
        </div>
      </div>
    </section>

    <!-- Logout -->
    <section :class="animateEnter ? 'page__section anim-enter anim-enter--2' : 'page__section'">
      <h2 class="section__label">账户</h2>
      <p class="hint">退出当前账号，返回登录页面</p>
      <button class="logout-btn" @click="doLogout">退出登录</button>
    </section>

    <p class="footer">DayAgent v0.2</p>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding-bottom: 40px;
}

.page__header {
  padding: 0 0 32px;
}

.page__title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 500;
  image-rendering: pixelated;
  color: var(--text);
  letter-spacing: -1px;
  margin: 0 0 6px;
}

.page__sub {
  font-size: var(--text-sm);
  font-weight: 400;
  color: var(--text-dim);
  margin: 0;
}

.page__section {
  padding: 0 0 28px;
}

.section__label {
  font-family: var(--font-display);
  font-size: 10px;
  color: var(--orange);
  letter-spacing: 1px;
  image-rendering: pixelated;
  margin-bottom: 14px;
}

/* ── Info ──────────────────────────────────────────────── */
.info-list {
  border: 1px solid var(--border-subtle);
  overflow: hidden;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
}

.info-row + .info-row {
  border-top: 1px solid var(--border-subtle);
}

.info-l {
  font-size: var(--text-sm);
  font-weight: 400;
  color: var(--text-dim);
}

.info-v {
  font-size: var(--text-sm);
  font-weight: 400;
  color: var(--text);
}

.info-v--mono {
  font-size: var(--text-xs);
  color: var(--text);
}

/* ── Logout ────────────────────────────────────────────── */
.hint {
  font-size: var(--text-sm);
  font-weight: 400;
  color: var(--text-dim);
  line-height: 1.6;
  margin: 0 0 16px;
}

.logout-btn {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 400;
  color: #c87070;
  background: transparent;
  border: 1px solid rgba(200, 112, 112, 0.18);
  padding: 8px 20px;
  image-rendering: pixelated;
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-out), border-color var(--duration-fast) var(--ease-out);
}
.logout-btn:hover {
  background: rgba(200, 112, 112, 0.08);
  border-color: rgba(200, 112, 112, 0.35);
}

/* ── Footer ────────────────────────────────────────────── */
.footer {
  text-align: center;
  padding: 32px 0 16px;
  font-size: var(--text-2xs);
  font-weight: 400;
  color: var(--text-dim);
  opacity: 0.5;
}

</style>
