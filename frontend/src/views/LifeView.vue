<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useKeepAliveEnter } from '@/composables/useKeepAliveEnter'
import { fetchCourses, importCourses, clearCourses } from '@/api/courses'
import { fetchChaoxingTasks } from '@/api/chaoxing'
import { useParcels } from '@/composables/useParcels'
import SkeletonCard from '@/components/shared/SkeletonCard.vue'
import ErrorBlock from '@/components/shared/ErrorBlock.vue'
import EmptyState from '@/components/shared/EmptyState.vue'
import ParcelForm from '@/components/parcel/ParcelForm.vue'
import ParcelList from '@/components/parcel/ParcelList.vue'

const userStore = useUserStore()
const { animateEnter } = useKeepAliveEnter()
const { parcels, loading: parcelsLoading, error: parcelsError, submitting, load: loadParcels, add, remove } = useParcels()

// ── Weekday labels ──
const WEEKDAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
const todayIndex = new Date().getDay() === 0 ? 7 : new Date().getDay()

// ── Courses ──
const coursesLoading = ref(false)
const coursesError = ref('')
const courseList = ref([])
const courseCount = ref(0)
const currentWeek = ref(null)
const importing = ref(false)
const importMsg = ref('')
const importOk = ref(false)
const clearing = ref(false)
const COURSES_KEY = `courses_${userStore.userId}`

// Group courses by day
const weekGrid = computed(() => {
  const grid = Array.from({ length: 7 }, () => [])
  for (const c of courseList.value) {
    const dayIdx = (c.day || 1) - 1 // 1=Mon → idx 0
    if (dayIdx >= 0 && dayIdx < 7) {
      grid[dayIdx].push(c)
    }
  }
  // Sort each day by time slot
  const slotOrder = { '第一大节': 0, '第二大节': 1, '第三大节': 2, '第四大节': 3, '第五大节': 4 }
  for (const day of grid) {
    day.sort((a, b) => (slotOrder[a.time_slot] ?? 99) - (slotOrder[b.time_slot] ?? 99))
  }
  return grid
})

const slotLabels = {
  '第一大节': '08:30', '第二大节': '10:25',
  '第三大节': '14:00', '第四大节': '15:35',
  '第五大节': '19:00',
}

// Format weeks string for display
function formatWeeks(weeks) {
  if (!weeks) return ''
  const rangeMatch = /^(\d+)-(\d+)$/.exec(weeks.trim())
  if (rangeMatch) return `${rangeMatch[1]}-${rangeMatch[2]}周`
  const parts = weeks.split(',').map(w => parseInt(w.trim(), 10)).filter(n => !isNaN(n))
  if (parts.length >= 2) {
    const allOdd = parts.every(n => n % 2 === 1)
    const allEven = parts.every(n => n % 2 === 0)
    if (allOdd) return '单周'
    if (allEven) return '双周'
  }
  return weeks
}

// Check if course is active in the current week
function _parseWeekNums(weeksStr) {
  const result = new Set()
  if (!weeksStr) return result
  const parts = weeksStr.split(/[,，]/)
  for (const part of parts) {
    const cleaned = part.trim()
    if (!cleaned) continue
    const rangeMatch = /^(\d+)-(\d+)$/.exec(cleaned)
    if (rangeMatch) {
      for (let i = parseInt(rangeMatch[1]); i <= parseInt(rangeMatch[2]); i++) result.add(i)
    } else {
      const num = parseInt(cleaned, 10)
      if (!isNaN(num)) result.add(num)
    }
  }
  return result
}

function isCourseActiveThisWeek(course) {
  if (!currentWeek.value || !course.weeks) return true
  const activeWeeks = _parseWeekNums(course.weeks)
  if (activeWeeks.size === 0) return true
  return activeWeeks.has(currentWeek.value)
}

async function loadCourses() {
  coursesLoading.value = true; coursesError.value = ''
  try {
    const data = await fetchCourses()
    courseList.value = data.courses || []
    courseCount.value = data.count || courseList.value.length
    currentWeek.value = data.current_week ?? null
    sessionStorage.setItem(COURSES_KEY, JSON.stringify({ courses: courseList.value, count: courseCount.value, currentWeek: currentWeek.value }))
  } catch (e) {
    coursesError.value = e.message
  } finally { coursesLoading.value = false }
}

async function doImportCourses() {
  importing.value = true; importMsg.value = ''; importOk.value = false
  try {
    const data = await importCourses()
    importMsg.value = data.message || `成功导入 ${data.count} 门课程`
    importOk.value = true
    await loadCourses()
  } catch (e) {
    importMsg.value = '导入失败：' + (e.response?.data?.detail || e.message)
    importOk.value = false
  } finally { importing.value = false }
}

async function doClearCourses() {
  clearing.value = true; coursesError.value = ''
  try {
    await clearCourses()
    courseList.value = []
    courseCount.value = 0
    sessionStorage.removeItem(COURSES_KEY)
  } catch (e) {
    coursesError.value = e.message
  } finally { clearing.value = false }
}

