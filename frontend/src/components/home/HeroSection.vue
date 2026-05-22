<script setup>
defineProps({
  insight: { type: String, default: '' },
  weatherText: { type: String, default: '' },
  weatherTemp: { type: Number, default: null },
  loading: { type: Boolean, default: false },
})
</script>

<template>
  <section class="hero" :class="{ 'hero--loading': loading }">
    <!-- AI Insight — large serif -->
    <h1 class="hero__title">
      <span v-if="insight">{{ insight }}</span>
      <span v-else class="hero__title--dim">早安，准备好开始新的一天。</span>
    </h1>

    <!-- Weather meta line -->
    <div v-if="weatherText" class="hero__meta">
      <span class="hero__weather">{{ weatherText }}</span>
      <template v-if="weatherTemp !== null">
        <span class="hero__dot">·</span>
        <span class="hero__temp">{{ weatherTemp }}&deg;C</span>
      </template>
    </div>
  </section>
</template>

<style scoped>
.hero {
  position: relative;
  padding: 8px 0 44px;
  transition: opacity var(--duration-normal) var(--ease-out);
}

.hero--loading {
  opacity: 0.4;
}

/* ── Title ─────────────────────────────────────────────── */
.hero__title {
  font-family: var(--font-body);
  font-size: clamp(26px, 2.4vw, 34px);
  font-weight: 400;
  image-rendering: pixelated;
  line-height: 1.35;
  color: var(--text);
  letter-spacing: 0;
  max-width: 68ch;
}

.hero__title--dim {
  color: var(--text-dim);
}

/* ── Meta ───────────────────────────────────────────────── */
.hero__meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 20px;
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 400;
  color: var(--text-dim);
  letter-spacing: 0.2px;
}

.hero__dot {
  color: var(--text-dim);
}

.hero__temp {
  color: var(--text-secondary);
  font-weight: 400;
}
</style>
