<script setup>
defineProps({ text: { type: String, default: '还没有数据' } })
</script>

<template>
  <div class="empty-state">
    <div class="empty-state__icon">
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
        <circle cx="12" cy="12" r="2.5" fill="currentColor" opacity="0.25"/>
        <circle cx="20" cy="12" r="2.5" fill="currentColor" opacity="0.25"/>
        <circle cx="16" cy="16" r="11" stroke="currentColor" stroke-width="1.2" opacity="0.15"/>
      </svg>
    </div>
    <p class="empty-state__text">{{ text }}</p>
  </div>
</template>
