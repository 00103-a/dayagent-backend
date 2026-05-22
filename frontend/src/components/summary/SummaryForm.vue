<script setup>
import { ref } from 'vue'
import PixelButton from '@/components/shared/PixelButton.vue'

const emit = defineEmits(['submit'])
const props = defineProps({ submitting: Boolean })

const content = ref('')
const moodScore = ref(3)

function handleSubmit() {
  if (!content.value.trim()) return
  emit('submit', { content: content.value.trim(), moodScore: moodScore.value })
  content.value = ''
  moodScore.value = 3
}

defineExpose({ clear() { content.value = ''; moodScore.value = 3 } })
</script>

<template>
  <div class="form">
    <!-- Mood score -->
    <div class="form-mood">
      <span class="form-mood-label">精力评分：</span>
      <button
        v-for="n in 5" :key="n"
        class="form-mood-star"
        :class="{ 'form-mood-star--active': n <= moodScore }"
        :disabled="submitting"
        @click="moodScore = n"
      >★</button>
    </div>
    <textarea v-model="content" class="textarea" placeholder="记录一下今天做了什么..."
      :disabled="submitting" />
    <div class="form-foot">
      <PixelButton :disabled="!content.trim() || submitting" :loading="submitting" @click="handleSubmit">
        写总结
      </PixelButton>
    </div>
  </div>
</template>

<style scoped>
.form { display: flex; flex-direction: column; gap: var(--space-3); }
.form-foot { display: flex; justify-content: flex-end; }

.form-mood {
  display: flex;
  align-items: center;
  gap: 4px;
}
.form-mood-label {
  font-size: var(--text-xs);
  color: var(--text-dim);
  margin-right: var(--space-2);
}
.form-mood-star {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: var(--text-dim);
  opacity: 0.25;
  padding: 2px 1px;
  transition: opacity 0.15s;
}
.form-mood-star--active {
  color: var(--orange);
  opacity: 1;
}
.form-mood-star:hover:not(:disabled) { opacity: 0.7; }
.form-mood-star:disabled { cursor: default; }
</style>
