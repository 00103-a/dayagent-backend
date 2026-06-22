<script setup>
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useHomeData } from '@/composables/useHomeData'
import { useKeepAliveEnter } from '@/composables/useKeepAliveEnter'
import HeroSection from '@/components/home/HeroSection.vue'
import FocusList from '@/components/home/FocusList.vue'
import CourseTimeline from '@/components/home/CourseTimeline.vue'
import HomeRightPanel from '@/components/home/HomeRightPanel.vue'
import HomeSkeleton from '@/components/home/HomeSkeleton.vue'
import ChatInline from '@/components/home/ChatInline.vue'

const userStore = useUserStore()
const {
  planLoading, planError, planData,
  heroInsight, focusItems, deepInsight,
  weatherLoading, weatherShort, weatherTemp,
  coursesLoading, todayCourseRows, hasCourses,
  newsLoading, newsLines,
  parcelsLoading, parcelItems,
  location,
  loadAll,
} = useHomeData()

const { animateEnter } = useKeepAliveEnter()

onMounted(() => {
  loadAll(false)
})
</script>

<template>
  <div class="home-layout">

    <!-- ═══════════ Main content column ═══════════ -->
    <div class="home-main">

      <!-- Skeleton → content crossfade -->
      <Transition name="skel" mode="out-in">
        <HomeSkeleton v-if="planLoading && !planData" key="skeleton" />

        <div v-else key="content">
          <!-- Error -->
          <div v-if="planError && !planData" class="home__error">
            <p class="home__error-msg">{{ planError }}</p>
            <button class="home__error-btn" @click="loadAll(true)">重试</button>
          </div>

          <!-- Content -->
          <template v-else>
            <div :class="animateEnter ? 'anim-enter anim-enter--1' : ''">
              <HeroSection
                :insight="heroInsight"
                :weather-text="weatherShort"
                :weather-temp="weatherTemp"
                :loading="planLoading"
              />
            </div>

            <div :class="animateEnter ? 'anim-enter anim-enter--2' : ''">
              <FocusList
                :items="focusItems"
                :loading="planLoading"
              />
            </div>

            <div :class="animateEnter ? 'anim-enter anim-enter--3' : ''">
              <CourseTimeline
                :course-rows="todayCourseRows"
                :has-courses="hasCourses"
                :loading="coursesLoading"
              />
            </div>

            <div :class="animateEnter ? 'anim-enter anim-enter--4' : ''">
              <ChatInline
                :plan="planData"
                :focus-items="focusItems"
              />
            </div>

            <div v-if="deepInsight" :class="animateEnter ? 'anim-enter anim-enter--4' : ''">
              <div class="deep-whisper">
                <p class="deep-whisper__text">{{ deepInsight }}</p>
              </div>
            </div>

            <!-- Refresh -->
            <div class="home__refresh">
              <button
                class="home__refresh-btn"
                :class="{ 'home__refresh-btn--spin': planLoading || weatherLoading || coursesLoading || newsLoading || parcelsLoading }"
                @click="loadAll(true)"
                title="刷新全部数据"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M1.5 7A5.5 5.5 0 0 1 12.18 4.5M12.5 7A5.5 5.5 0 0 1 1.82 9.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                  <path d="M12.18 4.5H9.5M1.82 9.5H4.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
              </button>
            </div>
          </template>
        </div>
      </Transition>

    </div>

    <!-- ═══════════ Right panel ═══════════ -->
    <aside class="home-right">
      <HomeRightPanel
        :weather-text="weatherShort"
        :weather-temp="weatherTemp"
        :weather-loading="weatherLoading"
        :parcel-items="parcelItems"
        :parcels-loading="parcelsLoading"
        :news-lines="newsLines"
        :news-loading="newsLoading"
        :location="location"
      />
    </aside>

  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════
   Layout: main content + right panel (responsive)
   ═══════════════════════════════════════════════════════════ */
.home-layout {
  display: grid;
  grid-template-columns: minmax(460px, 1fr) minmax(260px, 340px);
  gap: clamp(32px, 4vw, 56px);
}

.home-main {
  min-width: 0;
  position: relative;
  background: linear-gradient(90deg, rgba(8,6,4,0.75) 0%, rgba(8,6,4,0.45) 80%, transparent 100%);
  border-radius: 0 4px 4px 0;
}

.home-right {
  min-width: 0;
  padding-top: 4px;
}

/* ═══════════════════════════════════════════════════════════
   Error state
   ═══════════════════════════════════════════════════════════ */
.home__error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 100px 20px;
  text-align: center;
}

.home__error-msg {
  font-size: var(--text-base);
  color: var(--text-dim);
  font-weight: 400;
  line-height: 1.7;
  max-width: 380px;
  margin: 0;
}

.home__error-btn {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 400;
  color: var(--orange);
  background: transparent;
  border: 1px solid rgba(224, 112, 48, 0.2);
  padding: 8px 24px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-out), border-color var(--duration-fast) var(--ease-out);
}
.home__error-btn:hover {
  background: rgba(224, 112, 48, 0.08);
  border-color: rgba(224, 112, 48, 0.35);
}

/* ═══════════════════════════════════════════════════════════
   Deep insight whisper
   ═══════════════════════════════════════════════════════════ */
.deep-whisper {
  padding: 20px 0;
  border-top: 1px solid var(--border-subtle);
  margin-bottom: 8px;
}

.deep-whisper__text {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 400;
  font-style: italic;
  color: var(--text-dim);
  line-height: 1.6;
  margin: 0;
}

/* ═══════════════════════════════════════════════════════════
   Refresh
   ═══════════════════════════════════════════════════════════ */
.home__refresh {
  display: flex;
  justify-content: center;
  padding: 12px 0 8px;
}

.home__refresh-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--border-subtle);
  border-radius: 50%;
  background: transparent;
  color: var(--text-dim);
  cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-out), background var(--duration-fast) var(--ease-out), color var(--duration-fast) var(--ease-out);
}
.home__refresh-btn:hover {
  border-color: rgba(224, 112, 48, 0.25);
  color: var(--text);
  background: rgba(224, 112, 48, 0.04);
}
.home__refresh-btn--spin svg {
  animation: spin 1.2s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>

