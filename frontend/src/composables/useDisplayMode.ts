import { ref, watch } from 'vue'

export type DisplayMode = 'full' | 'mini'

const STORAGE_KEY = 'claude-monitor-display-mode'

const mode = ref<DisplayMode>(
  (localStorage.getItem(STORAGE_KEY) as DisplayMode) || 'full'
)

watch(mode, (m) => {
  localStorage.setItem(STORAGE_KEY, m)
})

export function useDisplayMode() {
  function toggle() {
    mode.value = mode.value === 'full' ? 'mini' : 'full'
  }

  function setMode(m: DisplayMode) {
    mode.value = m
  }

  return { mode, toggle, setMode }
}
