<script setup>
defineProps({
  courseRows: { type: Array, default: () => [] },
  hasCourses: { type: Boolean, default: false },
  coursesLoading: { type: Boolean, default: false },
  weatherText: { type: String, default: '' },
  weatherTemp: { type: Number, default: null },
  weatherLoading: { type: Boolean, default: false },
  parcelItems: { type: Array, default: () => [] },
  parcelsLoading: { type: Boolean, default: false },
  newsLines: { type: Array, default: () => [] },
  newsLoading: { type: Boolean, default: false },
  location: { type: String, default: '' },
})
</script>

<template>
  <section class="info">
    <!-- ── Course card ──────────────────────────────── -->
    <div class="info__card">
      <div class="info__card-header">
        <svg class="info__card-icon" width="14" height="14" viewBox="0 0 14 14" fill="none">
          <rect x="1.5" y="2.5" width="11" height="9" rx="1.5" stroke="currentColor" stroke-width="1.1"/>
          <path d="M4.5 1.5v2M9.5 1.5v2M1.5 6h11" stroke="currentColor" stroke-width="1.1" stroke-linecap="round"/>
        </svg>
        <span class="info__card-label">今日课程</span>
      </div>
      <div class="info__card-body">
        <template v-if="coursesLoading">
          <p class="info__card-empty">加载中…</p>
        </template>
        <template v-else-if="courseRows.length">
          <div v-for="(c, i) in courseRows" :key="i" class="course-row">
            <span class="course-row__time">{{ c.slot }}</span>
            <span class="course-row__name">{{ c.name }}</span>
            <span v-if="c.location" class="course-row__loc">@{{ c.location }}</span>
          </div>
        </template>
        <p v-else class="info__card-empty">{{ hasCourses ? '今日无课' : '课表未导入' }}</p>
      </div>
    </div>

    <!-- ── Weather card ──────────────────────────────── -->
    <div class="info__card">
      <div class="info__card-header">
        <svg class="info__card-icon" width="14" height="14" viewBox="0 0 14 14" fill="none">
          <circle cx="7" cy="7" r="2.5" stroke="currentColor" stroke-width="1.1"/>
          <g stroke="currentColor" stroke-width="1.1" stroke-linecap="round">
            <path d="M7 1v1.5M7 11.5V13M1 7h1.5M11.5 7H13M2.76 2.76l1.06 1.06M10.18 10.18l1.06 1.06M2.76 11.24l1.06-1.06M10.18 3.82l1.06-1.06"/>
          </g>
        </svg>
        <span class="info__card-label">天气</span>
      </div>
      <div class="info__card-body">
        <p v-if="weatherLoading" class="info__card-empty">加载中…</p>
        <p v-else-if="weatherText" class="info__card-text">
          {{ location }} · {{ weatherText }}
          <template v-if="weatherTemp !== null">&nbsp;· {{ weatherTemp }}°C</template>
        </p>
        <p v-else class="info__card-empty">暂无天气数据</p>
      </div>
    </div>

    <!-- ── Parcel card ───────────────────────────────── -->
    <div class="info__card">
      <div class="info__card-header">
        <svg class="info__card-icon" width="14" height="14" viewBox="0 0 14 14" fill="none">
          <rect x="2" y="4" width="10" height="7.5" rx="1" stroke="currentColor" stroke-width="1.1"/>
          <path d="M5 4V2.5h4V4M2 7.5h10" stroke="currentColor" stroke-width="1.1"/>
        </svg>
        <span class="info__card-label">快递</span>
      </div>
      <div class="info__card-body">
        <template v-if="parcelsLoading">
          <p class="info__card-empty">加载中…</p>
        </template>
        <template v-else-if="parcelItems.length">
          <p v-for="(p, i) in parcelItems.slice(0, 2)" :key="i" class="info__card-text">
            {{ p.remark || p.trackingNo }} · {{ p.status || '运输中' }}
          </p>
        </template>
        <p v-else class="info__card-empty">暂无快递</p>
      </div>
    </div>

    <!-- ── News card ─────────────────────────────────── -->
    <div class="info__card">
      <div class="info__card-header">
        <svg class="info__card-icon" width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M2 4.5h6M2 7h8M2 9.5h5M10 3v8a1 1 0 0 0 2 0V4.2a.7.7 0 0 0-.7-.7H10Z" stroke="currentColor" stroke-width="1.1" stroke-linecap="round"/>
        </svg>
        <span class="info__card-label">新闻摘要</span>
      </div>
      <div class="info__card-body">
        <template v-if="newsLoading">
          <p class="info__card-empty">加载中…</p>
        </template>
        <template v-else-if="newsLines.length">
          <p v-for="(line, i) in newsLines" :key="i" class="info__card-text news-line">
            {{ line }}
          </p>
        </template>
        <p v-else class="info__card-empty">暂无新闻</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 20px;
}

.info__card {
  background: var(--card);
  border: 1px solid var(--border-subtle);
  image-rendering: pixelated;
  padding: 18px 20px;
  transition: border-color var(--duration-normal) var(--ease-out),
              transform var(--duration-normal) var(--ease-out),
              box-shadow var(--duration-normal) var(--ease-out);
  cursor: default;
  min-height: 0;
}

.info__card:hover {
  border-color: var(--card-border);
  transform: translateY(-2px);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
}

.info__card-header {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 10px;
}

.info__card-icon {
  color: var(--text-dim);
  flex-shrink: 0;
}

.info__card-label {
  font-family: var(--font-display);
  font-size: 9px;
  color: var(--orange);
  letter-spacing: 1px;
  image-rendering: pixelated;
}

.info__card-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info__card-text {
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: 400;
  color: var(--text);
  line-height: 1.55;
}

.info__card-empty {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 400;
  color: var(--text-dim);
  image-rendering: pixelated;
}

/* ── Course rows ────────────────────────────────────── */
.course-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-family: var(--font-body);
  font-size: 13px;
  line-height: 1.5;
}

.course-row__time {
  font-weight: 400;
  color: var(--orange);
  min-width: 32px;
  flex-shrink: 0;
  font-size: 12px;
}

.course-row__name {
  font-weight: 400;
  color: var(--text);
}

.course-row__loc {
  font-weight: 400;
  color: var(--text-dim);
  font-size: 12px;
  margin-left: auto;
}

/* ── News lines ─────────────────────────────────────── */
.news-line {
  /* Each line is one news item */
}
</style>
