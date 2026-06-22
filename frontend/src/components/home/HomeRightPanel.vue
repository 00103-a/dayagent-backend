<script setup>
import { ref } from 'vue'
import { fetchWeather } from '@/api/weather'
import { weatherType, weatherShort as sharedWeatherShort, weatherTemp as sharedWeatherTemp } from '@/stores/weatherState'
import { deriveWeatherType, formatWeather } from '@/utils/weather'

const props = defineProps({
  weatherText: { type: String, default: '' },
  weatherTemp: { type: Number, default: null },
  weatherLoading: { type: Boolean, default: false },
  parcelItems: { type: Array, default: () => [] },
  parcelsLoading: { type: Boolean, default: false },
  newsLines: { type: Array, default: () => [] },
  newsLoading: { type: Boolean, default: false },
  location: { type: String, default: '' },
})

/* ── Weather independent refresh ────────────────────────── */
const weatherRefreshing = ref(false)
const localWeatherText = ref('')
const localWeatherTemp = ref(null)

async function refreshWeather() {
  weatherRefreshing.value = true
  try {
    const data = await fetchWeather({ location: props.location })
    const fmt = formatWeather(data.weather || '')
    localWeatherText.value = fmt.text
    localWeatherTemp.value = fmt.temp
    sharedWeatherShort.value = fmt.text
    sharedWeatherTemp.value = fmt.temp
    const wt = deriveWeatherType(data.condition_text || fmt.text || '')
    weatherType.value = wt
  } catch {
    // degrade silently
  } finally {
    weatherRefreshing.value = false
  }
}

/* ── Display helpers ─────────────────────────────────────── */
function displayText() { return localWeatherText.value || props.weatherText }
function displayTemp() {
  if (localWeatherTemp.value !== null) return localWeatherTemp.value
  return props.weatherTemp
}
</script>

<template>
  <div class="rpanel">

    <!-- ═══════════ Weather ═══════════ -->
    <div class="rpanel__block">
      <div class="rpanel__header">
        <p class="rpanel__label">天气</p>
        <button
          class="rpanel__refresh"
          :class="{ 'rpanel__refresh--spin': weatherRefreshing || weatherLoading }"
          @click="refreshWeather"
          title="刷新天气"
        >
          <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
            <path d="M1 5A4 4 0 0 1 8.6 3.2M9 5A4 4 0 0 1 1.4 6.8" stroke="currentColor" stroke-width="1" stroke-linecap="round"/>
            <path d="M8.6 3.2H6.8M1.4 6.8H3.2" stroke="currentColor" stroke-width="1" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
      <div class="rpanel__divider" />
      <p v-if="weatherLoading && !displayText()" class="rpanel__dim">加载中&hellip;</p>
      <p v-else-if="displayText()" class="rpanel__text">
        {{ props.location }}<br />
        {{ displayText() }}
        <template v-if="displayTemp() !== null">&middot; {{ displayTemp() }}&deg;C</template>
      </p>
      <p v-else class="rpanel__dim">暂无数据</p>
    </div>

    <!-- ═══════════ Parcels ═══════════ -->
    <div v-if="parcelItems.length || parcelsLoading" class="rpanel__block">
      <div class="rpanel__header">
        <p class="rpanel__label">快递</p>
        <!-- Pixel parcel icon 16x16 -->
        <svg class="rpanel__icon" width="16" height="16" viewBox="0 0 16 16" shape-rendering="crispEdges">
          <rect x="2" y="4" width="12" height="10" fill="#8b4a1f" stroke="#e07030" stroke-width="1" />
          <rect x="2" y="4" width="12" height="3" fill="#a06030" />
          <line x1="8" y1="4" x2="8" y2="14" stroke="#e07030" stroke-width="1" />
          <line x1="2" y1="9" x2="14" y2="9" stroke="#e07030" stroke-width="0.5" opacity="0.5" />
        </svg>
      </div>
      <div class="rpanel__divider" />
      <p v-if="parcelsLoading && !parcelItems.length" class="rpanel__dim">查询中&hellip;</p>
      <template v-else>
        <p
          v-for="(p, i) in parcelItems.slice(0, 3)"
          :key="i"
          class="rpanel__text rpanel__parcel"
        >
          <span class="rpanel__parcel-dot" :class="{ 'rpanel__parcel-dot--done': p.isDelivered }" />
          {{ p.remark || p.trackingNo }}
          <span class="rpanel__dim">&mdash; {{ p.status || '运输中' }}</span>
        </p>
      </template>
    </div>

    <!-- ═══════════ News ═══════════ -->
    <div v-if="newsLines.length || newsLoading" class="rpanel__block">
      <p class="rpanel__label">新闻摘要</p>
      <div class="rpanel__divider" />
      <p v-if="newsLoading && !newsLines.length" class="rpanel__dim">加载中&hellip;</p>
      <template v-else>
        <p
          v-for="(line, i) in newsLines.slice(0, 3)"
          :key="i"
          class="rpanel__text rpanel__news"
        >
          {{ line.replace(/^·\s*/, '') }}
        </p>
      </template>
    </div>

    <!-- ═══════════ Footer whisper ═══════════ -->
    <p class="rpanel__whisper">
      数据随时间刷新 &middot; 下拉可手动更新
    </p>

  </div>
</template>

<style scoped>
.rpanel {
  display: flex;
  flex-direction: column;
  padding-top: 4px;
}

/* ── Block spacing (item 5) ────────────────────────────── */
.rpanel__block {
  margin-bottom: 20px;
}

.rpanel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.rpanel__label {
  font-family: var(--font-display);
  font-size: 9px;
  color: var(--orange);
  letter-spacing: 1px;
  image-rendering: pixelated;
  margin: 0;
}

/* Divider line under title (item 5) */
.rpanel__divider {
  height: 1px;
  background: rgba(224, 112, 48, 0.15);
  margin: 8px 0 10px;
}

/* ── Weather refresh button (item 11) ─────────────────── */
.rpanel__refresh {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: 1px solid rgba(224, 112, 48, 0.15);
  background: transparent;
  color: var(--text-dim);
  cursor: pointer;
  flex-shrink: 0;
  transition: border-color 0.15s, color 0.15s;
}
.rpanel__refresh:hover {
  border-color: rgba(224, 112, 48, 0.3);
  color: var(--orange);
}
.rpanel__refresh--spin svg {
  animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Pixel parcel icon (item 2) ────────────────────────── */
.rpanel__icon {
  image-rendering: pixelated;
  flex-shrink: 0;
}

.rpanel__text {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 400;
  color: var(--text);
  line-height: 1.65;
  margin: 0 0 6px;
}

.rpanel__dim {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 400;
  color: var(--text-dim);
  image-rendering: pixelated;
  margin: 0;
}

/* ── Parcel dot ────────────────────────────────────────── */
.rpanel__parcel {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.rpanel__parcel-dot {
  width: 5px;
  height: 5px;
  image-rendering: pixelated;
  background: var(--orange);
  opacity: 0.5;
  flex-shrink: 0;
}

.rpanel__parcel-dot--done {
  background: #8a9a80;
  opacity: 0.5;
}

/* ── News (item 5: line-height 1.8) ───────────────────── */
.rpanel__news {
  line-height: 1.8;
  margin-bottom: 4px;
}

/* ── Whisper ───────────────────────────────────────────── */
.rpanel__whisper {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 400;
  color: var(--text-dim);
  opacity: 0.5;
  margin: 4px 0 0;
  letter-spacing: 0.3px;
}
</style>
