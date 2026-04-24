import { ref, watch } from 'vue'

export interface NotificationSettings {
  desktop: boolean
  sound: boolean
  events: {
    process_started: boolean
    process_exited: boolean
    user_input_required: boolean
    subagent_completed: boolean
  }
}

const STORAGE_KEY = 'claude-monitor-notifications'

const defaults: NotificationSettings = {
  desktop: true,
  sound: true,
  events: {
    process_started: true,
    process_exited: true,
    user_input_required: true,
    subagent_completed: true,
  },
}

function loadSettings(): NotificationSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      return { ...defaults, ...JSON.parse(raw), events: { ...defaults.events, ...(JSON.parse(raw).events || {}) } }
    }
  } catch { /* ignore */ }
  return { ...defaults, events: { ...defaults.events } }
}

const settings = ref<NotificationSettings>(loadSettings())
const permission = ref<NotificationPermission>(
  'Notification' in window ? Notification.permission : 'denied'
)

watch(settings, (s) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(s))
}, { deep: true })

export function useNotifications() {
  function updateSettings(patch: Partial<NotificationSettings>) {
    if (patch.events) {
      settings.value.events = { ...settings.value.events, ...patch.events }
    }
    const { events: _e, ...rest } = patch
    settings.value = { ...settings.value, ...rest }
  }

  async function requestPermission() {
    if (!('Notification' in window)) return
    const result = await Notification.requestPermission()
    permission.value = result
  }

  function isEventEnabled(type: string): boolean {
    const key = type as keyof NotificationSettings['events']
    return settings.value.events[key] !== false
  }

  return {
    settings,
    permission,
    updateSettings,
    requestPermission,
    isEventEnabled,
  }
}
