<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  id: { type: [Number, String], required: true },
  date: String,
  content: String,
  moodScore: { type: Number, default: null },
  aiReply: { type: String, default: '' },
})
const emit = defineEmits(['update', 'delete'])

const expanded = ref(false)
const editing = ref(false)
const editContent = ref('')
const editMoodScore = ref(0)
const editLoading = ref(false)
const confirmingDelete = ref(false)

const weekdays = ['日', '一', '二', '三', '四', '五', '六']

const dateLabel = computed(() => {
  if (!props.date) return ''
  try {
    const d = new Date(props.date)
    if (isNaN(d.getTime())) return props.date
    const m = d.getMonth() + 1
    const day = d.getDate()
    const w = weekdays[d.getDay()]
    return `${m}月${day}日 星期${w}`
  } catch {
    return props.date
  }
})

const preview = computed(() => {
  if (!props.content) return ''
  return props.content.length > 50
    ? props.content.slice(0, 50) + '...'
    : props.content
})

const moodLabel = computed(() => {
  const s = props.moodScore ?? 0
  if (s >= 5) return '精力充沛'
  if (s >= 4) return '状态良好'
  if (s >= 3) return '一般'
  if (s >= 2) return '有点疲惫'
  if (s >= 1) return '很累'
  return ''
})

function toggleExpand() {
  if (!editing.value) expanded.value = !expanded.value
}

function startEdit(e) {
  e.stopPropagation()
  editContent.value = props.content || ''
  editMoodScore.value = props.moodScore ?? 3
  editing.value = true
  expanded.value = true
}

function cancelEdit() {
  editing.value = false
  editContent.value = ''
  editMoodScore.value = 0
}

async function saveEdit() {
  if (!editContent.value.trim()) return
  editLoading.value = true
  emit('update', props.id, editContent.value.trim(), editMoodScore.value)
  // Parent will refresh list, so we exit edit mode optimistically
  editLoading.value = false
  editing.value = false
}

function requestDelete(e) {
  e.stopPropagation()
  confirmingDelete.value = true
}

function cancelDelete() {
  confirmingDelete.value = false
}

async function confirmDelete() {
  confirmingDelete.value = false
  emit('delete', props.id)
}
</script>

<template>
  <div class="sitem" :class="{ 'sitem--expanded': expanded }">
    <!-- Collapsed: summary row -->
    <div class="sitem__header" @click="toggleExpand">
      <div class="sitem__header-left">
        <span class="sitem__date">{{ dateLabel }}</span>
        <span v-if="moodScore" class="sitem__stars" :title="moodLabel">
          <template v-for="n in 5" :key="n">
            <span :class="n <= moodScore ? 'star--filled' : 'star--empty'">★</span>
          </template>
        </span>
        <span v-if="moodLabel" class="sitem__mood-label">{{ moodLabel }}</span>
      </div>
      <span class="sitem__caret">{{ expanded ? '▾' : '▸' }}</span>
    </div>

    <!-- Collapsed preview -->
    <p v-if="!expanded" class="sitem__preview">{{ preview }}</p>

    <!-- Expanded detail -->
    <div v-if="expanded" class="sitem__body">
      <template v-if="editing">
        <!-- Edit mode -->
        <div class="sitem__edit-mood">
          <span class="sitem__edit-label">精力评分：</span>
          <button
            v-for="n in 5" :key="n"
            class="sitem__star-btn"
            :class="{ 'sitem__star-btn--active': n <= editMoodScore }"
            @click="editMoodScore = n"
          >★</button>
        </div>
        <textarea
          v-model="editContent"
          class="textarea"
          style="min-height:100px"
          rows="4"
          :disabled="editLoading"
        />
        <div class="sitem__actions">
          <button class="act act--save" :disabled="editLoading" @click="saveEdit">保存</button>
          <button class="act" @click="cancelEdit">取消</button>
        </div>
      </template>
      <template v-else>
        <!-- View mode -->
        <p class="sitem__full-content">{{ content }}</p>
        <div v-if="aiReply" class="sitem__ai-reply">
          <p class="sitem__ai-label">AI 回复</p>
          <p class="sitem__ai-text">{{ aiReply }}</p>
        </div>
        <div class="sitem__actions">
          <button class="act" @click="startEdit">✎ 编辑</button>
          <button v-if="!confirmingDelete" class="act act--del" @click="requestDelete">✕ 删除</button>
          <!-- Inline delete confirmation -->
          <template v-else>
            <span class="sitem__confirm-text">确认删除？</span>
            <button class="act act--del" @click="confirmDelete">确认</button>
            <button class="act" @click="cancelDelete">取消</button>
          </template>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.sitem {
  padding: var(--space-4) 0;
  border-bottom: 1px solid var(--border-subtle);
  cursor: pointer;
  transition: opacity 0.2s;
}
.sitem:last-child { border-bottom: none; }
.sitem:hover { opacity: 0.92; }

