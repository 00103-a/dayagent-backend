import { ref } from 'vue'
import { fetchPlan } from '@/api/plan'
import { fetchWeather } from '@/api/weather'
import { fetchCourses } from '@/api/courses'
import { fetchNews } from '@/api/news'
import { getParcels } from '@/api/parcel'
import { useUserStore } from '@/stores/user'
import { weatherType, weatherShort as sharedWeatherShort, weatherTemp as sharedWeatherTemp } from '@/stores/weatherState'
import { deriveWeatherType, formatWeather } from '@/utils/weather'

function todayDayIndex() {
  const d = new Date().getDay()
  return d === 0 ? 7 : d
}

function todayDateStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/**
 * Parse today's courses into timeline rows.
 * Courses are already filtered by current week from the API (?week=current).
 */
function getTodayCourseRows(courses) {
  if (!courses?.length) return []
  const today = todayDayIndex()

  const todayCourses = courses.filter((c) => c.day === today)
  if (!todayCourses.length) return []

  const slotLabels = {
    '第一大节': '08:30', '第二大节': '10:25',
    '第三大节': '14:00', '第四大节': '15:35',
    '第五大节': '19:00',
  }

  return todayCourses
    .sort((a, b) => (a.time_slot || '').localeCompare(b.time_slot || ''))
    .map((c) => ({
      time: slotLabels[c.time_slot] || c.time_slot || '',
      name: c.name || '',
      teacher: c.teacher || '',
      location: c.location || '',
    }))
}

/**
 * Extract hero insight from plan text.
 * Looks for &ldquo;...&rdquo; marker (injected by Python planner).
 */
