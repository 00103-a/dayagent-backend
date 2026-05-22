import { ref, onActivated } from 'vue'

/**
 * Controls entrance animation playback across keep-alive reactivations.
 * - First mount (onMounted): animation plays (animateEnter = true by default)
 * - Keep-alive reactivation (onActivated): animation skipped (animateEnter = false)
 *
 * Usage:
 *   const { animateEnter } = useKeepAliveEnter()
 *   // In template: <div :class="{ 'anim-enter': animateEnter, 'anim-enter--1': animateEnter }">
 */
export function useKeepAliveEnter() {
  const animateEnter = ref(true)
  let activatedCount = 0

  onActivated(() => {
    activatedCount++
    if (activatedCount > 1) {
      animateEnter.value = false
    }
  })

  return { animateEnter }
}
