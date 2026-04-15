<script setup lang="ts">
import { computed } from 'vue'
import type { ProcessInfo } from '../composables/useWebSocket'

// Dashboard stats bar
const props = defineProps<{
  stats: { running: number; idle: number; total: number }
  processes: ProcessInfo[]
}>()

const totalInput = computed(() =>
  props.processes.reduce((sum, p) => sum + (p.session_info?.token_usage?.input_tokens || 0), 0)
)
const totalOutput = computed(() =>
  props.processes.reduce((sum, p) => sum + (p.session_info?.token_usage?.output_tokens || 0), 0)
)
const totalCache = computed(() =>
  props.processes.reduce((sum, p) => sum + (p.session_info?.token_usage?.cache_read_tokens || 0), 0)
)
const totalDuration = computed(() =>
  props.processes.reduce((sum, p) => sum + (p.session_info?.duration_seconds || 0), 0)
)

const showTokenRow = computed(() => totalInput.value > 0 || totalOutput.value > 0)

function formatTokens(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return String(n)
}

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}h${String(m).padStart(2, '0')}m`
  if (m > 0) return `${m}m${String(s).padStart(2, '0')}s`
  return `${s}s`
}
</script>

<template>
  <div class="status-bar">
    <div class="status-item">
      <span class="status-icon">▪</span>
      <span class="status-label">PROCESS</span>
      <span class="status-num">{{ stats.total }}</span>
    </div>
    <span class="divider">│</span>
    <div class="status-item">
      <span class="status-dot running"></span>
      <span class="status-label">ACTIVE</span>
      <span class="status-num running">{{ stats.running }}</span>
    </div>
    <span class="divider">│</span>
    <div class="status-item">
      <span class="status-dot idle"></span>
      <span class="status-label">IDLE</span>
      <span class="status-num idle">{{ stats.idle }}</span>
    </div>
  </div>
  <div v-if="showTokenRow" class="status-bar token-bar">
    <div class="status-item">
      <span class="status-icon">◆</span>
      <span class="status-label">INPUT</span>
      <span class="status-num token-val">{{ formatTokens(totalInput) }}</span>
    </div>
    <span class="divider">│</span>
    <div class="status-item">
      <span class="status-icon">◆</span>
      <span class="status-label">OUTPUT</span>
      <span class="status-num token-val">{{ formatTokens(totalOutput) }}</span>
    </div>
    <span class="divider">│</span>
    <div class="status-item">
      <span class="status-icon">◇</span>
      <span class="status-label">CACHE</span>
      <span class="status-num token-val">{{ formatTokens(totalCache) }}</span>
    </div>
    <span class="divider">│</span>
    <div class="status-item">
      <span class="status-icon">▶</span>
      <span class="status-label">DURATION</span>
      <span class="status-num token-val">{{ formatDuration(totalDuration) }}</span>
    </div>
  </div>
</template>

<style scoped>
.status-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 6px 20px;
  background: var(--bg-secondary);
  border-bottom: 2px solid var(--border);
  height: 32px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-icon {
  font-size: 10px;
  color: var(--text-muted);
}

.status-dot {
  width: 8px;
  height: 8px;
  flex-shrink: 0;
}

.status-dot.running {
  background: var(--success);
  box-shadow: var(--glow-success);
  animation: pulse-glow 2s ease-in-out infinite;
}

.status-dot.idle {
  background: var(--warning);
  box-shadow: var(--glow-accent);
}

.status-label {
  font-size: 9px;
  font-family: var(--font-pixel);
  color: var(--text-muted);
  letter-spacing: 1px;
}

.status-num {
  font-size: 11px;
  font-family: var(--font-pixel);
  color: var(--text-primary);
}

.status-num.running {
  color: var(--success);
  text-shadow: var(--glow-success);
}

.status-num.idle {
  color: var(--warning);
}

.divider {
  color: var(--border);
  font-size: 14px;
  line-height: 1;
}

@keyframes pulse-glow {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.token-bar {
  background: var(--bg-tertiary);
  border-bottom: 2px solid var(--border);
}

.token-val {
  color: var(--accent);
}
</style>