function extractHeroInsight(planText) {
  if (!planText) return ''
  // Look for &ldquo;...&rdquo; or "..." or ...
  const quoted = planText.match(/&ldquo;(.+?)&rdquo;/) || planText.match(/"(.+?)"/) || planText.match(/[\u201c](.+?)[\u201d]/)
  if (quoted) return quoted[1].trim()

  // Fallback: first meaningful line
  const lines = planText.split('\n').map((l) => l.trim()).filter(Boolean)
  for (const line of lines) {
    const clean = line.replace(/^[#*\s>><]+/, '').replace(/[#*`>><]+/g, '').trim()
    if (clean.length > 15 && clean.length < 50) return clean
  }
  return ''
}

/**
 * Split news text into individual line items.
 */
function parseNewsLines(text) {
  if (!text) return []
  return text
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l.startsWith('·'))
    .slice(0, 4)
}

/* ═══════════════════════════════════════════════════════════
   Date-aware cache helpers
   ═══════════════════════════════════════════════════════════ */

function cacheGet(key) {
  try {
    const raw = sessionStorage.getItem(key)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (parsed.date === todayDateStr()) return parsed.data
  } catch { /* ignore */ }
  sessionStorage.removeItem(key)
  return null
}

function cacheSet(key, data) {
  sessionStorage.setItem(key, JSON.stringify({ data, date: todayDateStr() }))
}

/* ═══════════════════════════════════════════════════════════
   Main composable
   ═══════════════════════════════════════════════════════════ */

export function useHomeData() {
  const userStore = useUserStore()

  /* ── Plan state ──────────────────────────────────────── */
  const planLoading = ref(false)
  const planError = ref('')
  const planData = ref(null)
  const heroInsight = ref('')
  const focusItems = ref([])
  const deepInsight = ref('')

  /* ── Weather ────────────────────────────────────────── */
  const weatherLoading = ref(false)
  const weatherShort = ref('')
  const weatherTemp = ref(null)

  /* ── Courses ────────────────────────────────────────── */
  const coursesLoading = ref(false)
  const todayCourseRows = ref([])
  const hasCourses = ref(false)

  /* ── News ───────────────────────────────────────────── */
  const newsLoading = ref(false)
  const newsLines = ref([])

  /* ── Parcels ────────────────────────────────────────── */
  const parcelsLoading = ref(false)
  const parcelItems = ref([])

  /* ── Location ───────────────────────────────────────── */
  const location = ref('南昌')

  /* ═══════════════════════════════════════════════════════
     Plan loading
     ═══════════════════════════════════════════════════════ */

  function applyPlanData() {
    if (!planData.value) return

    // 1. Use structured priorities from API (now populated by Python!)
    if (planData.value.priorities?.length) {
      focusItems.value = planData.value.priorities
    }

    // 2. Use structured warnings from API
    if (planData.value.warnings?.length) {
      deepInsight.value = planData.value.warnings.join('；')
    }

    // 3. Extract hero insight from plan text
    const hero = extractHeroInsight(planData.value.plan || '')
    if (hero) heroInsight.value = hero

    // 4. Extract parcels from plan response
    if (planData.value.parcels?.length) {
      parcelItems.value = planData.value.parcels.map((p) => ({
        trackingNo: p.tracking_no,
        carrier: p.carrier,
        remark: p.remark,
        status: p.state || p.latest_context || '',
        isDelivered: p.is_delivered,
      }))
    }
  }

  async function loadPlan(forceRefresh = false) {
    planLoading.value = true
    planError.value = ''
    try {
      const cacheKey = `plan_${userStore.userId}`
      let data = null

      if (!forceRefresh) {
        data = cacheGet(cacheKey)
      }

      if (!data) {
        data = await fetchPlan(userStore.userId, location.value, forceRefresh)
        cacheSet(cacheKey, data)
      }

      planData.value = data
      applyPlanData()
    } catch (e) {
      planError.value = e.message || '获取规划失败'
    } finally {
      planLoading.value = false
    }
  }

  /* ═══════════════════════════════════════════════════════
     Weather — cached for the day, refresh only on explicit action
     ═══════════════════════════════════════════════════════ */
  async function loadWeather(forceRefresh = false) {
    const cacheKey = `weather_${userStore.userId}`
    if (!forceRefresh) {
      const cached = cacheGet(cacheKey)
      if (cached) {
        weatherShort.value = cached.text
        weatherTemp.value = cached.temp
        sharedWeatherShort.value = cached.text
        sharedWeatherTemp.value = cached.temp
        weatherType.value = cached.weatherType || deriveWeatherType(cached.text || '')
        return
      }
    }
    weatherLoading.value = true
    try {
      const data = await fetchWeather({ location: location.value })
      const fmt = formatWeather(data.weather || '')
      weatherShort.value = fmt.text
      weatherTemp.value = fmt.temp
      sharedWeatherShort.value = fmt.text
      sharedWeatherTemp.value = fmt.temp
      const wt = deriveWeatherType(
        data.condition_text || fmt.text || ''
      )
      weatherType.value = wt
      cacheSet(cacheKey, { text: fmt.text, temp: fmt.temp, weatherType: wt })
    } catch {
      // degrade silently
    } finally {
      weatherLoading.value = false
    }
  }

  /* ═══════════════════════════════════════════════════════
     Courses — filter by current teaching week
     ═══════════════════════════════════════════════════════ */
  async function loadCourses() {
    coursesLoading.value = true
    try {
      // Call with ?week=current to only get courses active this week
      const data = await fetchCourses('current')
      const rows = getTodayCourseRows(data.courses || [])
      todayCourseRows.value = rows
      hasCourses.value = (data.courses || []).length > 0
    } catch {
      // degrade silently
    } finally {
      coursesLoading.value = false
    }
  }

  /* ═══════════════════════════════════════════════════════
     News — cached for the day, refresh only on explicit action
     ═══════════════════════════════════════════════════════ */
  async function loadNews(forceRefresh = false) {
    const cacheKey = `news_${userStore.userId}`
    if (!forceRefresh) {
      const cached = cacheGet(cacheKey)
      if (cached) {
        newsLines.value = cached
        return
      }
    }
    newsLoading.value = true
    try {
      const data = await fetchNews()
      const lines = parseNewsLines(data.news_text || '')
      newsLines.value = lines
      cacheSet(cacheKey, lines)
    } catch {
      // degrade silently
    } finally {
      newsLoading.value = false
    }
  }

  /* ═══════════════════════════════════════════════════════
     Parcels — cached for the day, refresh only on explicit action
     ═══════════════════════════════════════════════════════ */
  async function loadParcels(forceRefresh = false) {
    const cacheKey = `parcels_${userStore.userId}`
    if (!forceRefresh) {
      const cached = cacheGet(cacheKey)
      if (cached) {
        if (!parcelItems.value.length) {
          parcelItems.value = cached
        }
        return
      }
    }
    parcelsLoading.value = true
    try {
      const data = await getParcels()
      if (data?.length && !parcelItems.value.length) {
        parcelItems.value = data
      }
      cacheSet(cacheKey, data || [])
    } catch {
      // degrade
    } finally {
      parcelsLoading.value = false
    }
  }

  /* ═══════════════════════════════════════════════════════
     Load all
     ═══════════════════════════════════════════════════════ */
  async function loadAll(forceRefresh = false) {
    await Promise.allSettled([
      loadPlan(forceRefresh),
      loadWeather(forceRefresh),
      loadCourses(),
      loadNews(forceRefresh),
      loadParcels(forceRefresh),
    ])
  }

  return {
    planLoading, planError, planData,
    heroInsight, focusItems, deepInsight,
    weatherLoading, weatherShort, weatherTemp,
    coursesLoading, todayCourseRows, hasCourses,
    newsLoading, newsLines,
    parcelsLoading, parcelItems,
    location,
    loadAll,
  }
}
