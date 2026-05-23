<script setup>
import { ref } from 'vue'
import PixelButton from '@/components/shared/PixelButton.vue'

const emit = defineEmits(['submit'])
const props = defineProps({ submitting: Boolean })

const content = ref('')
const type = ref('weekly')

function handleSubmit() {
  if (!content.value.trim()) return
  const today = new Date()
  const startDate = today.toISOString().slice(0, 10)
  const end = new Date(today)
  if (type.value === 'weekly') {
    end.setDate(end.getDate() + 7)
  } else {
    end.setMonth(end.getMonth() + 1)
  }
  const endDate = end.toISOString().slice(0, 10)
  emit('submit', { type: type.value, content: content.value.trim(), startDate, endDate })
  content.value = ''
}
</script>

<template>
  <div class="row">
    <select v-model="type" class="select" style="width:110px;flex-shrink:0">
      <option value="weekly">周目标</option>
      <option value="monthly">月目标</option>
    </select>
    <input v-model="content" class="input" style="flex:1" placeholder="新目标..."
      :disabled="submitting" @keyup.enter="handleSubmit" />
    <PixelButton :disabled="!content.trim() || submitting" :loading="submitting" @click="handleSubmit">
      添加
    </PixelButton>
  </div>
</template>

<style scoped>
.row { display: flex; gap: var(--space-2); align-items: center; }
</style>