.sitem__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-2);
}

.sitem__header-left {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}

.sitem__date {
  font-size: var(--text-xs);
  color: var(--text-dim);
  flex-shrink: 0;
}

.sitem__stars {
  display: inline-flex;
  gap: 1px;
  flex-shrink: 0;
}
.star--filled { color: var(--orange); font-size: 12px; }
.star--empty { color: var(--text-dim); opacity: 0.3; font-size: 12px; }

.sitem__mood-label {
  font-size: 10px;
  color: var(--text-dim);
  opacity: 0.6;
}

.sitem__caret {
  font-size: 12px;
  color: var(--text-dim);
  flex-shrink: 0;
  transition: transform 0.2s;
}

.sitem__preview {
  font-size: var(--text-sm);
  color: var(--text-dim);
  line-height: var(--leading-relaxed);
  margin-top: var(--space-2);
  padding-left: 0;
}

/* Expanded body — max-height transition */
.sitem__body {
  margin-top: var(--space-3);
  overflow: hidden;
  animation: expandIn 0.25s ease;
}

@keyframes expandIn {
  from { max-height: 0; opacity: 0; }
  to { max-height: 800px; opacity: 1; }
}

.sitem__full-content {
  font-size: var(--text-sm);
  color: var(--text);
  line-height: var(--leading-relaxed);
  white-space: pre-wrap;
  word-break: break-word;
  margin-bottom: var(--space-3);
}

.sitem__ai-reply {
  background: rgba(14, 9, 5, 0.5);
  border-left: 2px solid var(--orange);
  padding: var(--space-3) var(--space-4);
  margin-bottom: var(--space-3);
}
.sitem__ai-label {
  font-family: var(--font-display);
  font-size: 9px;
  color: var(--orange);
  letter-spacing: 0.5px;
  margin-bottom: var(--space-1);
  image-rendering: pixelated;
}
.sitem__ai-text {
  font-size: var(--text-sm);
  color: var(--text);
  line-height: var(--leading-relaxed);
  white-space: pre-wrap;
}

.sitem__edit-mood {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: var(--space-3);
}
.sitem__edit-label {
  font-size: var(--text-xs);
  color: var(--text-dim);
  margin-right: var(--space-2);
}
.sitem__star-btn {
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  color: var(--text-dim);
  opacity: 0.3;
  padding: 2px;
  transition: opacity 0.15s;
}
.sitem__star-btn--active {
  color: var(--orange);
  opacity: 1;
}
.sitem__star-btn:hover { opacity: 0.7; }

.sitem__actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.sitem__confirm-text {
  font-size: var(--text-xs);
  color: #c87070;
}

.act {
  font-family: var(--font-body);
  font-size: var(--text-xs);
  color: var(--text-dim);
  background: none;
  border: 1px solid var(--border-subtle);
  cursor: pointer;
  padding: 5px 12px;
  transition: color var(--duration-fast), border-color var(--duration-fast);
  min-height: 32px;
}
.act:hover { color: var(--text); border-color: rgba(224, 112, 48, 0.2); }
.act--save { color: var(--orange); border-color: rgba(224, 112, 48, 0.15); }
.act--save:hover { color: #e89868; border-color: rgba(224, 112, 48, 0.3); }
.act--del { color: var(--text-dim); border-color: rgba(200, 112, 112, 0.08); }
.act--del:hover { color: #c87070; border-color: rgba(200, 112, 112, 0.2); }
</style>
