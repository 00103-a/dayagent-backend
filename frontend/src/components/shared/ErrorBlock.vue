<script setup>
import PixelButton from './PixelButton.vue'
defineProps({
  message: { type: String, default: '未知错误' },
  canRetry: Boolean,
})
defineEmits(['retry'])
</script>

<template>
  <div class="error-block">
    <svg class="error-block__icon" width="18" height="18" viewBox="0 0 18 18" fill="none">
      <circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.5"/>
      <path d="M9 5.5v3.5M9 12.2v.3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
    </svg>
    <p class="error-block__msg">{{ message }}</p>
    <PixelButton v-if="canRetry" variant="secondary" size="sm" @click="$emit('retry')">重试</PixelButton>
  </div>
</template>
