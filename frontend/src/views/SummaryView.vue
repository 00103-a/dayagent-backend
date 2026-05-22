<script setup>
import { onMounted } from 'vue'
import { useSummary } from '@/composables/useSummary'
import { useKeepAliveEnter } from '@/composables/useKeepAliveEnter'
import SkeletonCard from '@/components/shared/SkeletonCard.vue'
import ErrorBlock from '@/components/shared/ErrorBlock.vue'
import EmptyState from '@/components/shared/EmptyState.vue'
import SummaryForm from '@/components/summary/SummaryForm.vue'
import SummaryList from '@/components/summary/SummaryList.vue'

const { summaries, loading, error, submitting, load, add, update, remove } = useSummary()
const { animateEnter } = useKeepAliveEnter()

onMounted(() => { load() })
</script>

<template>
  <div class="page">
    <!-- Header -->
    <header class="page__header">
      <h1 class="page__title">日记</h1>
      <p class="page__sub">记录每一天，让时间看得见。</p>
    </header>

    <!-- Write -->
    <section :class="animateEnter ? 'page__section anim-enter anim-enter--1' : 'page__section'">
      <h2 class="section__label">写总结</h2>
      <SummaryForm :submitting="submitting" @submit="(data) => add(data)" />
    </section>

    <!-- Error -->
    <ErrorBlock v-if="error" :message="error" can-retry @retry="load()" />

    <!-- Skeleton → content crossfade -->
    <Transition name="skel" mode="out-in">
      <SkeletonCard v-if="loading" key="skel" :lines="4" />

      <div v-else key="content">
        <!-- History -->
        <section v-if="summaries.length" :class="animateEnter ? 'page__section anim-enter anim-enter--2' : 'page__section'">
          <h2 class="section__label">历史</h2>
          <SummaryList
            :items="summaries"
            @update="(id, content, moodScore) => update(id, content, moodScore)"
            @delete="(id) => remove(id)"
          />
        </section>

        <!-- Empty -->
        <EmptyState v-if="!summaries.length && !error" text="还没有写过总结，来记录今天吧" />
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding-bottom: 40px;
}

.page__header {
  padding: 0 0 32px;
}

.page__title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 500;
  image-rendering: pixelated;
  color: var(--text);
  letter-spacing: -1px;
  margin: 0 0 6px;
}

.page__sub {
  font-size: var(--text-sm);
  font-weight: 400;
  color: var(--text-dim);
  margin: 0;
}

.page__section {
  padding: 0 0 28px;
}

.section__label {
  font-family: var(--font-display);
  font-size: 10px;
  color: var(--orange);
  letter-spacing: 1px;
  image-rendering: pixelated;
  margin-bottom: 14px;
}

</style>
