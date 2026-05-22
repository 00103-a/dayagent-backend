<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  trackingNo: String, carrier: String, remark: String, status: String,
  isDelivered: Boolean, deleting: Boolean, trackDetails: Array,
})
defineEmits(['delete'])

const expanded = ref(false)
const hasTrack = computed(() => props.trackDetails && props.trackDetails.length > 0)

function toggle() {
  if (hasTrack.value) expanded.value = !expanded.value
}
</script>

<template>
  <div :class="['pitem', { 'pitem--done': isDelivered }]">
    <div class="pitem-body">
      <div class="pitem-head">
        <span :class="['tag', isDelivered ? 'tag--done' : 'tag--active']">{{ carrier }}</span>
        <span v-if="remark" class="pitem-rem">{{ remark }}</span>
      </div>
      <p class="pitem-no">{{ trackingNo }}</p>
      <p v-if="status" class="pitem-st" :class="{ 'pitem-st--link': hasTrack }" @click="toggle">
        {{ status }}
        <span v-if="hasTrack" class="pitem-arrow">{{ expanded ? '&#9650;' : '&#9660;' }}</span>
      </p>
      <!-- Track timeline -->
      <div v-if="expanded && hasTrack" class="track-timeline">
        <div v-for="(t, i) in trackDetails" :key="i" class="track-item">
          <div class="track-dot" :class="{ 'track-dot--latest': i === 0 }" />
          <div class="track-content">
            <p class="track-time">{{ t.time || t.ftime || '' }}</p>
            <p class="track-context">{{ t.context }}</p>
          </div>
        </div>
      </div>
    </div>
    <button class="pitem-del" :disabled="deleting" @click="$emit('delete')">
      <svg v-if="deleting" class="spinner" width="14" height="14" viewBox="0 0 14 14" fill="none">
        <circle cx="7" cy="7" r="5.5" stroke="currentColor" stroke-opacity="0.25" stroke-width="1.5"/>
        <path d="M7 1.5a5.5 5.5 0 0 1 4.8 2.8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
      <svg v-else width="14" height="14" viewBox="0 0 14 14" fill="none">
        <path d="M2.5 2.5l9 9M11.5 2.5l-9 9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
    </button>
  </div>
</template>

<style scoped>
@keyframes spin { to { transform: rotate(360deg); } }
.spinner { animation: spin 0.8s linear infinite; }

.pitem { display: flex; align-items: flex-start; gap: var(--space-3); padding: var(--space-4) 0; border-bottom: 1px solid var(--border-subtle); }
.pitem:last-child { border-bottom: none; }
.pitem--done { opacity: 0.45; }
.pitem-body { flex: 1; min-width: 0; }
.pitem-head { display: flex; align-items: center; gap: var(--space-2); margin-bottom: var(--space-1); }
.pitem-rem { font-size: var(--text-xs); color: var(--text-dim); }
.pitem-no { font-size: var(--text-sm); color: var(--text); margin-bottom: 1px; }
.pitem-st { font-size: var(--text-xs); color: var(--text-dim); }
.pitem-st--link { cursor: pointer; user-select: none; }
.pitem-st--link:hover { color: var(--orange); }
.pitem-arrow { font-size: 10px; margin-left: 4px; }
.pitem-del {
  background: none; border: none; cursor: pointer; flex-shrink: 0; padding: 4px; display: flex;
  align-items: center; color: var(--text-dim); transition: color var(--duration-fast); image-rendering: pixelated;
}
.pitem-del:hover:not(:disabled) { color: #c87070; background: rgba(200,112,112,0.08); }
.pitem-del:disabled { cursor: not-allowed; opacity: 0.5; }

/* Track timeline */
.track-timeline {
  margin-top: var(--space-3);
  padding-left: var(--space-1);
}
.track-item {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-1) 0;
  position: relative;
}
.track-item::before {
  content: '';
  position: absolute;
  left: 4px;
  top: 12px;
  bottom: -2px;
  width: 1px;
  background: var(--border-subtle);
}
.track-item:last-child::before { display: none; }
.track-dot {
  width: 9px; height: 9px; image-rendering: pixelated;
  background: var(--card-border);
  flex-shrink: 0; margin-top: 3px; position: relative; z-index: 1;
}
.track-dot--latest {
  background: var(--orange);
  box-shadow: 0 0 6px var(--orange-glow);
}
.track-content { min-width: 0; }
.track-time {
  font-size: var(--text-2xs);
  color: var(--text-dim);
  margin-bottom: 1px;
}
.track-context {
  font-size: var(--text-xs);
  color: var(--text-dim);
  line-height: var(--leading-snug);
}
</style>
