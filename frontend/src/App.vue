<script setup lang="ts">
import { ref, computed } from 'vue'
import { useWebSocket } from './composables/useWebSocket'
import { useTheme } from './composables/useTheme'
import Dashboard from './components/Dashboard.vue'
import ProcessList from './components/ProcessList.vue'
import ProcessDetail from './components/ProcessDetail.vue'
import NotificationPanel from './components/NotificationPanel.vue'

const { processes, notifications, connected } = useWebSocket()
const { theme, toggle } = useTheme()
const selectedPid = ref<number | null>(null)

const selectedProcess = computed(() => {
  if (selectedPid.value === null) return null
  return processes.value.find(p => p.pid === selectedPid.value) ?? null
})

const stats = computed(() => {
  const running = processes.value.filter(p => p.status === 'running').length
  const idle = processes.value.filter(p => p.status === 'idle').length
  const total = processes.value.length
  return { running, idle, total }
})

function selectProcess(pid: number) {
  selectedPid.value = pid
}
</script>

<template>
  <div class="app" :data-theme="theme">
    <!-- CRT scanline overlay (dark only) -->
    <div class="scanlines" v-if="theme === 'dark'"></div>

    <header class="header">
      <div class="header-left">
        <h1 class="logo">
          <span class="logo-icon">
            <span class="logo-bracket">[</span>
            <span class="logo-text">CM</span>
            <span class="logo-bracket">]</span>
          </span>
          <span class="logo-title">Claude Monitor</span>
        </h1>
        <span class="connection-badge" :class="connected ? 'connected' : 'disconnected'">
          <span class="badge-icon">{{ connected ? '◆' : '◇' }}</span>
          {{ connected ? 'ONLINE' : 'OFFLINE' }}
        </span>
      </div>
      <div class="header-right">
        <button class="theme-toggle" @click="toggle" :title="theme === 'dark' ? 'Switch to light' : 'Switch to dark'">
          <span class="toggle-icon">{{ theme === 'dark' ? '◉' : '◎' }}</span>
        </button>
        <NotificationPanel :notifications="notifications" />
      </div>
    </header>

    <Dashboard :stats="stats" :processes="processes" />

    <main class="main-content">
      <ProcessList
        :processes="processes"
        :selected-pid="selectedPid"
        @select="selectProcess"
      />
      <ProcessDetail :process="selectedProcess" />
    </main>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Silkscreen:wght@400;700&display=swap');

/* ===== DARK THEME (default) ===== */
:root,
[data-theme="dark"] {
  --bg-primary: #0a0a1a;
  --bg-secondary: #111128;
  --bg-tertiary: #1a1a3e;
  --bg-inset: #0d0d24;

  --border: #2a2a5a;
  --border-light: #1e1e44;

  --text-primary: #e0e0ff;
  --text-secondary: #8888bb;
  --text-muted: #555580;
  --text-inverse: #0a0a1a;

  --accent: #ffaa00;
  --accent-light: #ffcc44;
  --accent-bg: #1a1500;

  --success: #00ff41;
  --success-bg: #001a00;
  --warning: #ffcc00;
  --warning-bg: #1a1500;
  --danger: #ff4444;
  --danger-bg: #1a0000;
  --info: #00d4ff;
  --info-bg: #001a22;

  --shadow-subtle: 4px 4px 0px rgba(0, 0, 0, 0.4);
  --shadow-medium: 6px 6px 0px rgba(0, 0, 0, 0.5);
  --shadow-elevated: 8px 8px 0px rgba(0, 0, 0, 0.6);

  --glow-accent: 0 0 8px rgba(255, 170, 0, 0.4);
  --glow-success: 0 0 8px rgba(0, 255, 65, 0.4);
  --glow-danger: 0 0 8px rgba(255, 68, 68, 0.4);
  --glow-info: 0 0 8px rgba(0, 212, 255, 0.4);

  --thinking: #A78BFA;
  --thinking-border: #7C3AED;
  --thinking-bg: #1a0a3e;
  --thinking-glow: 0 0 6px rgba(124, 58, 237, 0.4);

  --avatar-bg-lightness: 12%;
  --avatar-fg-saturation: 90%;
  --scanline-opacity: 0.08;
}

