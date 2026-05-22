<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import SceneBackground from '@/components/shared/SceneBackground.vue'
import { weatherType } from '@/stores/weatherState'

const route = useRoute()

const isMaximized = ref(false)
const isElectron = typeof window !== 'undefined' && window.electronAPI?.isElectron

function minimize() { window.electronAPI?.minimize() }
function toggleMaximize() { window.electronAPI?.maximize() }
function closeWindow() { window.electronAPI?.close() }

onMounted(() => {
  if (isElectron) {
    window.electronAPI.onMaximizeChange((val) => { isMaximized.value = val })
  }
})

/* ── Auth gate ────────────────────────────────────────── */
const showShell = computed(() => route.name !== 'Login')

/* ── Today's date ─────────────────────────────────────── */
const weekdays = ['日', '一', '二', '三', '四', '五', '六']
const todayLabel = computed(() => {
  const d = new Date()
  const y = d.getFullYear()
  const m = d.getMonth() + 1
  const day = d.getDate()
  const w = weekdays[d.getDay()]
  return `${y}/${m}/${day} 星期${w}`
})

/* ── Navigation ───────────────────────────────────────── */
const navItems = [
  { name: 'Report', label: '今日', path: '/report' },
  { name: 'Summary', label: '日记', path: '/summary' },
  { name: 'Goals', label: '目标', path: '/goals' },
  { name: 'Life', label: '生活', path: '/life' },
  { name: 'Settings', label: '设置', path: '/settings' },
]

const activeNav = computed(() => route.name)

</script>

<template>
  <div class="app-shell" :class="{ 'app-shell--electron': isElectron }">

    <!-- ═══════════ Scene Background (global) ═══════════ -->
    <SceneBackground :weather-type="weatherType" />

    <!-- ═══════════ CRT scanlines overlay ═══════════ -->
    <div class="crt-overlay" aria-hidden="true" />

    <!-- ═══════════ Custom title bar (Electron only) ═══════════ -->
    <header v-if="isElectron && showShell" class="titlebar">
      <div class="titlebar__inner">
        <div class="titlebar__left">
          <span class="titlebar__dot" />
          <span class="titlebar__wordmark">DayAgent</span>
          <span class="titlebar__date">{{ todayLabel }}</span>
        </div>
        <div class="titlebar__center" />
        <div class="titlebar__controls">
          <button class="titlebar__ctrl" @click="minimize" title="Minimize">
            <svg width="8" height="8" viewBox="0 0 8 8"><path d="M1 4h6" stroke="currentColor" stroke-width="1"/></svg>
          </button>
          <button class="titlebar__ctrl" @click="toggleMaximize" title="Maximize">
            <svg v-if="!isMaximized" width="8" height="8" viewBox="0 0 8 8"><rect x="1" y="1" width="6" height="6" stroke="currentColor" stroke-width="1"/></svg>
            <svg v-else width="8" height="8" viewBox="0 0 8 8"><rect x="2" y="0" width="5" height="5" stroke="currentColor" stroke-width="1"/><path d="M0 2h5v5" stroke="currentColor" stroke-width="1"/></svg>
          </button>
          <button class="titlebar__ctrl titlebar__ctrl--close" @click="closeWindow" title="Close">
            <svg width="8" height="8" viewBox="0 0 8 8"><path d="M1 1l6 6M7 1l-6 6" stroke="currentColor" stroke-width="1"/></svg>
          </button>
        </div>
      </div>
    </header>

    <!-- ═══════════ Web fallback topbar ═══════════ -->
    <header v-else-if="showShell" class="app-topbar">
      <span class="titlebar__dot" />
      <span class="app-wordmark">DayAgent</span>
    </header>

    <!-- ═══════════ Body: sidebar + main ═══════════ -->
    <div v-if="showShell" class="app-body" :class="{ 'app-body--electron': isElectron }">

      <!-- ── Left Sidebar ──────────────────────────────── -->
      <nav class="sidebar">
        <div class="sidebar__inner">
          <div class="sidebar__logo">
            <span class="sidebar__dot" />
            <span class="sidebar__wordmark">DAY<br>AGENT</span>
          </div>

          <div class="sidebar__nav">
            <router-link
              v-for="item in navItems"
              :key="item.name"
              :to="item.path"
              :class="['nav-item', { 'nav-item--active': activeNav === item.name }]"
            >
              <span class="nav-item__caret" />
              <span class="nav-item__label">{{ item.label }}</span>
            </router-link>
          </div>

          <div class="sidebar__spacer" />
          <div class="sidebar__status">
            <span class="sidebar__status-dot" />
            <span class="sidebar__status-text">ONLINE</span>
          </div>
        </div>
      </nav>

      <!-- ── Main content ──────────────────────────────── -->
      <main class="main-content">
        <!-- Left gradient mask: blends sidebar edge into content -->
        <div class="main-content__gradient-left" aria-hidden="true" />
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <keep-alive>
              <component :is="Component" />
            </keep-alive>
          </transition>
        </router-view>
      </main>

    </div>

    <!-- ═══════════ Login page (fullscreen, no shell) ═══════════ -->
    <div v-else class="app-login">
      <router-view />
    </div>

  </div>
