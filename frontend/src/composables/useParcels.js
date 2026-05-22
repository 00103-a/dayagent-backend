import { ref } from 'vue'
import { addParcel, getParcels, deleteParcel } from '@/api/parcel'

export function useParcels() {
  const parcels = ref([])
  const loading = ref(false)
  const error = ref(null)
  const submitting = ref(false)

  async function load() {
    loading.value = true
    error.value = null
    try {
      parcels.value = await getParcels()
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function add(trackingNo, carrier, remark) {
    submitting.value = true
    try {
      await addParcel(trackingNo, carrier, remark)
      await load()
    } catch (e) {
      error.value = e.message
    } finally {
      submitting.value = false
    }
  }

  async function remove(id) {
    submitting.value = true
    try {
      await deleteParcel(id)
      await load()
    } catch (e) {
      error.value = e.message
    } finally {
      submitting.value = false
    }
  }

  return { parcels, loading, error, submitting, load, add, remove }
}
