<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Notification } from '../composables/useWebSocket'

const props = defineProps<{
  notifications: Notification[]
}>()

const showPanel = ref(false)
const unread = ref(0)

watch(() => props.notifications.length, (newLen, oldLen) => {
  if (newLen > (oldLen ?? 0)) {
    unread.value += newLen - (oldLen ?? 0)
    const latest = props.notifications[props.notifications.length - 1]
    if (latest && 'Notification' in window && Notification.permission === 'granted') {
      new Notification('Claude Monitor', {
        body: latest.type === 'process_started'
          ? `New process: ${latest.project || latest.pid}`
          : `Process exited: PID ${latest.pid}`,
      })
    }
  }
})

function togglePanel() {
  showPanel.value = !showPanel.value
  if (showPanel.value) {
    unread.value = 0
  }
}

function formatTime(isoStr: string | undefined) {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
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
          <button class="close-btn" @click="showPanel = false">[X]</button>
        </div>
        <div class="panel-body">
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
            <span class="notif-icon">{{ notif.type === 'process_started' ? '+' : 'x' }}</span>
            <div class="notif-content">
              <div class="notif-title">
                {{ notif.type === 'process_started' ? 'PROCESS START' : 'PROCESS EXIT' }}
              </div>
              <div class="notif-desc">
                {{ notif.type === 'process_started'
                  ? `${notif.project || notif.pid} PID:${notif.pid}`
                  : `PID ${notif.pid}`
                }}
              </div>
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