</template>

<style>
/* ── CSS Variables (global) — Pixel Art Palette ──────────── */
:root {
  --bg: #080604;
  --orange: #e07030;
  --orange-dim: #8b4a1f;
  --card: rgba(14, 9, 5, 0.75);
  --card-border: rgba(224, 112, 48, 0.13);
  --text: #c8b89a;
  --text-dim: #6b5a48;
  --nav-bg: rgba(6, 4, 3, 0.82);

  /* Extended palette */
  --orange-hover: #f08040;
  --orange-glow: rgba(224, 112, 48, 0.18);
  --orange-soft: rgba(224, 112, 48, 0.08);
  --border-subtle: rgba(224, 112, 48, 0.06);

  --font-display: 'Press Start 2P', 'zpix', monospace;
  --font-body: 'zpix', 'Press Start 2P', monospace;
  --font-content: 'zpix', monospace;  /* Chinese-dense areas: news, plans, courses */

  --radius-sm: 0px;
  --radius-md: 0px;
  --radius-lg: 0px;
  --radius-full: 0px;

  --shadow-sm: none;
  --shadow-md: none;
  --shadow-lg: none;

  --ease-out: steps(6);
  --ease-enter: cubic-bezier(0.25, 0.46, 0.45, 0.94);
  --duration-fast: 100ms;
  --duration-normal: 200ms;
  --duration-slow: 400ms;

  /* Type scale */
  --text-2xs: 11px;
  --text-xs: 12px;
  --text-sm: 13px;
  --text-base: 14px;
  --text-md: 15px;
  --text-lg: 16px;
  --text-xl: 18px;
  --text-2xl: 22px;

  /* Weights */
  --weight-normal: 400;

  /* Line heights */
  --leading-snug: 1.2;
  --leading-normal: 1.5;
  --leading-relaxed: 1.7;

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
}
</style>

<style scoped>
/* ═══════════════════════════════════════════════════════════
   App Shell
   ═══════════════════════════════════════════════════════════ */
.app-shell {
  height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  background: var(--bg);
  overflow: hidden;
}

/* ═══════════════════════════════════════════════════════════
   CRT overlay
   ═══════════════════════════════════════════════════════════ */
.crt-overlay {
  pointer-events: none;
  position: fixed;
  inset: 0;
  z-index: 998;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.04) 2px,
    rgba(0, 0, 0, 0.04) 4px
  );
}

/* ═══════════════════════════════════════════════════════════
   Titlebar (Electron) — 32px per spec
   ═══════════════════════════════════════════════════════════ */
.titlebar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: 32px;
  -webkit-app-region: drag;
  user-select: none;
  background: rgba(6, 4, 3, 0.82);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--card-border);
}

.titlebar__inner {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 10px;
}

.titlebar__left {
  display: flex;
  align-items: center;
  gap: 8px;
  -webkit-app-region: drag;
}

.titlebar__dot {
  width: 6px;
  height: 6px;
  background: var(--orange);
  box-shadow: 0 0 6px var(--orange), 0 0 12px var(--orange-glow);
  flex-shrink: 0;
  image-rendering: pixelated;
  animation: logoBreathe 3.5s ease-in-out infinite;
}

.titlebar__wordmark {
  font-family: var(--font-display);
  font-size: 11px;
  color: var(--orange);
  letter-spacing: 1px;
  -webkit-app-region: no-drag;
  image-rendering: pixelated;
}

.titlebar__date {
  font-family: var(--font-body);
  font-size: var(--text-2xs);
  color: var(--text-dim);
}

.titlebar__center { flex: 1; -webkit-app-region: drag; }

.titlebar__controls {
  display: flex;
  align-items: center;
  gap: 2px;
  -webkit-app-region: no-drag;
}

.titlebar__ctrl {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-dim);
  cursor: pointer;
  image-rendering: pixelated;
  transition: border-color 0.15s, background 0.15s, color 0.15s;
}
.titlebar__ctrl:hover {
  background: rgba(224, 112, 48, 0.08);
  border-color: rgba(224, 112, 48, 0.2);
  color: var(--text);
}
.titlebar__ctrl--close:hover {
  background: rgba(220, 60, 40, 0.7);
  border-color: rgba(220, 60, 40, 0.5);
  color: #fff;
}

/* ═══════════════════════════════════════════════════════════
   Web fallback topbar
   ═══════════════════════════════════════════════════════════ */
.app-topbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: rgba(6, 4, 3, 0.82);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--card-border);
}