/* ===== LIGHT THEME ===== */
[data-theme="light"] {
  --bg-primary: #f0f0f0;
  --bg-secondary: #e4e4e8;
  --bg-tertiary: #d4d4dc;
  --bg-inset: #e8e8ec;

  --border: #b0b0c0;
  --border-light: #c4c4d0;

  --text-primary: #1a1a2e;
  --text-secondary: #4a4a6a;
  --text-muted: #808098;
  --text-inverse: #f0f0f0;

  --accent: #d97706;
  --accent-light: #f59e0b;
  --accent-bg: #fff7ed;

  --success: #16a34a;
  --success-bg: #f0fdf4;
  --warning: #ca8a04;
  --warning-bg: #fefce8;
  --danger: #dc2626;
  --danger-bg: #fef2f2;
  --info: #2563eb;
  --info-bg: #eff6ff;

  --shadow-subtle: 3px 3px 0px rgba(0, 0, 0, 0.12);
  --shadow-medium: 5px 5px 0px rgba(0, 0, 0, 0.15);
  --shadow-elevated: 7px 7px 0px rgba(0, 0, 0, 0.18);

  --glow-accent: none;
  --glow-success: none;
  --glow-danger: none;
  --glow-info: none;

  --thinking: #7C3AED;
  --thinking-border: #7C3AED;
  --thinking-bg: #f3f0ff;
  --thinking-glow: none;

  --avatar-bg-lightness: 88%;
  --avatar-fg-saturation: 65%;
  --scanline-opacity: 0;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-body);
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.5;
  -webkit-font-smoothing: none;
  -moz-osx-font-smoothing: unset;
  image-rendering: pixelated;
}

/* CRT Scanline effect */
.scanlines {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 9999;
  background: repeating-linear-gradient(
    0deg,
    rgba(0, 0, 0, var(--scanline-opacity)) 0px,
    rgba(0, 0, 0, var(--scanline-opacity)) 1px,
    transparent 1px,
    transparent 3px
  );
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* Header */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 20px;
  background: var(--bg-secondary);
  border-bottom: 3px solid var(--accent);
  position: relative;
}

/* Decorative pixel corners */
.header::before,
.header::after {
  content: '';
  position: absolute;
  bottom: -3px;
  width: 12px;
  height: 3px;
  background: var(--accent-light);
}
.header::before { left: 0; }
.header::after { right: 0; }

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Theme toggle button */
.theme-toggle {
  background: var(--bg-tertiary);
  border: 2px solid var(--border);
  cursor: pointer;
  padding: 6px 10px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-pixel);
  font-size: 14px;
  transition: all 0.1s step-end;
}

.theme-toggle:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.theme-toggle:active {
  transform: translate(2px, 2px);
  box-shadow: none;
}

.toggle-icon {
  line-height: 1;
}

.logo {
  font-size: 10px;
  font-family: var(--font-pixel);
  display: flex;
  align-items: center;
  gap: 10px;
  letter-spacing: 0;
}

.logo-icon {
  display: inline-flex;
  align-items: center;
  gap: 0;
  background: var(--accent);
  color: var(--text-inverse);
  padding: 6px 8px;
  border: 2px solid var(--accent-light);
  box-shadow: var(--shadow-subtle);
  line-height: 1;
}

.logo-bracket {
  color: var(--bg-primary);
  font-size: 10px;
}

.logo-text {
  font-size: 10px;
  letter-spacing: 1px;
}

.logo-title {
  color: var(--text-primary);
  font-size: 12px;
}

[data-theme="dark"] .logo-title {
  text-shadow: 0 0 10px rgba(255, 170, 0, 0.5);
}

.connection-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 9px;
  font-family: var(--font-pixel);
  padding: 4px 12px;
  border: 2px solid;
  letter-spacing: 1px;
}

.connection-badge.connected {
  border-color: var(--success);
  color: var(--success);
  background: var(--success-bg);
}

[data-theme="dark"] .connection-badge.connected {
  text-shadow: var(--glow-success);
}

.connection-badge.disconnected {
  border-color: var(--danger);
  color: var(--danger);
  background: var(--danger-bg);
  animation: blink 1.2s step-end infinite;
}

.badge-icon {
  font-size: 8px;
}

@keyframes blink {
  50% { opacity: 0.3; }
}

/* Main content */
.main-content {
  flex: 1;
  display: flex;
  gap: 0;
  overflow: hidden;
}

/* Scrollbar styling - pixelated */
::-webkit-scrollbar {
  width: 12px;
}

::-webkit-scrollbar-track {
  background: var(--bg-primary);
  border-left: 2px solid var(--border);
}

::-webkit-scrollbar-thumb {
  background: var(--bg-tertiary);
  border: 2px solid var(--border);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--accent);
  border-color: var(--accent-light);
}

/* Global selection */
::selection {
  background: var(--accent);
  color: var(--text-inverse);
}
</style>
