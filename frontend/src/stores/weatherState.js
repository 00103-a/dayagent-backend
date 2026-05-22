/**
 * 全局天气状态 — 驱动 SceneBackground 场景切换
 * useHomeData 加载天气后写入，App.vue 读取后传给 SceneBackground
 */
import { ref } from 'vue'

export const weatherType = ref('sunny')
export const weatherShort = ref('')
export const weatherTemp = ref(null)