// ── Chaoxing ──
const chaoxingLoading = ref(false)
const chaoxingError = ref('')
const chaoxingText = ref('')
const CHAOXING_KEY = `chaoxing_${userStore.userId}`

async function refreshChaoxing() {
  chaoxingLoading.value = true; chaoxingError.value = ''
  try {
    const data = await fetchChaoxingTasks()
    chaoxingText.value = data.tasks_text
    sessionStorage.setItem(CHAOXING_KEY, chaoxingText.value)
  } catch (e) {
    chaoxingError.value = e.message
  } finally { chaoxingLoading.value = false }
}

// ── Parcel ──
const deletingId = ref(null)
function handleAdd({ trackingNo, carrier, remark }) { add(trackingNo, carrier, remark) }
async function handleDelete(id) { deletingId.value = id; await remove(id); deletingId.value = null }

// ── Init ──
onMounted(() => {
  const cachedCourses = sessionStorage.getItem(COURSES_KEY)
  if (cachedCourses) {
    try { const c = JSON.parse(cachedCourses); courseList.value = c.courses || []; courseCount.value = c.count || 0; currentWeek.value = c.currentWeek ?? null } catch {}
    loadCourses() // background refresh
  } else {
    loadCourses()
  }

  const cachedChaoxing = sessionStorage.getItem(CHAOXING_KEY)
  if (cachedChaoxing) chaoxingText.value = cachedChaoxing
  else refreshChaoxing()

  loadParcels()
})
</script>

<template>
  <div class="page">
    <!-- Header -->
    <header class="page__header">
      <h1 class="page__title">生活</h1>
      <p class="page__sub">课表、学习通、快递，生活一览。</p>
    </header>

    <!-- ═══════════ Weekly Course Timeline ═══════════ -->
    <section :class="animateEnter ? 'page__section anim-enter anim-enter--1' : 'page__section'">
      <div class="section__head">
        <h2 class="section__label">
          我的课表
          <span v-if="currentWeek" class="week-badge">第 {{ currentWeek }} 周</span>
        </h2>
        <div class="section__actions">
          <button class="act-btn" :disabled="importing" @click="doImportCourses">
            {{ importing ? '导入中…' : '导入课表' }}
          </button>
          <button v-if="courseCount" class="act-btn act-btn--ghost" :disabled="clearing" @click="doClearCourses">
            清空
          </button>
        </div>
      </div>

      <div v-if="importMsg" :class="['banner', importOk ? 'banner--ok' : 'banner--err']" style="margin-bottom:16px">
        {{ importMsg }}
      </div>

      <!-- Loading -->
      <SkeletonCard v-if="coursesLoading && !courseList.length" :lines="6" />

      <!-- Error -->
      <ErrorBlock v-else-if="coursesError && !courseList.length" :message="coursesError" can-retry @retry="loadCourses" />

      <!-- Week grid -->
      <div v-else-if="courseList.length" class="week">
        <div
          v-for="(dayCourses, di) in weekGrid"
          :key="di"
          class="week__day"
          :class="{ 'week__day--today': di + 1 === todayIndex }"
        >
          <!-- Day header -->
          <div class="week__day-head">
            <span class="week__day-name">{{ WEEKDAYS[di] }}</span>
            <span v-if="di + 1 === todayIndex" class="week__today-dot" />
          </div>

          <!-- Courses for this day -->
          <div v-if="dayCourses.length" class="week__courses">
            <div
              v-for="(c, ci) in dayCourses"
              :key="ci"
              class="week__course"
              :class="{ 'week__course--inactive': !isCourseActiveThisWeek(c) }"
            >
              <p class="week__course-time">{{ slotLabels[c.time_slot] || c.time_slot }}</p>
              <p class="week__course-name">{{ c.name }}</p>
              <p v-if="c.weeks" class="week__course-weeks">{{ formatWeeks(c.weeks) }}</p>
              <p v-if="c.location || c.teacher" class="week__course-sub">
                <template v-if="c.location">@{{ c.location }}</template>
                <template v-if="c.location && c.teacher"> · </template>
                <template v-if="c.teacher">{{ c.teacher }}</template>
              </p>
            </div>
          </div>
          <p v-else class="week__empty-day">—</p>
        </div>
      </div>

      <!-- Empty -->
      <EmptyState v-else-if="!coursesLoading" text="课表未导入，点击上方按钮从教务系统导入" />
    </section>

    <!-- ═══════════ Chaoxing ═══════════ -->
    <section :class="animateEnter ? 'page__section anim-enter anim-enter--2' : 'page__section'">
      <div class="section__head">
        <h2 class="section__label">学习通</h2>
        <button class="act-btn act-btn--ghost" :disabled="chaoxingLoading" @click="refreshChaoxing">刷新</button>
      </div>

      <SkeletonCard v-if="chaoxingLoading && !chaoxingText" :lines="3" />
      <ErrorBlock v-else-if="chaoxingError && !chaoxingText" :message="chaoxingError" can-retry @retry="refreshChaoxing" />
      <pre v-else-if="chaoxingText" class="mod-text">{{ chaoxingText }}</pre>
      <EmptyState v-else text="暂无学习通数据" />
    </section>

    <!-- ═══════════ Parcels ═══════════ -->
    <section :class="animateEnter ? 'page__section anim-enter anim-enter--3' : 'page__section'">
      <h2 class="section__label">快递</h2>
      <ParcelForm :submitting="submitting" @submit="handleAdd" />

      <ErrorBlock v-if="parcelsError" :message="parcelsError" can-retry @retry="loadParcels" style="margin-top:16px" />
      <SkeletonCard v-if="parcelsLoading" :lines="5" style="margin-top:16px" />

      <div v-if="!parcelsLoading && parcels.length" style="margin-top:8px">
        <ParcelList :items="parcels" :deleting-id="deletingId" @delete="handleDelete" />
      </div>
      <EmptyState v-if="!parcelsLoading && !parcels.length && !parcelsError" text="还没有快递，上方添加一个快递单号" />
    </section>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding-bottom: 48px;
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
  padding: 0 0 32px;
}

