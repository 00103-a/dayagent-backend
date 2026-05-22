<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  id: { type: [Number, String], required: true },
  content: String,
  type: String,
  status: String,
  startDate: String,
  endDate: String,
})
const emit = defineEmits(['toggle', 'delete', 'update'])

const expanded = ref(false)
const editing = ref(false)
const confirmingDelete = ref(false)
const editContent = ref('')
const editEndDate = ref('')
const editLoading = ref(false)

const typeLabel = computed(() => props.type === 'weekly' ? '周目标' : '月目标')
const isDone = computed(() => props.status === 'done')

const progressPct = computed(() => {
  if (!props.startDate || !props.endDate) return 0
  const start = new Date(props.startDate)
  const end = new Date(props.endDate)
  const now = new Date()
  if (now < start) return 0
  if (now > end) return 100
  const total = end.getTime() - start.getTime()
  if (total <= 0) return 0
  return Math.round(((now.getTime() - start.getTime()) / total) * 100)
})

const remainingDays = computed(() => {
  if (!props.endDate) return null
  const end = new Date(props.endDate)
  const now = new Date()
  const diff = Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
  if (diff < 0) return '已过期'
  if (diff === 0) return '今天截止'
  return `剩余 ${diff} 天`
})

function toggleExpand() {
  if (!editing.value) expanded.value = !expanded.value
}

function startEdit(e) {
  e.stopPropagation()
  editContent.value = props.content || ''
  editEndDate.value = props.endDate || ''
  editing.value = true
  expanded.value = true
}

function cancelEdit() { editing.value = false }

async function saveEdit() {
  if (!editContent.value.trim()) return
  editLoading.value = true
  emit('update', props.id, editContent.value.trim(), editEndDate.value || undefined)
  editLoading.value = false
  editing.value = false
}

function requestDelete(e) { e.stopPropagation(); confirmingDelete.value = true }
function cancelDelete() { confirmingDelete.value = false }
async function confirmDelete() { confirmingDelete.value = false; emit('delete', props.id) }

function handleToggle(e) {
  e.stopPropagation()
  emit('toggle', props.id, props.status)
}
</script>

<template>
  <div
    class="gitem"
    :class="{
      'gitem--done': isDone,
      'gitem--expanded': expanded
    }"
  >
    <!-- Header row -->
    <div class="gitem__header" @click="toggleExpand">
      <button class="gitem-check" @click="handleToggle" :title="isDone ? '取消完成' : '标记完成'">
        <svg v-if="isDone" width="18" height="18" viewBox="0 0 18 18" fill="none">
          <circle cx="9" cy="9" r="7.5" fill="#8aaa80" opacity="0.9"/>
          <path d="M5.5 9.5l2.5 2 4.5-5" stroke="#fff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <svg v-else width="18" height="18" viewBox="0 0 18 18" fill="none">
          <circle cx="9" cy="9" r="7.5" stroke="var(--text-dim)" stroke-width="1.2"/>
        </svg>
      </button>
      <span :class="['gitem-tag', props.type === 'weekly' ? 'gitem-tag--w' : 'gitem-tag--m']">
        {{ typeLabel }}
      </span>
      <span class="gitem-text">{{ content }}</span>
      <span class="gitem-caret">{{ expanded ? '▾' : '▸' }}</span>
    </div>

    <!-- Progress bar -->
    <div v-if="progressPct > 0 && !isDone" class="gitem__progress">
      <div class="gitem__progress-bar" :style="{ width: progressPct + '%' }" />
    </div>

    <!-- Expanded detail -->
    <div v-if="expanded" class="gitem__body">
      <template v-if="editing">
        <div class="gitem__edit-fields">
          <label class="gitem__label">目标内容</label>
          <textarea v-model="editContent" class="textarea" style="min-height:60px" rows="2" :disabled="editLoading" />
          <label class="gitem__label">结束日期</label>
          <input v-model="editEndDate" type="date" class="input" style="width:100%" :disabled="editLoading" />
        </div>
        <div class="gitem__actions">
          <button class="act act--save" :disabled="editLoading" @click="saveEdit">保存</button>
          <button class="act" @click="cancelEdit">取消</button>
        </div>
      </template>
      <template v-else>
        <div class="gitem__detail">
          <div v-if="startDate" class="gitem__detail-row">
            <span class="gitem__detail-label">开始</span>
            <span class="gitem__detail-value">{{ startDate }}</span>
          </div>
          <div v-if="endDate" class="gitem__detail-row">
            <span class="gitem__detail-label">截止</span>
            <span class="gitem__detail-value">{{ endDate }}</span>
          </div>
          <div class="gitem__detail-row">
            <span class="gitem__detail-label">状态</span>
            <span :class="['gitem__status', isDone ? 'gitem__status--done' : 'gitem__status--active']">
              {{ isDone ? '已完成' : '进行中' }}
            </span>
          </div>
          <div v-if="remainingDays" class="gitem__detail-row">
            <span class="gitem__detail-label">时间</span>
            <span class="gitem__detail-value">{{ remainingDays }}</span>
          </div>
          <div v-if="progressPct > 0 && !isDone" class="gitem__detail-row">
            <span class="gitem__detail-label">进度</span>
            <span class="gitem__detail-value">{{ progressPct }}%</span>
          </div>
        </div>

        <div class="gitem__actions">
          <button class="act" @click="startEdit">✎ 编辑</button>
          <button v-if="!isDone" class="act act--done" @click="(e) => { e.stopPropagation(); emit('toggle', props.id, props.status) }">✓ 标记完成</button>
          <template v-if="!confirmingDelete">
            <button class="act act--del" @click="requestDelete">✕ 删除</button>
          </template>
          <template v-else>
            <span class="gitem__confirm-text">确认删除？</span>
            <button class="act act--del" @click="confirmDelete">确认</button>
            <button class="act" @click="cancelDelete">取消</button>
          </template>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.gitem {
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--border-subtle);
  cursor: pointer;
  transition: opacity 0.2s, background 0.2s;
}
.gitem:last-child { border-bottom: none; }
.gitem--done { opacity: 0.45; }
.gitem--done .gitem-text { text-decoration: line-through; }
.gitem:hover { opacity: 0.92; }

