<script setup>
import { ref } from 'vue'
import PixelButton from '@/components/shared/PixelButton.vue'

const emit = defineEmits(['submit'])
const props = defineProps({ submitting: Boolean })

const trackingNo = ref('')
const carrier = ref('')
const remark = ref('')
const carriers = ['顺丰','圆通','中通','申通','韵达','京东','EMS','极兔','其他']

function handleSubmit() {
  if (!trackingNo.value.trim()) return
  emit('submit', { trackingNo: trackingNo.value.trim(), carrier: carrier.value || '其他', remark: remark.value.trim() })
  trackingNo.value = ''; carrier.value = ''; remark.value = ''
}
</script>

<template>
  <div class="pform">
    <div class="pform-row">
      <input v-model="trackingNo" class="input" style="flex:1" placeholder="快递单号"
        :disabled="submitting" @keyup.enter="handleSubmit" />
      <PixelButton :disabled="!trackingNo.trim() || submitting" :loading="submitting" @click="handleSubmit">
        添加
      </PixelButton>
    </div>
    <div class="pform-row">
      <select v-model="carrier" class="select" style="flex:1">
        <option value="">选择快递公司</option>
        <option v-for="c in carriers" :key="c" :value="c">{{ c }}</option>
      </select>
      <input v-model="remark" class="input" style="flex:1" placeholder="备注（选填）" :disabled="submitting" />
    </div>
  </div>
</template>

<style scoped>
.pform { display: flex; flex-direction: column; gap: var(--space-2); }
.pform-row { display: flex; gap: var(--space-2); }
</style>
