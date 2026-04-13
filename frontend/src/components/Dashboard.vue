<script setup lang="ts">
// Dashboard stats bar
defineProps<{
  stats: { running: number; idle: number; total: number }
}>()
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
</style>
