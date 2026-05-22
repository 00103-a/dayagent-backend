<script setup>
import SummaryItem from './SummaryItem.vue'
defineProps({ items: { type: Array, default: () => [] } })
const emit = defineEmits(['update', 'delete'])
</script>

<template>
  <div>
    <SummaryItem
      v-for="item in items" :key="item.id || item.summaryDate"
      :id="item.id"
      :date="item.summaryDate || item.createdAt"
      :content="item.content"
      :mood-score="item.moodScore"
      :ai-reply="item.aiReply"
      @update="(id, content, moodScore) => emit('update', id, content, moodScore)"
      @delete="(id) => emit('delete', id)"
    />
  </div>
</template>
