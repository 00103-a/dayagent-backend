import { ref } from 'vue'
import { submitSummary, getSummaries, updateSummary, deleteSummary } from '@/api/summary'
import { useUserStore } from '@/stores/user'

export function useSummary() {
  const summaries = ref([])
  const loading = ref(false)
  const error = ref(null)
  const submitting = ref(false)

  async function load() {
    const user = useUserStore()
    loading.value = true
    error.value = null
    try {
      summaries.value = await getSummaries(user.userId)
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function add(data) {
    const user = useUserStore()
    submitting.value = true
    try {
      const content = typeof data === 'string' ? data : data.content
      const moodScore = typeof data === 'object' ? data.moodScore : undefined
      await submitSummary(user.userId, content, moodScore)
      await load()
    } catch (e) {
      error.value = e.message
    } finally {
      submitting.value = false
    }
  }

  async function update(id, content, moodScore) {
    try {
      await updateSummary(id, content, moodScore)
      await load()
    } catch (e) {
      error.value = e.message
    }
  }

  async function remove(id) {
    try {
      await deleteSummary(id)
      await load()
    } catch (e) {
      error.value = e.message
    }
  }

  return { summaries, loading, error, submitting, load, add, update, remove }
}
