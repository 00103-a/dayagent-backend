<script setup>
defineProps({ lines: { type: Number, default: 3 } })
</script>

<template>
  <div class="card">
    <div
      v-for="i in lines" :key="i"
      class="skeleton"
      :style="{ height: '13px', width: (92 - (i-1)*11) + '%', marginBottom: i < lines ? 'var(--space-3)' : '0' }"
    />
  </div>
</template>
