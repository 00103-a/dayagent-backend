<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  scores: {
    type: Array, // Array of { date: string, score: number | null } for last 7 days
    default: () => [],
  },
})

const CHART_W = 260
const CHART_H = 70
const PAD_L = 4
const PAD_R = 4
const PAD_T = 4
const PAD_B = 16

const weekdays = ['日', '一', '二', '三', '四', '五', '六']

const avg = computed(() => {
  const valid = props.scores.filter((s) => s && s.score != null)
  if (!valid.length) return null
  const sum = valid.reduce((a, b) => a + b.score, 0)
  return (sum / valid.length).toFixed(1)
})

const hasAnyData = computed(() => props.scores.some((s) => s && s.score != null))

const dayLabels = computed(() => {
  return props.scores.map((s) => {
    if (!s || !s.date) return ''
    try {
      const d = new Date(s.date)
      if (isNaN(d.getTime())) return s.date.slice(5)
      const m = d.getMonth() + 1
      const day = d.getDate()
      return `${m}/${day}`
    } catch {
      return ''
    }
  })
})

const todayIndex = computed(() => {
  if (!props.scores.length) return -1
  const today = new Date().toISOString().slice(0, 10)
  return props.scores.findIndex((s) => s && s.date === today)
})

const points = computed(() => {
  if (!props.scores.length) return []
  const n = props.scores.length
  const stepX = (CHART_W - PAD_L - PAD_R) / Math.max(n - 1, 1)
  const rangeY = CHART_H - PAD_T - PAD_B
  return props.scores.map((s, i) => {
    if (!s || s.score == null) return { x: PAD_L + i * stepX, y: null, score: null, date: s?.date }
    const y = PAD_T + rangeY - ((s.score - 1) / 4) * rangeY
    return { x: PAD_L + i * stepX, y: Math.round(y), score: s.score, date: s.date }
  })
})

const linePath = computed(() => {
  const valid = points.value.filter((p) => p.y != null)
  if (valid.length < 2) return ''
  return valid.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')
})

// Grid lines: 5 horizontal lines (1-5)
const gridLines = [1, 2, 3, 4, 5]

// Hover state
const hoveredIdx = ref(-1)
function onHover(idx) { hoveredIdx.value = idx }
function onLeave() { hoveredIdx.value = -1 }
</script>

<template>
  <div class="energy-card">
    <!-- Header -->
    <div class="energy-card__head">
      <span class="energy-card__title">精力趋势</span>
      <span v-if="avg" class="energy-card__avg">AVG {{ avg }}</span>
    </div>

    <!-- Empty state -->
    <div v-if="!hasAnyData" class="energy-card__empty">
      暂无精力记录，写日记后自动生成
    </div>

    <!-- Chart -->
    <div v-else class="energy-card__chart">
      <svg
        :viewBox="`0 0 ${CHART_W} ${CHART_H}`"
        width="100%"
        height="70"
        preserveAspectRatio="xMidYMid meet"
        style="display:block"
      >
        <!-- Grid lines -->
        <line
          v-for="gl in gridLines" :key="gl"
          :x1="PAD_L" :y1="PAD_T + ((gl - 1) / 4) * (CHART_H - PAD_T - PAD_B)"
          :x2="CHART_W - PAD_R" :y2="PAD_T + ((gl - 1) / 4) * (CHART_H - PAD_T - PAD_B)"
          stroke="rgba(224,112,48,0.08)"
          stroke-width="1"
          stroke-dasharray="2 2"
        />

        <!-- Polyline -->
        <path
          v-if="linePath"
          :d="linePath"
          fill="none"
          stroke="#e07030"
          stroke-width="1.5"
          stroke-linecap="square"
          stroke-linejoin="miter"
        />

        <!-- Data points -->
        <template v-for="(p, i) in points" :key="i">
          <!-- Filled rect for valid points -->
          <rect
            v-if="p.y != null"
            :x="p.x - (hoveredIdx === i ? 3 : 2)"
            :y="p.y - (hoveredIdx === i ? 3 : 2)"
            :width="hoveredIdx === i ? 6 : 4"
            :height="hoveredIdx === i ? 6 : 4"
            fill="#e07030"
            shape-rendering="crispEdges"
            style="cursor:pointer"
            @mouseenter="onHover(i)"
            @mouseleave="onLeave"
          />
          <!-- Empty rect for missing data -->
          <rect
            v-else
            :x="p.x - 2"
            :y="CHART_H / 2 - 2"
            :width="4"
            :height="4"
            fill="none"
            stroke="#6b5a48"
            stroke-width="1"
            shape-rendering="crispEdges"
          />
        </template>

        <!-- Hover tooltip -->
        <g v-if="hoveredIdx >= 0 && points[hoveredIdx]?.y != null">
          <rect
            :x="Math.min(Math.max(points[hoveredIdx].x - 18, 2), CHART_W - 40)"
            :y="Math.max(points[hoveredIdx].y - 22, 2)"
            width="36"
            height="16"
            fill="rgba(8,6,4,0.92)"
            stroke="rgba(224,112,48,0.3)"
            stroke-width="1"
            shape-rendering="crispEdges"
          />
          <text
            :x="Math.min(Math.max(points[hoveredIdx].x, 20), CHART_W - 22)"
            :y="Math.max(points[hoveredIdx].y - 10, 13)"
            text-anchor="middle"
            fill="#c8b89a"
            font-family="zpix, monospace"
            font-size="8"
          >
            {{ dayLabels[hoveredIdx] }} {{ points[hoveredIdx].score }}
          </text>
        </g>
      </svg>

      <!-- X-axis labels -->
      <div class="energy-card__x-labels">
        <span
          v-for="(label, i) in dayLabels"
          :key="i"
          class="energy-card__x-label"
          :class="{ 'energy-card__x-label--today': i === todayIndex }"
        >{{ label }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.energy-card {
  background: rgba(14, 9, 5, 0.72);
  border: 1px solid rgba(224, 112, 48, 0.13);
  padding: 16px;
  position: relative;
}

/* Top highlight line */
.energy-card::after {
  content: '';
  position: absolute;
  top: 0;
  left: 15%;
  right: 15%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(224, 112, 48, 0.3), transparent);
  pointer-events: none;
}

.energy-card__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.energy-card__title {
  font-family: 'Press Start 2P', 'zpix', monospace;
  font-size: 8px;
  color: #e07030;
  letter-spacing: 0.5px;
  image-rendering: pixelated;
  -webkit-font-smoothing: none;
}

.energy-card__avg {
  font-family: 'zpix', monospace;
  font-size: 11px;
  color: #c8b89a;
  -webkit-font-smoothing: none;
}

.energy-card__chart {
  width: 100%;
}

.energy-card__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 70px;
  font-family: 'zpix', monospace;
  font-size: 11px;
  color: var(--text-dim);
  -webkit-font-smoothing: none;
}

.energy-card__x-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 2px;
  padding: 0 4px;
}

.energy-card__x-label {
  font-family: 'zpix', monospace;
  font-size: 10px;
  color: #6b5a48;
  -webkit-font-smoothing: none;
  text-align: center;
  min-width: 28px;
}

.energy-card__x-label--today {
  color: #e07030;
}
</style>
