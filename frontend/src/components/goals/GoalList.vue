<script setup>
import GoalItem from './GoalItem.vue'
defineProps({ items: { type: Array, default: () => [] } })
const emit = defineEmits(['toggle', 'delete', 'update'])
</script>

<template>
  <div>
    <GoalItem
      v-for="item in items" :key="item.id"
      :id="item.id"
      :content="item.content"
      :type="item.type"
      :status="item.status"
      :start-date="item.startDate"
      :end-date="item.endDate"
      @toggle="(id, s) => emit('toggle', id, s)"
      @delete="(id) => emit('delete', id)"
      @update="(id, content, endDate) => emit('update', id, content, endDate)"
    />
  </div>
</template>