.gitem__header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 36px;
}

.gitem-check {
  background: none; border: none; cursor: pointer; flex-shrink: 0; padding: 0; display: flex;
  transition: opacity var(--duration-fast);
}
.gitem-check:hover { opacity: 0.7; }

.gitem-tag {
  font-size: var(--text-2xs); font-weight: 600;
  padding: 2px 6px; image-rendering: pixelated; flex-shrink: 0;
}
.gitem-tag--w { color: var(--orange); background: var(--orange-soft); }
.gitem-tag--m { color: #c8a86e; background: rgba(200,168,110,0.1); }

.gitem-text {
  flex: 1; font-size: var(--text-sm); color: var(--text);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

.gitem-caret { font-size: 12px; color: var(--text-dim); flex-shrink: 0; }

/* Progress bar */
.gitem__progress {
  margin-top: var(--space-2);
  height: 3px;
  background: var(--border-subtle);
  border-radius: 0;
  overflow: hidden;
}
.gitem__progress-bar {
  height: 100%;
  background: var(--orange);
  transition: width 0.3s ease;
  image-rendering: pixelated;
}

/* Expanded body */
.gitem__body {
  margin-top: var(--space-3);
  animation: expandIn 0.25s ease;
  overflow: hidden;
}
@keyframes expandIn {
  from { max-height: 0; opacity: 0; }
  to { max-height: 600px; opacity: 1; }
}

.gitem__detail {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}
.gitem__detail-row {
  display: flex;
  gap: var(--space-3);
  align-items: center;
}
.gitem__detail-label {
  font-size: var(--text-xs);
  color: var(--text-dim);
  min-width: 40px;
  flex-shrink: 0;
}
.gitem__detail-value {
  font-size: var(--text-sm);
  color: var(--text);
}
.gitem__status {
  font-size: var(--text-xs);
  padding: 2px 8px;
}
.gitem__status--active { color: var(--orange); background: var(--orange-soft); }
.gitem__status--done { color: #8a9a80; background: rgba(140, 160, 130, 0.1); }

.gitem__edit-fields {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}
.gitem__label {
  font-size: var(--text-xs);
  color: var(--text-dim);
  margin-top: var(--space-1);
}

.gitem__actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}
.gitem__confirm-text { font-size: var(--text-xs); color: #c87070; }

.act {
  font-family: var(--font-body); font-size: var(--text-xs); color: var(--text-dim);
  background: none; border: 1px solid var(--border-subtle);
  cursor: pointer; padding: 5px 12px; min-height: 32px;
  transition: color var(--duration-fast), border-color var(--duration-fast);
}
.act:hover { color: var(--text); border-color: rgba(224, 112, 48, 0.2); }
.act--save { color: var(--orange); border-color: rgba(224, 112, 48, 0.15); }
.act--save:hover { color: #e89868; border-color: rgba(224, 112, 48, 0.3); }
.act--done { color: #8aaa80; border-color: rgba(140, 170, 128, 0.12); }
.act--done:hover { color: #9ab88a; border-color: rgba(140, 170, 128, 0.25); }
.act--del { color: var(--text-dim); border-color: rgba(200, 112, 112, 0.08); }
.act--del:hover { color: #c87070; border-color: rgba(200, 112, 112, 0.2); }
</style>
