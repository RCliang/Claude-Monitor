<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { ProcessInfo } from '../composables/useWebSocket'

const props = defineProps<{
  processes: ProcessInfo[]
  connected: boolean
}>()

const emit = defineEmits<{
  (e: 'expand'): void
  (e: 'selectProcess', pid: number): void
}>()

// --- Drag support ---
const overlayRef = ref<HTMLElement | null>(null)
const pos = ref({ x: window.innerWidth - 320, y: 16 })
const dragging = ref(false)
const dragOffset = ref({ x: 0, y: 0 })

function onDragStart(e: MouseEvent) {
  // Only drag from title bar
  const target = e.target as HTMLElement
  if (!target.closest('.mini-titlebar')) return
  dragging.value = true
  dragOffset.value = { x: e.clientX - pos.value.x, y: e.clientY - pos.value.y }
  e.preventDefault()
}

function onDragMove(e: MouseEvent) {
  if (!dragging.value) return
  pos.value = {
    x: Math.max(0, Math.min(window.innerWidth - 300, e.clientX - dragOffset.value.x)),
    y: Math.max(0, Math.min(window.innerHeight - 200, e.clientY - dragOffset.value.y)),
  }
}

function onDragEnd() {
  dragging.value = false
}

onMounted(() => {
  window.addEventListener('mousemove', onDragMove)
  window.addEventListener('mouseup', onDragEnd)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onDragMove)
  window.removeEventListener('mouseup', onDragEnd)
})

// --- Computed data ---
const runningCount = computed(() => props.processes.filter(p => p.status === 'running').length)
const waitingCount = computed(() =>
  props.processes.filter(p => {
    if (p.status !== 'idle') return false
    const state = p.session_info?.activity_state
    return state === 'waiting'
  }).length
)

const totalInput = computed(() =>
  props.processes.reduce((sum, p) => sum + (p.session_info?.token_usage?.input_tokens || 0), 0)
)
const totalOutput = computed(() =>
  props.processes.reduce((sum, p) => sum + (p.session_info?.token_usage?.output_tokens || 0), 0)
)

const processRows = computed(() =>
  props.processes.map(p => {
    const state = p.session_info?.activity_state
    let status = 'IDLE'
    let cls = 'idle'
    if (p.status === 'running') {
      if (state === 'thinking') { status = 'THINK'; cls = 'thinking' }
      else if (state === 'executing') { status = 'EXEC'; cls = 'executing' }
      else { status = 'RUN'; cls = 'running' }
    } else if (state === 'waiting') {
      status = 'WAIT'; cls = 'waiting'
    }
    const saList = p.session_info?.subagents || []
    const runningSA = saList.filter(s => s.status === 'running').length
    const totalSA = saList.length
    return {
      pid: p.pid,
      name: p.project_name || '???',
      status,
      cls,
      runningSA,
      totalSA,
    }
  })
)

function formatTokens(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return String(n)
}
</script>

<template>
  <div
    ref="overlayRef"
    class="mini-overlay"
    :style="{ left: pos.x + 'px', top: pos.y + 'px' }"
    @mousedown="onDragStart"
  >
    <!-- Title bar -->
    <div class="mini-titlebar">
      <span class="mini-logo">
        <span class="logo-bracket">[</span>CM<span class="logo-bracket">]</span>
      </span>
      <span class="mini-conn" :class="connected ? 'on' : 'off'">
        {{ connected ? '◆' : '◇' }}
      </span>
      <span class="mini-summary">
        {{ processes.length }} PROC
        <span v-if="runningCount" class="sum-run"> | {{ runningCount }} RUN</span>
        <span v-if="waitingCount" class="sum-wait"> | {{ waitingCount }} WAIT</span>
      </span>
      <button class="mini-expand" @click.stop="emit('expand')" title="Expand [Ctrl+M]">▼</button>
    </div>

    <!-- Process rows -->
    <div class="mini-body">
      <div
        v-for="row in processRows"
        :key="row.pid"
        class="mini-row"
        :class="row.cls"
        @click.stop="emit('selectProcess', row.pid)"
      >
        <span class="row-dot" :class="row.cls"></span>
        <span class="row-name">{{ row.name }}</span>
        <span class="row-status" :class="row.cls">{{ row.status }}</span>
        <span class="row-sa" v-if="row.totalSA > 0">SA:{{ row.runningSA }}/{{ row.totalSA }}</span>
      </div>
    </div>

    <!-- Token bar -->
    <div class="mini-token" v-if="totalInput > 0 || totalOutput > 0">
      <span class="tok-label">IN:{{ formatTokens(totalInput) }}</span>
      <span class="tok-sep">│</span>
      <span class="tok-label">OUT:{{ formatTokens(totalOutput) }}</span>
    </div>
  </div>
