<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { Notification } from '../composables/useWebSocket'
import type { NotificationSettings } from '../composables/useNotifications'

const props = defineProps<{
  notifications: Notification[]
  settings: NotificationSettings
  permission: NotificationPermission
}>()

const emit = defineEmits<{
  (e: 'updateSettings', patch: Partial<NotificationSettings>): void
  (e: 'requestPermission'): void
  (e: 'toggleEvent', key: string): void
}>()

const showPanel = ref(false)
const showSettings = ref(false)
const unread = ref(0)

// --- Web Audio API sound system ---
let audioCtx: AudioContext | null = null

function getAudioCtx(): AudioContext {
  if (!audioCtx) {
    audioCtx = new AudioContext()
  }
  return audioCtx
}

function playTone(frequency: number, duration: number, type: OscillatorType = 'square') {
  try {
    const ctx = getAudioCtx()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = type
    osc.frequency.setValueAtTime(frequency, ctx.currentTime)
    gain.gain.setValueAtTime(0.15, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration)
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start(ctx.currentTime)
    osc.stop(ctx.currentTime + duration)
  } catch { /* ignore audio errors */ }
}

function playSound(type: string) {
  if (!props.settings.sound) return
  if (!props.settings.events[type as keyof NotificationSettings['events']]) return

  switch (type) {
    case 'process_started':
      playTone(660, 0.1)
      setTimeout(() => playTone(880, 0.12), 100)
      break
    case 'process_exited':
      playTone(440, 0.12)
      setTimeout(() => playTone(330, 0.15), 120)
      break
    case 'user_input_required':
      playTone(880, 0.1)
      setTimeout(() => playTone(1100, 0.15), 120)
      setTimeout(() => playTone(880, 0.1), 280)
      break
    case 'subagent_completed':
      playTone(523, 0.08)
      setTimeout(() => playTone(659, 0.08), 80)
      setTimeout(() => playTone(784, 0.12), 160)
      break
  }
}

// --- Desktop notification ---
function sendDesktopNotification(notif: Notification) {
  if (!props.settings.desktop) return
  if (!props.settings.events[notif.type as keyof NotificationSettings['events']]) return
  if (!('Notification' in window) || Notification.permission !== 'granted') return

  const bodyText = getNotifBody(notif)
  new Notification('Claude Monitor', { body: bodyText })
}

// --- Watch for new notifications ---
watch(() => props.notifications.length, (newLen, oldLen) => {
  if (newLen > (oldLen ?? 0)) {
    unread.value += newLen - (oldLen ?? 0)
    const latest = props.notifications[props.notifications.length - 1]
    if (latest) {
      playSound(latest.type)
      sendDesktopNotification(latest)
    }
  }
})

// --- Helpers ---
function togglePanel() {
  showPanel.value = !showPanel.value
  if (showPanel.value) {
    unread.value = 0
    showSettings.value = false
  }
}

function toggleSettings() {
  showSettings.value = !showSettings.value
}

function toggleEvent(key: string) {
  emit('toggleEvent', key)
}

