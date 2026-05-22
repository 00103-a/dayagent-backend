<script setup>
defineProps({
  loading: Boolean,
  disabled: Boolean,
  variant: { type: String, default: 'primary', validator: (v) => ['primary','secondary','danger','ghost'].includes(v) },
  size: { type: String, default: 'md', validator: (v) => ['sm','md','lg'].includes(v) },
  type: { type: String, default: 'button' },
})
defineEmits(['click'])
</script>

<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="['btn', `btn--${variant}`, size !== 'md' ? `btn--${size}` : '']"
    @click="$emit('click')"
  >
    <svg v-if="loading" class="spinner" width="15" height="15" viewBox="0 0 15 15" fill="none">
      <circle cx="7.5" cy="7.5" r="5.5" stroke="currentColor" stroke-opacity="0.25" stroke-width="1.5"/>
      <path d="M7.5 2a5.5 5.5 0 0 1 4.8 2.8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    </svg>
    <slot />
  </button>
</template>

<style scoped>
@keyframes spin { to { transform: rotate(360deg); } }
.spinner { animation: spin 0.8s linear infinite; }
</style>
