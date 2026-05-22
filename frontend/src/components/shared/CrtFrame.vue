<script setup>
defineProps({
  title: String,
  accent: Boolean,
})
</script>

<template>
  <div :class="['card', { 'card--accent': accent }]">
    <div v-if="title" class="frame-title">{{ title }}</div>
    <slot />
  </div>
</template>

<style scoped>
.frame-title {
  font-family: var(--font-display);
  font-size: 10px;
  color: var(--orange);
  letter-spacing: 1px;
  padding-bottom: var(--space-4);
  margin-bottom: var(--space-2);
  border-bottom: 1px solid var(--card-border);
  image-rendering: pixelated;
}
</style>