.section__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.section__label {
  font-family: var(--font-display);
  font-size: 10px;
  color: var(--orange);
  letter-spacing: 1px;
  image-rendering: pixelated;
  display: flex;
  align-items: center;
  gap: 10px;
}

.week-badge {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 500;
  color: var(--orange);
  background: var(--orange-soft);
  border: 1px solid rgba(224, 112, 48, 0.15);
  padding: 2px 10px;
  letter-spacing: 0;
}

.section__actions {
  display: flex;
  gap: 8px;
}

/* ── Action button ─────────────────────────────────────── */
.act-btn {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 400;
  color: var(--orange);
  background: transparent;
  border: 1px solid rgba(224, 112, 48, 0.18);
  padding: 5px 14px;
  image-rendering: pixelated;
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-out), border-color var(--duration-fast) var(--ease-out), color var(--duration-fast) var(--ease-out);
}
.act-btn:hover:not(:disabled) {
  background: rgba(224, 112, 48, 0.08);
  border-color: rgba(224, 112, 48, 0.3);
}
.act-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.act-btn--ghost {
  color: var(--text-dim);
  border-color: var(--border-subtle);
}
.act-btn--ghost:hover:not(:disabled) {
  color: var(--text);
  background: rgba(224, 112, 48, 0.04);
}

/* ═══════════ Week grid ═══════════ */
.week {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 1px;
  background: var(--border-subtle);
  border: 1px solid var(--border-subtle);
  overflow: hidden;
}

.week__day {
  background: var(--card);
  padding: 12px 10px 14px;
  min-height: 120px;
  transition: background var(--duration-fast) var(--ease-out);
}

.week__day--today {
  background: var(var(--card));
  box-shadow: inset 0 1px 0 rgba(224, 112, 48, 0.12);
}

.week__day-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.week__day-name {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 500;
  color: var(--text-dim);
}

.week__today-dot {
  width: 4px;
  height: 4px;
  image-rendering: pixelated;
  background: var(--orange);
}

.week__courses {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.week__course {
  min-width: 80px;
}

.week__course--inactive {
  opacity: 0.45;
}

.week__course-time {
  font-family: 'zpix', monospace;
  font-size: 11px;
  -webkit-font-smoothing: none;
  font-weight: 500;
  image-rendering: pixelated;
  color: var(--orange);
  opacity: 0.6;
  margin: 0 0 2px;
}

.week__course-name {
  font-family: 'zpix', monospace;
  font-size: 13px;
  -webkit-font-smoothing: none;
  font-weight: 500;
  color: var(--text);
  line-height: 1.35;
  margin: 0;
}

.week__course-weeks {
  font-family: 'zpix', monospace;
  font-size: 11px;
  -webkit-font-smoothing: none;
  font-weight: 400;
  color: var(--text-dim);
  margin: 2px 0 0;
  line-height: 1.3;
}

.week__course-sub {
  font-family: 'zpix', monospace;
  font-size: 11px;
  -webkit-font-smoothing: none;
  font-weight: 400;
  color: var(--text-dim);
  line-height: 1.35;
  margin: 1px 0 0;
}

.week__empty-day {
  font-family: var(--font-display);
  font-size: 14px;
  image-rendering: pixelated;
  color: var(--text-dim);
  opacity: 0.35;
  text-align: center;
  padding-top: 8px;
  margin: 0;
}

/* ── Mod text (chaoxing raw) ────────────────────────────── */
.mod-text {
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: 400;
  line-height: 1.7;
  color: var(--text);
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
}

</style>
