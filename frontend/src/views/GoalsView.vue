<script setup>
import { onMounted } from 'vue'
import { useGoals } from '@/composables/useGoals'
import { useKeepAliveEnter } from '@/composables/useKeepAliveEnter'
import SkeletonCard from '@/components/shared/SkeletonCard.vue'
import ErrorBlock from '@/components/shared/ErrorBlock.vue'
import EmptyState from '@/components/shared/EmptyState.vue'
import GoalForm from '@/components/goals/GoalForm.vue'
import GoalList from '@/components/goals/GoalList.vue'

const { goals, loading, error, submitting, load, add, toggleDone, remove, update } = useGoals()
const { animateEnter } = useKeepAliveEnter()

onMounted(() => { load() })

function handleAdd({ type, content, startDate, endDate }) {
  add(type, content, startDate, endDate)
}
</script>

<template>
  <div class="page">
    <!-- Header -->
    <header class="page__header">
      <h1 class="page__title">目标</h1>
      <p class="page__sub">设定方向，保持专注。</p>
    </header>

    <!-- New goal -->
    <section :class="animateEnter ? 'page__section anim-enter anim-enter--1' : 'page__section'">
      <h2 class="section__label">新目标</h2>
      <GoalForm :submitting="submitting" @submit="handleAdd" />
    </section>

    <!-- Error -->
    <ErrorBlock v-if="error" :message="error" can-retry @retry="load()" />

    <!-- Skeleton → content crossfade -->
    <Transition name="skel" mode="out-in">
      <SkeletonCard v-if="loading" key="skel" :lines="5" />

      <div v-else key="content">
        <!-- Active goals -->
        <section v-if="goals.filter(g => g.status === 'active').length" :class="animateEnter ? 'page__section anim-enter anim-enter--2' : 'page__section'">
          <h2 class="section__label">进行中</h2>
          <GoalList
            :items="goals.filter(g => g.status === 'active')"
            @toggle="(id, s) => toggleDone(id, s)"
            @delete="(id) => remove(id)"
            @update="(id, content, endDate) => update(id, content, endDate)"
          />
        </section>

        <!-- Completed goals -->
        <section v-if="goals.some(g => g.status === 'done')" :class="animateEnter ? 'page__section anim-enter anim-enter--3' : 'page__section'">
          <h2 class="section__label">已完成</h2>
          <GoalList
            :items="goals.filter(g => g.status === 'done')"
            @toggle="(id, s) => toggleDone(id, s)"
            @delete="(id) => remove(id)"
            @update="(id, content, endDate) => update(id, content, endDate)"
          />
        </section>

        <!-- Empty -->
        <EmptyState v-if="!goals.length && !error" text="还没有目标，设定一个方向吧" />
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
