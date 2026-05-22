import { ref } from 'vue'
import { createGoal, getGoals, updateGoalStatus, updateGoal, deleteGoal } from '@/api/goal'
import { useUserStore } from '@/stores/user'

export function useGoals() {
  const goals = ref([])
  const loading = ref(false)
  const error = ref(null)
  const submitting = ref(false)

  async function load() {
    const user = useUserStore()
    loading.value = true
    error.value = null
    try {
      goals.value = await getGoals(user.userId)
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function add(type, content, startDate, endDate) {
    const user = useUserStore()
    submitting.value = true
    try {
      await createGoal(user.userId, type, content, startDate, endDate)
      await load()
    } catch (e) {
      error.value = e.message
    } finally {
      submitting.value = false
    }
  }

  async function toggleDone(id, currentStatus) {
    const newStatus = currentStatus === 'done' ? 'active' : 'done'
    try {
      await updateGoalStatus(id, newStatus)
      await load()
    } catch (e) {
      error.value = e.message
    }
  }

  async function remove(id) {
    try {
      await deleteGoal(id)
      await load()
    } catch (e) {
      error.value = e.message
    }
  }

  async function update(id, content, endDate) {
    try {
      const data = {}
      if (content !== undefined) data.content = content
      if (endDate !== undefined) data.endDate = endDate
      await updateGoal(id, data)
      await load()
    } catch (e) {
      error.value = e.message
    }
  }

  return { goals, loading, error, submitting, load, add, toggleDone, remove, update }
}