function formatTime(isoStr: string | undefined) {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function getNotifIcon(type: string): string {
  switch (type) {
    case 'process_started': return '+'
    case 'process_exited': return 'x'
    case 'user_input_required': return '?'
    case 'subagent_completed': return 'V'
    default: return '!'
  }
}

function getNotifTitle(type: string): string {
  switch (type) {
    case 'process_started': return 'PROCESS START'
    case 'process_exited': return 'PROCESS EXIT'
    case 'user_input_required': return 'INPUT NEEDED'
    case 'subagent_completed': return 'AGENT DONE'
    default: return 'ALERT'
  }
}

function getNotifBody(notif: Notification): string {
  switch (notif.type) {
    case 'process_started':
      return `New process: ${notif.project || notif.pid}`
    case 'process_exited':
      return `Process exited: PID ${notif.pid}`
    case 'user_input_required':
      return `${notif.project || 'PID ' + notif.pid} needs input`
    case 'subagent_completed':
      return `${notif.description || notif.agent_id}`
    default:
      return ''
  }
}

type EventKey = keyof NotificationSettings['events']

const eventLabels: Record<EventKey, string> = {
  process_started: 'PROCESS START',
  process_exited: 'PROCESS EXIT',
  user_input_required: 'INPUT NEEDED',
  subagent_completed: 'AGENT DONE',
}
</script>

<template>
  <div class="notification-area">
    <button class="bell-btn" @click="togglePanel" :class="{ active: showPanel }">
      <span class="bell-icon">{{ showPanel ? '■' : '◆' }}</span>
      <span class="unread-badge" v-if="unread > 0">{{ unread > 9 ? '9+' : unread }}</span>
    </button>

    <Transition name="panel">
      <div class="notification-panel" v-if="showPanel">
        <div class="panel-header">
          <span class="panel-title">ALERTS</span>
          <div class="panel-header-actions">
            <button class="header-btn" @click="toggleSettings" :class="{ active: showSettings }" title="Settings">[S]</button>
            <button class="close-btn" @click="showPanel = false">[X]</button>
          </div>
        </div>

        <!-- Settings section -->
        <div class="settings-section" v-if="showSettings">
          <div class="settings-group">
            <div class="settings-row master-toggle" @click="emit('updateSettings', { desktop: !settings.desktop })">
              <span class="toggle-check">{{ settings.desktop ? '[X]' : '[ ]' }}</span>
              <span class="toggle-label">DESKTOP NOTIFY</span>
            </div>

            <div class="permission-row" v-if="permission !== 'granted'">
              <button class="enable-btn" @click="emit('requestPermission')">
                {{ permission === 'default' ? '[ENABLE]' : '[DENIED]' }}
              </button>
            </div>
            <div class="permission-row" v-else>
              <span class="permission-granted">[ENABLED]</span>
            </div>

            <div class="settings-row master-toggle" @click="emit('updateSettings', { sound: !settings.sound })">
              <span class="toggle-check">{{ settings.sound ? '[X]' : '[ ]' }}</span>
              <span class="toggle-label">SOUND ALERT</span>
            </div>
          </div>

          <div class="settings-divider"></div>

          <div class="settings-group">
            <div class="settings-label">EVENT TYPES</div>
            <div
              v-for="(label, key) in eventLabels"
              :key="key"
              class="settings-row"
              @click="toggleEvent(key)"
            >
              <span class="toggle-check">{{ settings.events[key as EventKey] ? '[X]' : '[ ]' }}</span>
              <span class="toggle-label">{{ label }}</span>
            </div>
          </div>
        </div>

        <!-- Notifications list -->
        <div class="panel-body" v-if="!showSettings">
          <div class="no-notifications" v-if="notifications.length === 0">
            <p class="empty-frame">
            ┌────────────┐
            │  NO ALERTS │
            └────────────┘
            </p>
          </div>
          <div
            v-for="(notif, idx) in [...notifications].reverse()"
            :key="idx"
            class="notif-item"
            :class="notif.type"
          >
            <span class="notif-icon">{{ getNotifIcon(notif.type) }}</span>
            <div class="notif-content">
              <div class="notif-title">{{ getNotifTitle(notif.type) }}</div>
              <div class="notif-desc">{{ getNotifBody(notif) }}</div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.notification-area {
  position: relative;
}

.bell-btn {
  background: var(--bg-tertiary);
  border: 2px solid var(--border);
  cursor: pointer;
  padding: 6px 10px;
  position: relative;
  color: var(--text-secondary);
  transition: all 0.1s step-end;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-pixel);
  font-size: 12px;
}

.bell-btn:hover {
  background: var(--bg-tertiary);
  color: var(--accent);
  border-color: var(--accent);
}

.bell-btn.active {
  background: var(--accent-bg);
  color: var(--accent);
  border-color: var(--accent);
}

.bell-icon {
  font-size: 12px;
}

.unread-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: var(--danger);
  color: var(--text-inverse);
  font-size: 7px;
  min-width: 14px;
  height: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-family: var(--font-pixel);
  border: 2px solid var(--bg-secondary);
}

.notification-panel {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  width: 340px;
  max-height: 400px;
  background: var(--bg-primary);
  border: 2px solid var(--border);
  box-shadow: var(--shadow-elevated);
  z-index: 100;
  overflow: hidden;
}

