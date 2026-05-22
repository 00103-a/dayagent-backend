<script setup>
import ParcelItem from './ParcelItem.vue'
defineProps({
  items: { type: Array, default: () => [] },
  deletingId: { type: [String,Number], default: null },
})
defineEmits(['delete'])
</script>

<template>
  <div>
    <ParcelItem
      v-for="item in items" :key="item.id"
      :tracking-no="item.trackingNo" :carrier="item.carrier" :remark="item.remark"
      :status="item.status" :is-delivered="item.isDelivered"
      :deleting="deletingId === item.id"
      @delete="$emit('delete', item.id)"
    />
  </div>
</template>
