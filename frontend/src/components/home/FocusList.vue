<script setup>
defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})
</script>

<template>
  <section class="focus" :class="{ 'focus--loading': loading }">
    <h2 class="focus__label">今日重点</h2>

    <div v-if="items.length" class="focus__list">
      <div
        v-for="(item, i) in items.slice(0, 5)"
        :key="i"
        class="focus__item"
        :style="{ animationDelay: `${i * 0.06}s` }"
      >
        <span class="focus__index">{{ i + 1 }}</span>
        <p class="focus__text">{{ item }}</p>
      </div>
    </div>

    <p v-else class="focus__empty">
      放松一下也不错，不用每天都紧绷。
    </p>
  </section>
</template>

<style scoped>
.focus {
  padding: 0 0 32px;
}

.focus--loading {
  opacity: 0.4;
}

.focus__label {
  font-family: var(--font-display);
  font-size: 10px;
  color: var(--orange);
  letter-spacing: 1px;
  image-rendering: pixelated;
  margin-bottom: 16px;
}

.focus__list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.focus__item {
  display: flex;
  align-items: baseline;
  gap: 16px;
  padding: 16px 0;
  border-bottom: 1px solid var(--border-subtle);
  animation: fadeInUp 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
  transition: transform var(--duration-fast) var(--ease-out);
}

.focus__item:last-child {
  border-bottom: none;
}

.focus__item:hover {
  transform: translateX(4px);
}

.focus__index {
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 500;
  image-rendering: pixelated;
  color: var(--orange);
  opacity: 0.55;
  min-width: 16px;
  flex-shrink: 0;
}

.focus__text {
  font-family: var(--font-body);
  font-size: var(--text-base);
  font-weight: 400;
  color: var(--text);
  line-height: 1.55;
  margin: 0;
}

.focus__empty {
  font-family: var(--font-body);
  font-size: var(--text-base);
  font-weight: 400;
  color: var(--text-dim);
  image-rendering: pixelated;
  padding: 8px 0;
  margin: 0;
}
</style>
