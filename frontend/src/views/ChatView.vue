<script setup>
import { computed, nextTick, ref } from 'vue'
import { sendChat } from '@/api/chat'
import { useKeepAliveEnter } from '@/composables/useKeepAliveEnter'

const { animateEnter } = useKeepAliveEnter()

const input = ref('')
const loading = ref(false)
const error = ref('')
const messages = ref([
  {
    role: 'assistant',
    text: '我会先理解你的需求，再结合今日规划、目标和最近总结来回答。你可以直接问：我现在该先做什么？',
    usedContext: [],
    toolResults: [],
  },
])
const scroller = ref(null)

const canSend = computed(() => input.value.trim() && !loading.value)

async function scrollToBottom() {
  await nextTick()
  if (scroller.value) {
    scroller.value.scrollTop = scroller.value.scrollHeight
  }
}

async function submit() {
  const text = input.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', text })
  input.value = ''
  error.value = ''
  loading.value = true
  await scrollToBottom()

  try {
    const res = await sendChat(text)
    messages.value.push({
      role: 'assistant',
      text: res.reply || '我暂时没有想好怎么回答。',
      needAnalysis: res.need_analysis || null,
      usedContext: res.used_context || [],
      toolResults: res.tool_results || [],
    })
  } catch (e) {
    error.value = e.message || '发送失败'
    messages.value.push({ role: 'assistant', text: '我这边暂时连不上，稍后再试。' })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}
</script>

<template>
  <div class="chat-page">
    <header class="chat-head" :class="animateEnter ? 'anim-enter anim-enter--1' : ''">
      <p class="chat-kicker">AGENT CHAT</p>
      <h1 class="chat-title">个人对话</h1>
      <p class="chat-sub">会结合今日规划、目标、总结和必要工具来分析你的问题。</p>
    </header>

    <section class="chat-shell" :class="animateEnter ? 'anim-enter anim-enter--2' : ''">
      <div ref="scroller" class="chat-log">
        <article
          v-for="(msg, index) in messages"
          :key="index"
          :class="['chat-msg', `chat-msg--${msg.role}`]"
        >
          <div class="chat-msg__meta">{{ msg.role === 'user' ? 'YOU' : 'DAYAGENT' }}</div>
          <p class="chat-msg__text">{{ msg.text }}</p>

          <div v-if="msg.role === 'assistant' && (msg.usedContext?.length || msg.toolResults?.length || msg.needAnalysis)" class="chat-trace">
            <p v-if="msg.needAnalysis?.intent" class="chat-trace__line">需求：{{ msg.needAnalysis.intent }}</p>
            <p v-if="msg.usedContext?.length" class="chat-trace__line">参考：{{ msg.usedContext.join(' / ') }}</p>
            <p v-if="msg.toolResults?.length" class="chat-trace__line">
              工具：{{ msg.toolResults.map((item) => item.name).join(' / ') }}
            </p>
          </div>
        </article>

        <div v-if="loading" class="chat-loading">分析中...</div>
      </div>

      <p v-if="error" class="chat-error">{{ error }}</p>

      <form class="chat-input" @submit.prevent="submit">
        <textarea
          v-model="input"
          class="chat-input__field"
          rows="3"
          placeholder="比如：我今天很累，但还有任务，应该怎么安排？"
          @keydown.enter.exact.prevent="submit"
        />
        <button class="chat-input__send" type="submit" :disabled="!canSend">
          发送
        </button>
      </form>
    </section>
  </div>
</template>

<style scoped>
.chat-page {
  min-height: 100%;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 18px;
  padding: 0 0 28px;
}

.chat-head { padding: 0 0 4px; }
.chat-kicker {
  font-family: var(--font-display);
  font-size: 9px;
  color: var(--weather-accent, var(--orange));
  letter-spacing: 1px;
  margin-bottom: 10px;
}
.chat-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  color: var(--text);
  margin: 0 0 8px;
}
.chat-sub {
  font-size: var(--text-sm);
  color: var(--text-dim);
  line-height: 1.7;
}

.chat-shell {
  min-height: 0;
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto auto;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.025), transparent 80px),
    rgba(12, 12, 10, 0.9);
  border: 1px solid rgba(224, 112, 48, 0.13);
  box-shadow: var(--shadow-lg);
}

.chat-log {
  min-height: 360px;
  max-height: calc(100vh - 260px);
  overflow-y: auto;
  padding: 20px;
}

.chat-msg {
  max-width: 760px;
  margin-bottom: 16px;
}
.chat-msg--user { margin-left: auto; }
.chat-msg__meta {
  font-family: var(--font-display);
  font-size: 8px;
  color: var(--text-faint);
  margin-bottom: 7px;
}
.chat-msg--user .chat-msg__meta { text-align: right; }
.chat-msg__text {
  white-space: pre-wrap;
  font-family: var(--font-body);
  font-size: 13px;
  line-height: 1.8;
  color: var(--text);
  padding: 13px 15px;
  border: 1px solid rgba(224, 112, 48, 0.12);
  background: rgba(255,255,255,0.024);
}
.chat-msg--user .chat-msg__text {
  color: #0b0a08;
  background: var(--weather-accent, var(--orange));
  border-color: var(--weather-accent, var(--orange));
}

.chat-trace {
  margin-top: 8px;
  padding: 9px 11px;
  border-left: 2px solid var(--weather-accent-line, rgba(224,112,48,0.24));
  background: rgba(255,255,255,0.018);
}
.chat-trace__line {
  font-size: 11px;
  color: var(--text-dim);
  line-height: 1.7;
}

.chat-loading,
.chat-error {
  font-size: 12px;
  color: var(--text-dim);
  padding: 0 20px 12px;
}
.chat-error { color: #c87070; }

.chat-input {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 84px;
  gap: 10px;
  padding: 14px;
  border-top: 1px solid rgba(224,112,48,0.1);
}
.chat-input__field {
  width: 100%;
  resize: none;
  font-family: var(--font-body);
  font-size: 13px;
  line-height: 1.7;
  color: var(--text);
  background: rgba(7, 7, 6, 0.76);
  border: 1px solid rgba(224, 112, 48, 0.15);
  outline: none;
  padding: 10px 12px;
}
.chat-input__field:focus {
  border-color: var(--weather-accent-line, rgba(224,112,48,0.3));
}
.chat-input__send {
  font-family: var(--font-body);
  font-size: 13px;
  color: #090a09;
  background: var(--weather-accent, var(--orange));
  border: 1px solid var(--weather-accent, var(--orange));
  cursor: pointer;
}
.chat-input__send:disabled {
  opacity: 0.34;
  cursor: not-allowed;
}

@media (max-width: 760px) {
  .chat-input { grid-template-columns: 1fr; }
  .chat-input__send { min-height: 36px; }
}
</style>