.app-wordmark {
  font-family: var(--font-display);
  font-size: 11px;
  color: var(--orange);
  letter-spacing: 1px;
  image-rendering: pixelated;
}

/* ═══════════════════════════════════════════════════════════
   Body: sidebar (160px) + main
   ═══════════════════════════════════════════════════════════ */
.app-body {
  flex: 1;
  display: grid;
  grid-template-columns: 160px minmax(0, 1fr);
  width: 100%;
  max-width: 1440px;
  margin: 0 auto;
  padding: 48px 16px 24px 8px;
  gap: 0;
  position: relative;
  z-index: 1;
  overflow: hidden;
}

.app-body--electron {
  padding-top: calc(32px + 32px);
}

/* ═══════════════════════════════════════════════════════════
   Left Sidebar — 160px
   ═══════════════════════════════════════════════════════════ */
.sidebar {
  position: relative;
  display: flex;
  flex-direction: column;
}

.sidebar__inner {
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.sidebar__logo {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 0 0 28px 4px;
}

.sidebar__dot {
  width: 6px;
  height: 6px;
  margin-top: 2px;
  background: var(--orange);
  box-shadow: 0 0 6px var(--orange), 0 0 12px var(--orange-glow);
  flex-shrink: 0;
  image-rendering: pixelated;
  animation: logoBreathe 3.5s ease-in-out infinite;
}

.sidebar__wordmark {
  font-family: var(--font-display);
  font-size: 10px;
  color: var(--orange);
  line-height: 1.6;
  letter-spacing: 1px;
  image-rendering: pixelated;
  word-break: break-all;
}

/* ── Nav ────────────────────────────────────────────────── */
.sidebar__nav {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  text-decoration: none;
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--text-dim);
  position: relative;
  border: 1px solid transparent;
  transition: color 0.15s, background 0.15s, border-color 0.15s;
  cursor: pointer;
  image-rendering: pixelated;
}

.nav-item:hover {
  color: var(--text);
  background: rgba(224, 112, 48, 0.04);
  border-color: rgba(224, 112, 48, 0.08);
}

.nav-item__caret {
  width: 2px;
  height: 10px;
  flex-shrink: 0;
  opacity: 0;
  background: #e07030;
  image-rendering: pixelated;
  transition: opacity 0.1s;
}

.nav-item--active {
  color: #e07030;
  background: rgba(224, 112, 48, 0.10);
  border-color: rgba(224, 112, 48, 0.12);
}

.nav-item--active .nav-item__caret {
  opacity: 1;
}

.nav-item__label {
  position: relative;
  z-index: 1;
}

.sidebar__spacer {
  flex: 1;
}

.sidebar__status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  border-top: 1px solid var(--card-border);
}

.sidebar__status-dot {
  width: 6px;
  height: 6px;
  background: #4caf50;
  border-radius: 50%;
  box-shadow: 0 0 6px rgba(76, 175, 80, 0.5);
  animation: statusBlink 2s ease-in-out infinite;
}

.sidebar__status-text {
  font-family: var(--font-display);
  font-size: 9px;
  color: #5a8a40;
  letter-spacing: 1px;
  image-rendering: pixelated;
}

@keyframes statusBlink {
  0%, 100% { opacity: 1; box-shadow: 0 0 6px rgba(76, 175, 80, 0.5); }
  50% { opacity: 0.2; box-shadow: 0 0 2px rgba(76, 175, 80, 0.15); }
}

/* ═══════════════════════════════════════════════════════════
   Main Content
   ═══════════════════════════════════════════════════════════ */
.main-content {
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0 4px 0 12px;
  min-height: 0;
  position: relative;
}

/* Left gradient mask — blends scene background into content cards */
.main-content__gradient-left {
  pointer-events: none;
  position: fixed;
  top: 0;
  left: 0;
  width: 200px;
  height: 100vh;
  z-index: 0;
  background: linear-gradient(
    90deg,
    rgba(6,4,3,0.85) 0%,
    rgba(6,4,3,0.6) 60%,
    transparent 100%
  );
}

/* ═══════════════════════════════════════════════════════════
   Login fullscreen
   ═══════════════════════════════════════════════════════════ */
.app-login {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;
}

/* ═══════════════════════════════════════════════════════════
   Page transitions — 150ms fade, no slide (smooth in Electron)
   ═══════════════════════════════════════════════════════════ */
.page-enter-active,
.page-leave-active {
  transition: opacity 0.15s ease;
}
.page-enter-from { opacity: 0; }
.page-leave-to { opacity: 0; }

/* ═══════════════════════════════════════════════════════════
   Logo breathing
   ═══════════════════════════════════════════════════════════ */
@keyframes logoBreathe {
  0%, 100% { box-shadow: 0 0 6px var(--orange), 0 0 12px var(--orange-glow); }
  50% { box-shadow: 0 0 10px var(--orange), 0 0 20px rgba(224, 112, 48, 0.3); }
}
</style>
