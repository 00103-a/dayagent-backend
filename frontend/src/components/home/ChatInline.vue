<script setup>
import { computed, ref } from 'vue'
import { sendChat } from '@/api/chat'

const props = defineProps({
  // Today 页传入的只是当前页面已有的轻量预览，帮助后端兼容页面场景。
  // Agent 真正使用的完整上下文仍由 Java ChatService 查询。
  plan: { type: Object, default: null },
  focusItems: { type: Array, default: () => [] },
})

const input = ref('')
const loading = ref(false)
const reply = ref('')
const error = ref('')
const trace = ref(null)

const canSend = computed(() => input.value.trim() && !loading.value)

async function ask() {
  const text = input.value.trim()
  if (!text || loading.value) return

  // 内嵌入口不保存完整聊天历史，只回答“此刻我该怎么办”这种短问题。
  loading.value = true
  error.value = ''
  reply.value = ''
  trace.value = null

  try {
    const res = await sendChat(text, {
      // 这些字段只是页面补充信息；后端不会信任它们作为唯一上下文来源。
      today_plan_preview: props.plan?.plan || '',
      focus_items: props.focusItems,
    })
    reply.value = res.reply || '我暂时没有想好怎么回答。'
    trace.value = {
      intent: res.need_analysis?.intent || '',
      usedContext: res.used_context || [],
      toolResults: res.tool_results || [],
    }
    input.value = ''
  } catch (e) {
    error.value = e.message || '发送失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="chat-inline">
    <div class="chat-inline__head">
      <h2 class="chat-inline__label">问问 DayAgent</h2>
      <span class="chat-inline__hint">会参考你的今日状态</span>
    </div>

    <form class="chat-inline__form" @submit.prevent="ask">
      <input
        v-model="input"
        class="chat-inline__input"
        placeholder="我现在该先做什么？"
      />
      <button class="chat-inline__btn" type="submit" :disabled="!canSend">
        {{ loading ? '分析' : '发送' }}
      </button>
    </form>

    <p v-if="error" class="chat-inline__error">{{ error }}</p>
    <div v-if="reply" class="chat-inline__reply">
      <p>{{ reply }}</p>
      <p v-if="trace?.usedContext?.length" class="chat-inline__trace">
        参考：{{ trace.usedContext.join(' / ') }}
      </p>
    </div>
  </section>
</template>

<style scoped>
.chat-inline {
  margin: 8px 0 18px;
  padding: 15px;
  border: 1px solid rgba(224,112,48,0.12);
  background: rgba(255,255,255,0.02);
}
.chat-inline__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.chat-inline__label {
  font-family: var(--font-display);
  font-size: 9px;
  color: var(--weather-accent, var(--orange));
  letter-spacing: 1px;
}
.chat-inline__hint {
  font-size: 11px;
  color: var(--text-faint);
}
.chat-inline__form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 70px;
  gap: 8px;
}
.chat-inline__input {
  min-width: 0;
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--text);
  background: rgba(7,7,6,0.72);
  border: 1px solid rgba(224,112,48,0.13);
  outline: none;
  padding: 9px 11px;
}
.chat-inline__input:focus {
  border-color: var(--weather-accent-line, rgba(224,112,48,0.3));
}
.chat-inline__btn {
  font-family: var(--font-body);
  font-size: 12px;
  color: #090a09;
  background: var(--weather-accent, var(--orange));
  border: 1px solid var(--weather-accent, var(--orange));
  cursor: pointer;
}
.chat-inline__btn:disabled { opacity: 0.35; cursor: not-allowed; }
.chat-inline__reply {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(224,112,48,0.09);
  font-size: 13px;
  line-height: 1.75;
  color: var(--text);
  white-space: pre-wrap;
}
.chat-inline__trace {
  margin-top: 8px;
  font-size: 11px;
  color: var(--text-dim);
}
.chat-inline__error {
  margin-top: 9px;
  font-size: 12px;
  color: #c87070;
}
</style>