.panel-enter-active,
.panel-leave-active {
  transition: all 0.1s step-end;
}

.panel-enter-from,
.panel-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-bottom: 2px solid var(--border);
  background: var(--bg-secondary);
}

.panel-title {
  font-size: 9px;
  font-family: var(--font-pixel);
  color: var(--text-primary);
  letter-spacing: 2px;
}

.panel-header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.header-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 2px 4px;
  font-family: var(--font-pixel);
  font-size: 8px;
  transition: color 0.1s step-end;
}

.header-btn:hover {
  color: var(--accent);
}

.header-btn.active {
  color: var(--accent);
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 2px 4px;
  font-family: var(--font-pixel);
  font-size: 8px;
  transition: color 0.1s step-end;
}

.close-btn:hover {
  color: var(--danger);
}

/* Settings section */
.settings-section {
  padding: 12px 16px;
  border-bottom: 2px solid var(--border);
  background: var(--bg-secondary);
}

.settings-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.settings-label {
  font-family: var(--font-pixel);
  font-size: 7px;
  color: var(--text-muted);
  letter-spacing: 1px;
  margin-bottom: 2px;
}

.settings-row {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 0;
  transition: color 0.1s step-end;
}

.settings-row:hover {
  color: var(--accent);
}

.toggle-check {
  font-family: var(--font-pixel);
  font-size: 9px;
  color: var(--text-secondary);
  width: 32px;
  flex-shrink: 0;
}

.settings-row:hover .toggle-check {
  color: var(--accent);
}

.toggle-label {
  font-family: var(--font-pixel);
  font-size: 8px;
  color: var(--text-primary);
  letter-spacing: 1px;
}

.settings-row:hover .toggle-label {
  color: var(--accent);
}

.master-toggle {
  padding: 6px 0;
}

.settings-divider {
  height: 2px;
  background: var(--border-light);
  margin: 8px 0;
}

.permission-row {
  padding: 4px 0 4px 40px;
}

.enable-btn {
  background: none;
  border: 2px solid var(--info);
  color: var(--info);
  cursor: pointer;
  padding: 3px 10px;
  font-family: var(--font-pixel);
  font-size: 8px;
  transition: all 0.1s step-end;
}

.enable-btn:hover {
  background: var(--info-bg);
}

.permission-granted {
  font-family: var(--font-pixel);
  font-size: 8px;
  color: var(--success);
  letter-spacing: 1px;
}

/* Panel body / notification list */
.panel-body {
  max-height: 340px;
  overflow-y: auto;
}

.no-notifications {
  padding: 40px 16px;
  text-align: center;
}

.empty-frame {
  font-family: var(--font-pixel);
  font-size: 8px;
  line-height: 2;
  color: var(--text-muted);
  white-space: pre;
}

.notif-item {
  display: flex;
  gap: 10px;
  padding: 8px 16px;
  border-bottom: 1px dashed var(--border-light);
  transition: background 0.1s step-end;
}

.notif-item:hover {
  background: var(--bg-tertiary);
}

.notif-item:last-child {
  border-bottom: none;
}

.notif-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-pixel);
  font-size: 10px;
  flex-shrink: 0;
  border: 1px solid;
}

.notif-item.process_started .notif-icon {
  border-color: var(--success);
  color: var(--success);
  background: var(--success-bg);
}

.notif-item.process_exited .notif-icon {
  border-color: var(--danger);
  color: var(--danger);
  background: var(--danger-bg);
}

.notif-item.user_input_required .notif-icon {
  border-color: var(--info);
  color: var(--info);
  background: var(--info-bg);
}

.notif-item.subagent_completed .notif-icon {
  border-color: var(--success);
  color: var(--success);
  background: var(--success-bg);
}

.notif-content {
  min-width: 0;
  flex: 1;
}

.notif-title {
  font-size: 8px;
  font-family: var(--font-pixel);
  color: var(--text-primary);
  letter-spacing: 1px;
}

.notif-desc {
  font-size: 11px;
  font-family: var(--font-body);
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}
</style>
