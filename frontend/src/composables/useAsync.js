/**
 * 通用异步三态工具
 * 封装 loading / error / data 状态，视图层不再写 try/catch
 */
import { ref } from 'vue'

export function useAsync(asyncFn) {
  const data = ref(null)
  const error = ref(null)
  const loading = ref(false)

  async function execute(...args) {
    loading.value = true
    error.value = null
    try {
      data.value = await asyncFn(...args)
      return data.value
    } catch (e) {
      error.value = e.message || '未知错误'
      return null
    } finally {
      loading.value = false
    }
  }

  function reset() {
    data.value = null
    error.value = null
    loading.value = false
  }

  return { data, error, loading, execute, reset }
}
