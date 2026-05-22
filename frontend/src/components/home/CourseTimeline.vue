<script setup>
defineProps({
  courseRows: { type: Array, default: () => [] },
  hasCourses: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
})
</script>

<template>
  <section class="timeline" :class="{ 'timeline--loading': loading }">
    <h2 class="timeline__label">今日时间流</h2>

    <!-- Loading -->
    <div v-if="loading" class="timeline__empty">
      加载中&hellip;
    </div>

    <!-- Courses -->
    <div v-else-if="courseRows.length" class="timeline__list">
      <div
        v-for="(c, i) in courseRows"
        :key="i"
        class="timeline__item"
        :style="{ animationDelay: `${i * 0.06}s` }"
      >
        <!-- Time -->
        <div class="timeline__time">
          <span class="timeline__time-text">{{ c.time }}</span>
          <div class="timeline__line" />
        </div>

        <!-- Content -->
        <div class="timeline__card">
          <p class="timeline__name">{{ c.name }}</p>
          <p v-if="c.location || c.teacher" class="timeline__sub">
            <template v-if="c.location">@{{ c.location }}</template>
            <template v-if="c.location && c.teacher"> · </template>
            <template v-if="c.teacher">{{ c.teacher }}</template>
          </p>
        </div>
      </div>
    </div>

    <!-- Empty -->
    <p v-else class="timeline__empty">
      {{ hasCourses ? '今日无课，自由安排时间。' : '课表未导入，去 Settings 导入。' }}
    </p>
  </section>
</template>

<style scoped>
.timeline {
  padding: 0 0 28px;
}

.timeline--loading {
  opacity: 0.4;
}

.timeline__label {
  font-family: var(--font-display);
  font-size: 10px;
  color: var(--orange);
  letter-spacing: 1px;
  image-rendering: pixelated;
  margin-bottom: 16px;
}

.timeline__list {
  display: flex;
  flex-direction: column;
}

/* ── Each timeline row ─────────────────────────────────── */
.timeline__item {
  display: flex;
  gap: 16px;
  animation: fadeInUp 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
  min-height: 56px;
}

/* ── Time column ───────────────────────────────────────── */
.timeline__time {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 48px;
  flex-shrink: 0;
  padding-top: 2px;
}

.timeline__time-text {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 500;
  image-rendering: pixelated;
  color: var(--orange);
  opacity: 0.7;
  letter-spacing: -0.3px;
}

.timeline__line {
  width: 1px;
  flex: 1;
  background: linear-gradient(
    180deg,
    rgba(224, 112, 48, 0.25) 0%,
    rgba(224, 112, 48, 0.08) 50%,
    transparent 100%
  );
  margin-top: 8px;
  min-height: 24px;
}

.timeline__item:last-child .timeline__line {
  background: none;
}

/* ── Card ──────────────────────────────────────────────── */
.timeline__card {
  flex: 1;
  padding: 2px 0 20px;
}

.timeline__name {
  font-family: var(--font-body);
  font-size: var(--text-md);
  font-weight: 500;
  color: var(--text);
  line-height: 1.4;
  margin: 0;
}

.timeline__sub {
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 400;
  color: var(--text-dim);
  margin: 4px 0 0;
  line-height: 1.4;
}

/* ── Empty ─────────────────────────────────────────────── */
.timeline__empty {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 400;
  color: var(--text-dim);
  image-rendering: pixelated;
  padding: 4px 0;
  margin: 0;
}
</style>