</template>

<style scoped>
.mini-overlay {
  position: fixed;
  z-index: 9998;
  width: 280px;
  background: var(--bg-primary);
  border: 2px solid var(--accent);
  box-shadow: 4px 4px 0px rgba(0, 0, 0, 0.5);
  font-family: var(--font-pixel);
  user-select: none;
  overflow: hidden;
}

[data-theme="dark"] .mini-overlay {
  background: rgba(10, 10, 26, 0.92);
}

/* Title bar */
.mini-titlebar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: var(--bg-secondary);
  border-bottom: 2px solid var(--accent);
  cursor: grab;
  font-size: 8px;
}

.mini-titlebar:active {
  cursor: grabbing;
}

.mini-logo {
  color: var(--accent);
  font-size: 8px;
  letter-spacing: 1px;
  flex-shrink: 0;
}

.logo-bracket {
  color: var(--text-muted);
}

.mini-conn {
  font-size: 6px;
  flex-shrink: 0;
}

.mini-conn.on { color: var(--success); }
.mini-conn.off { color: var(--danger); animation: blink 1.2s step-end infinite; }

.mini-summary {
  font-size: 7px;
  color: var(--text-secondary);
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sum-run { color: var(--success); }
.sum-wait { color: var(--info); }

.mini-expand {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-family: var(--font-pixel);
  font-size: 10px;
  padding: 0 2px;
  transition: color 0.1s step-end;
  flex-shrink: 0;
}

.mini-expand:hover {
  color: var(--accent);
}

/* Process rows */
.mini-body {
  max-height: 180px;
  overflow-y: auto;
}

.mini-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 8px;
  cursor: pointer;
  transition: background 0.1s step-end;
  border-bottom: 1px solid var(--border-light);
  font-size: 7px;
}

.mini-row:hover {
  background: var(--bg-tertiary);
}

.mini-row:last-child {
  border-bottom: none;
}

.row-dot {
  width: 8px;
  height: 8px;
  flex-shrink: 0;
}

.row-dot.running, .row-dot.executing {
  background: var(--success);
  box-shadow: var(--glow-success);
}

.row-dot.thinking {
  background: var(--thinking);
  box-shadow: var(--thinking-glow);
  animation: blink 1.2s step-end infinite;
}

.row-dot.idle {
  background: var(--warning);
}

.row-dot.waiting {
  background: var(--info);
  box-shadow: var(--glow-info);
  animation: input-blink 1s step-end infinite;
}

.row-name {
  color: var(--text-primary);
  font-size: 7px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.row-status {
  font-size: 6px;
  letter-spacing: 1px;
  flex-shrink: 0;
}

.row-status.running, .row-status.executing { color: var(--success); }
.row-status.thinking { color: var(--thinking); }
.row-status.idle { color: var(--warning); }
.row-status.waiting { color: var(--info); }

.row-sa {
  font-size: 6px;
  color: var(--text-muted);
  flex-shrink: 0;
}

/* Token bar */
.mini-token {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 3px 8px;
  background: var(--bg-tertiary);
  border-top: 2px solid var(--border);
}

.tok-label {
  font-size: 6px;
  color: var(--accent);
  letter-spacing: 0.5px;
}

.tok-sep {
  font-size: 8px;
  color: var(--border);
}

/* Animations */
@keyframes blink {
  50% { opacity: 0.3; }
}

@keyframes input-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }
}
</style>
