<script setup lang="ts">
import type { ProcessInfo } from '../composables/useWebSocket'
import PixelAvatar from './PixelAvatar.vue'

defineProps<{
  processes: ProcessInfo[]
  selectedPid: number | null
}>()

const emit = defineEmits<{
  select: [pid: number]
}>()

function statusLabel(status: string) {
  switch (status) {
    case 'running': return 'ACTIVE'
    case 'idle': return 'IDLE'
    default: return status.toUpperCase()
  }
}

function needsUserInput(proc: ProcessInfo) {
  if (proc.status !== 'idle') return false
  const logs = proc.session_info?.recent_logs
  if (!logs || logs.length === 0) return false
  const lastLog = logs[logs.length - 1]
  return lastLog.role === 'assistant'
}

function formatTime(isoStr: string) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function shortCwd(cwd: string | null) {
  if (!cwd) return '???'
  const parts = cwd.replace(/\\/g, '/').split('/')
  return parts.slice(-2).join('/')
}
</script>

<template>
  <div class="process-list">
    <div class="list-header">
      <span class="header-label">PROCESSES</span>
      <span class="count">{{ processes.length }}</span>
    </div>

    <div class="list-empty" v-if="processes.length === 0">
      <p class="empty-icon">┌─────────────┐</p>
      <p class="empty-icon">│ NO PROCESS  │</p>
      <p class="empty-icon">│  DETECTED   │</p>
      <p class="empty-icon">└─────────────┘</p>
      <p class="hint">// Claude Code not running</p>
    </div>

    <div
      v-for="proc in processes"
      :key="proc.pid"
      class="process-item"
      :class="{
        selected: selectedPid === proc.pid,
        waiting: needsUserInput(proc)
      }"
      @click="emit('select', proc.pid)"
    >
      <div class="item-row">
        <PixelAvatar
          :seed="String(proc.pid)"
          :size="36"
          :status="proc.status"
        />
        <div class="item-info">
          <div class="item-top">
            <span class="pid">PID:{{ proc.pid }}</span>
            <span v-if="proc.status === 'running'" class="working-indicator" title="Working"></span>
            <span v-if="needsUserInput(proc)" class="input-indicator" title="Waiting for user input"></span>
            <span class="status-text" :class="proc.status">{{ statusLabel(proc.status) }}</span>
          </div>
          <div class="item-project">{{ proc.project_name || shortCwd(proc.cwd) }}</div>
          <div class="item-meta">
            <span>CPU {{ proc.cpu_percent.toFixed(1) }}%</span>
            <span>│</span>
            <span>{{ proc.memory_mb }}MB</span>
            <span>│</span>
            <span>{{ formatTime(proc.create_time) }}</span>
            <template v-if="proc.session_info?.subagents?.length">
              <span>│</span>
              <span class="sa-badge" v-if="proc.session_info.subagents.some(s => s.status === 'running')">SA:{{ proc.session_info.subagents.filter(s => s.status === 'running').length }}/{{ proc.session_info.subagents.length }}</span>
              <span class="sa-badge sa-done" v-else>SA:{{ proc.session_info.subagents.length }}</span>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.process-list {
  width: 300px;
  min-width: 300px;
  background: var(--bg-primary);
  border-right: 2px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.list-header {
  padding: 10px 16px;
  background: var(--bg-secondary);
  border-bottom: 2px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-label {
  font-size: 9px;
  font-family: var(--font-pixel);
  color: var(--text-muted);
  letter-spacing: 2px;
}

.count {
  background: var(--bg-tertiary);
  border: 2px solid var(--border);
  padding: 2px 10px;
  font-size: 10px;
  font-family: var(--font-pixel);
  color: var(--accent);
}

.list-empty {
  padding: 48px 16px;
  text-align: center;
}

.empty-icon {
  font-family: var(--font-pixel);
  font-size: 8px;
  color: var(--text-muted);
  line-height: 1.6;
  white-space: pre;
}

.hint {
  font-size: 11px;
  margin-top: 12px;
  color: var(--text-muted);
  font-family: var(--font-body);
}

.process-item {
  padding: 10px 16px;
  cursor: pointer;
  border-bottom: 2px solid var(--border-light);
  border-left: 3px solid transparent;
  transition: all 0.1s step-end;
}

.process-item:hover {
  background: var(--bg-tertiary);
  border-left-color: var(--text-muted);
}

.process-item.selected {
  background: var(--accent-bg);
  border-left-color: var(--accent);
}

.process-item.selected .pid {
  color: var(--accent);
}

.process-item.waiting {
  border-left-color: var(--info);
  background: var(--info-bg);
}

.process-item.waiting:hover {
  background: var(--bg-tertiary);
}

.working-indicator {
  display: inline-block;
  width: 8px;
  height: 8px;
  background: var(--success);
  border: 2px solid var(--success);
  animation: input-blink 1s step-end infinite;
  box-shadow: 0 0 6px var(--success);
  flex-shrink: 0;
}

.input-indicator {
  display: inline-block;
  width: 8px;
  height: 8px;
  background: var(--info);
  border: 2px solid var(--info);
  animation: input-blink 1s step-end infinite;
  box-shadow: 0 0 6px var(--info);
  flex-shrink: 0;
}

@keyframes input-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }
}

.item-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.pid {
  font-size: 10px;
  font-family: var(--font-pixel);
  color: var(--text-primary);
}

.status-text {
  font-size: 8px;
  font-family: var(--font-pixel);
  margin-left: auto;
  padding: 2px 8px;
  border: 2px solid;
  letter-spacing: 1px;
}

.status-text.running {
  border-color: var(--success);
  color: var(--success);
  background: var(--success-bg);
  text-shadow: var(--glow-success);
}

.status-text.idle {
  border-color: var(--warning);
  color: var(--warning);
  background: var(--warning-bg);
}

.item-project {
  font-size: 12px;
  font-family: var(--font-body);
  color: var(--text-secondary);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-meta {
  display: flex;
  gap: 6px;
  font-size: 10px;
  font-family: var(--font-pixel);
  color: var(--text-muted);
  align-items: center;
}

.sa-badge {
  font-size: 7px;
  color: var(--success);
  border: 1px solid var(--success);
  background: var(--success-bg);
  padding: 0 4px;
  letter-spacing: 1px;
}

.sa-badge.sa-done {
  color: var(--text-muted);
  border-color: var(--border);
  background: transparent;
}
</style>
