<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const tabs = [
  { name: 'report', label: '汇报', path: '/report' },
  { name: 'summary', label: '总结', path: '/summary' },
  { name: 'goals', label: '目标', path: '/goals' },
  { name: 'life', label: '生活', path: '/life' },
  { name: 'settings', label: '设置', path: '/settings' },
]

const activeTab = computed(() => {
  const name = route.name
  return typeof name === 'string' ? name.toLowerCase() : 'report'
})
</script>

<template>
  <nav class="bottom-bar">
    <div class="bottom-bar__inner">
      <router-link
        v-for="tab in tabs"
        :key="tab.name"
        :to="tab.path"
        :class="['nav-item', { 'nav-item--active': activeTab === tab.name }]"
      >
        {{ tab.label }}
      </router-link>
    </div>
  </nav>
</template>

<style scoped>
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 10;
  padding: var(--space-3) var(--space-5);
  padding-bottom: max(var(--space-3), env(safe-area-inset-bottom));
  background: rgba(6, 4, 3, 0.82);
  backdrop-filter: blur(18px) saturate(1.2);
  -webkit-backdrop-filter: blur(18px) saturate(1.2);
  border-top: 1px solid rgba(224, 112, 48, 0.08);
}

.bottom-bar__inner {
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  justify-content: center;
  gap: var(--space-1);
}

.nav-item {
  padding: 6px 16px;
  image-rendering: pixelated;
  font-size: var(--text-sm);
  font-weight: var(--weight-normal);
  color: var(--text-dim);
  text-decoration: none;
  transition: color var(--duration-fast) var(--ease-out), background var(--duration-fast) var(--ease-out);
}

.nav-item:hover {
  color: var(--text);
  background: rgba(224, 112, 48, 0.05);
}

.nav-item--active {
  color: var(--orange);
  background: var(--orange-soft);
}
</style>
