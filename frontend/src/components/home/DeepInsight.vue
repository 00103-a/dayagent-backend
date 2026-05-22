<script setup>
defineProps({
  insight: { type: String, default: '' },
  loading: { type: Boolean, default: false },
})
</script>

<template>
  <section v-if="insight" class="deep" :class="{ 'deep--loading': loading }">
    <div class="deep__inner">
      <div class="deep__icon">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="6.5" stroke="currentColor" stroke-width="1.1"/>
          <path d="M8 5v3.5M8 11.5v.01" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
      </div>
      <div class="deep__content">
        <p class="deep__label">深度建议</p>
        <p class="deep__text">{{ insight }}</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.deep {
  margin-top: 20px;
}

.deep--loading {
  opacity: 0.4;
}

.deep__inner {
  display: flex;
  gap: 14px;
  padding: 22px 24px;
  background: var(--card);
  border: 1px solid var(--card-border);
  image-rendering: pixelated;
  transition: border-color var(--duration-normal) var(--ease-out),
              box-shadow var(--duration-normal) var(--ease-out);
}

.deep__inner:hover {
  border-color: rgba(224, 112, 48, 0.22);
  box-shadow: 0 0 30px rgba(224, 112, 48, 0.04);
}

.deep__icon {
  color: var(--orange);
  opacity: 0.6;
  flex-shrink: 0;
  margin-top: 1px;
}

.deep__content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.deep__label {
  font-family: var(--font-display);
  font-size: 9px;
  color: var(--orange);
  letter-spacing: 1px;
  image-rendering: pixelated;
}

.deep__text {
  font-family: var(--font-body);
  font-size: var(--text-base);
  font-weight: 400;
  color: var(--text);
  line-height: 1.6;
}
</style>
