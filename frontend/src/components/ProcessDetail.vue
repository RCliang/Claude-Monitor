<script setup lang="ts">
import { ref, computed } from 'vue'
import type { ProcessInfo, TodoItem, SubagentInfo } from '../composables/useWebSocket'
import PixelAvatar from './PixelAvatar.vue'

const props = defineProps<{
  process: ProcessInfo | null
}>()

const expandedLogs = ref<Set<number>>(new Set())
const sessionExpanded = ref(false)
const toolkitExpanded = ref(false)
const subagentsExpanded = ref(true)

interface ToolItem {
  name: string
  desc: string
}

interface ToolGroup {
  group: string
  icon: string
  items: ToolItem[]
}

const toolkitData: ToolGroup[] = [
  {
    group: 'SKILLS',
    icon: '⚔',
    items: [
      { name: 'algorithmic-art', desc: 'p5.js 算法艺术生成' },
      { name: 'brand-guidelines', desc: 'Anthropic 品牌色彩/排版' },
      { name: 'canvas-design', desc: 'PNG/PDF 视觉设计' },
      { name: 'doc-coauthoring', desc: '文档协作写作工作流' },
      { name: 'docx', desc: 'Word 文档创建/编辑/分析' },
      { name: 'frontend-design', desc: '高质量前端界面设计' },
      { name: 'internal-comms', desc: '内部沟通文档写作' },
      { name: 'mcp-builder', desc: '构建 MCP Server' },
      { name: 'pdf', desc: 'PDF 操作工具集' },
      { name: 'pptx', desc: 'PPT 演示文稿操作' },
      { name: 'skill-creator', desc: '创建新 Skill' },
      { name: 'slack-gif-creator', desc: 'Slack 动画 GIF 创建' },
      { name: 'theme-factory', desc: '主题样式工具包' },
      { name: 'web-artifacts-builder', desc: '多组件 HTML artifacts' },
      { name: 'webapp-testing', desc: 'Playwright Web 测试' },
      { name: 'xlsx', desc: 'Excel 电子表格操作' },
      { name: 'mermaid-visualizer', desc: 'Mermaid 图表可视化' },
      { name: 'excalidraw-diagram', desc: 'Excalidraw 图表生成' },
      { name: 'obsidian-canvas-creator', desc: 'Obsidian Canvas 创建' },
      { name: 'brainstorming', desc: '创意探索与需求分析' },
      { name: 'dispatching-parallel-agents', desc: '并行任务调度' },
      { name: 'executing-plans', desc: '执行实施计划' },
      { name: 'systematic-debugging', desc: '系统化调试' },
      { name: 'test-driven-development', desc: '测试驱动开发' },
      { name: 'writing-plans', desc: '编写实施计划' },
      { name: 'requesting-code-review', desc: '请求代码审查' },
      { name: 'usage-query', desc: '查询账户用量' },
    ]
  },
  {
    group: 'MCP TOOLS',
    icon: '🛡',
    items: [
      { name: 'analyze_image', desc: 'AI 视觉图像分析' },
      { name: 'webReader', desc: 'URL 转 Markdown 读取' },
      { name: 'web_search_prime', desc: '网页搜索' },
      { name: 'analyze_data_visualization', desc: '数据可视化图表分析' },
      { name: 'analyze_video', desc: '视频内容分析' },
      { name: 'diagnose_error_screenshot', desc: '错误截图诊断' },
      { name: 'extract_text_from_screenshot', desc: 'OCR 文字提取' },
      { name: 'ui_diff_check', desc: 'UI 截图对比' },
      { name: 'ui_to_artifact', desc: 'UI 截图转代码/规范' },
      { name: 'understand_technical_diagram', desc: '技术图表解读' },
      { name: 'get_repo_structure', desc: 'GitHub 仓库目录结构' },
      { name: 'read_file', desc: 'GitHub 仓库文件读取' },
      { name: 'search_doc', desc: '仓库文档/Issue 搜索' },
    ]
  },
]

const sortedLogs = computed(() => {
  if (!props.process?.session_info?.recent_logs) return []
  return [...props.process.session_info.recent_logs].reverse()
})

const activeTodos = computed(() => {
  const todos = props.process?.session_info?.current_todos
  if (!todos) return []
  return todos.filter(t => t.status !== 'completed')
})

const todoStats = computed(() => {
  const todos = props.process?.session_info?.current_todos
  if (!todos || todos.length === 0) return null
  const done = todos.filter(t => t.status === 'completed').length
  const inProgress = todos.filter(t => t.status === 'in_progress').length
  const pending = todos.filter(t => t.status === 'pending').length
  const total = todos.length
  const percent = total > 0 ? Math.round((done / total) * 100) : 0
  return { done, inProgress, pending, total, percent }
})

const currentActivity = computed(() => {
  return props.process?.session_info?.current_activity ?? null
})

const activityState = computed(() => {
  return props.process?.session_info?.activity_state ?? null
})

const stateConfig = computed(() => {
  switch (activityState.value) {
    case 'thinking': return { icon: '●', label: 'THINKING', cls: 'thinking' }
    case 'executing': return { icon: '■', label: 'EXECUTING', cls: 'executing' }
    case 'responding': return { icon: '▶', label: 'RESPONDING', cls: 'responding' }
    case 'waiting': return { icon: '◇', label: 'WAITING INPUT', cls: 'waiting' }
    default: return null
  }
})

const subagents = computed(() => {
  return props.process?.session_info?.subagents ?? []
})

const activeSubagents = computed(() => {
  return subagents.value.filter(s => s.status === 'running')
})

const tokenUsage = computed(() => {
  return props.process?.session_info?.token_usage ?? null
})

const durationSec = computed(() => {
  return props.process?.session_info?.duration_seconds ?? null
})

function formatSessionDuration(seconds: number | null) {
  if (!seconds) return '--'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}h${String(m).padStart(2, '0')}m`
  if (m > 0) return `${m}m${String(s).padStart(2, '0')}s`
  return `${s}s`
}

function formatDuration(ms: number | null) {
  if (!ms) return '--'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${Math.floor(ms / 60000)}m${Math.floor((ms % 60000) / 1000)}s`
}

function formatTokens(n: number | null) {
  if (!n) return '--'
  if (n < 1000) return `${n}`
  if (n < 1000000) return `${(n / 1000).toFixed(1)}K`
  return `${(n / 1000000).toFixed(1)}M`
}

const needsUserInput = computed(() => {
  if (!props.process) return false
  if (props.process.status !== 'idle') return false
  const logs = props.process.session_info?.recent_logs
  if (!logs || logs.length === 0) return false
  const lastLog = logs[logs.length - 1]
  return lastLog.role === 'assistant'
})

const statusState = computed(() => {
  if (!props.process) return 'idle' as const
  if (props.process.status === 'running') return 'active' as const
  if (needsUserInput.value) return 'waiting' as const
  return 'idle' as const
})

function formatTime(isoStr: string | null) {
  if (!isoStr) return '--:--'
  const d = new Date(isoStr)
  return d.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function roleIcon(role: string) {
  switch (role) {
    case 'assistant': return 'AI'
    case 'user': return 'U'
    default: return role.charAt(0).toUpperCase()
  }
}

function contentTypeLabel(ct: string) {
  switch (ct) {
    case 'tool_use': return 'TOOL'
    case 'tool_result': return 'RESULT'
    case 'text': return 'TEXT'
    case 'thinking': return 'THINK'
    default: return ct.toUpperCase()
  }
}

function hasDetail(log: { detail?: string | null; summary: string }) {
  return !!log.detail && log.detail !== log.summary
}

function toggleExpand(idx: number) {
  if (expandedLogs.value.has(idx)) {
    expandedLogs.value.delete(idx)
  } else {
    expandedLogs.value.add(idx)
  }
}

function parseEditDetail(detail: string | null): { oldPart: string; newPart: string } | null {
  if (!detail) return null
  const oldIdx = detail.indexOf('--- old ---\n')
  const newIdx = detail.indexOf('+++ new +++\n')
  if (oldIdx === -1 || newIdx === -1) return null
  const oldPart = detail.slice(oldIdx + '--- old ---\n'.length, newIdx).trimEnd()
  const newPart = detail.slice(newIdx + '+++ new +++\n'.length).trimEnd()
  return { oldPart, newPart }
}

function isEditDiff(log: { detail?: string | null; tool_name?: string | null }) {
  return log.tool_name === 'Edit' && parseEditDetail(log.detail ?? null) !== null
}
</script>

<template>
  <div class="process-detail">
    <div class="empty-state" v-if="!process">
      <div class="empty-frame">
        <p class="empty-line">┌──────────────────┐</p>
        <p class="empty-line">│  SELECT A        │</p>
        <p class="empty-line">│  PROCESS TO      │</p>
        <p class="empty-line">│  VIEW DETAILS    │</p>
        <p class="empty-line">└──────────────────┘</p>
      </div>
    </div>

    <template v-else>
      <!-- Process Info Header -->
      <div class="detail-header">
        <div class="header-top">
          <PixelAvatar
            :seed="String(process.pid)"
            :size="48"
            :status="process.status"
          />
          <div class="header-info">
            <h2 class="project-name">
              {{ process.project_name || 'Unknown Project' }}
            </h2>
            <div class="header-meta">
              <span class="meta-item">
                <span class="meta-label">PID</span>
                <span class="meta-value">{{ process.pid }}</span>
              </span>
              <span class="meta-sep">│</span>
              <span class="meta-item">
                <span class="meta-label">START</span>
                <span class="meta-value">{{ formatTime(process.create_time) }}</span>
              </span>
              <span class="meta-sep">│</span>
              <span class="meta-item">
                <span class="meta-label">CPU</span>
                <span class="meta-value">{{ process.cpu_percent.toFixed(1) }}%</span>
              </span>
              <span class="meta-sep">│</span>
              <span class="meta-item">
                <span class="meta-label">MEM</span>
                <span class="meta-value">{{ process.memory_mb }}MB</span>
              </span>
              <span class="status-badge" :class="process.status">
                {{ process.status === 'running' ? '▶ ACTIVE' : '■ IDLE' }}
              </span>
              <span class="toolkit-toggle" @click.stop="toolkitExpanded = !toolkitExpanded" :class="{ active: toolkitExpanded }">
                <span class="toolkit-icon">⚙</span>
                <span class="toolkit-label">TOOLKIT</span>
                <span class="toolkit-count">{{ toolkitData.reduce((s, g) => s + g.items.length, 0) }}</span>
                <span class="toolkit-chevron" :class="{ expanded: toolkitExpanded }">▼</span>
              </span>
            </div>
          </div>
        </div>
        <div class="header-cwd" v-if="process.cwd">
          <span class="cwd-prefix">&gt;</span>
          <span class="cwd-value">{{ process.cwd }}</span>
        </div>
        <Transition name="expand">
          <div class="toolkit-dropdown" v-if="toolkitExpanded" @click.stop>
            <div class="toolkit-columns">
              <div v-for="group in toolkitData" :key="group.group" class="toolkit-group">
                <div class="toolkit-group-header">
                  <span class="group-icon">{{ group.icon }}</span>
                  <span class="group-name">{{ group.group }}</span>
                  <span class="group-count">{{ group.items.length }}</span>
                </div>
                <div class="toolkit-items">
                  <div v-for="item in group.items" :key="item.name" class="toolkit-item">
                    <span class="item-name">{{ item.name }}</span>
                    <span class="item-desc">{{ item.desc }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Status Bar -->
      <div class="status-section" :class="statusState" v-if="currentActivity || activeTodos.length || needsUserInput">
        <h3 class="section-title status-title" :class="statusState">// STATUS</h3>
        <!-- Waiting for user input alert -->
        <div class="user-input-alert" v-if="needsUserInput">
          <span class="alert-icon">⚠</span>
          <span class="alert-text">WAITING FOR USER INPUT</span>
        </div>
        <div class="activity-line" v-if="currentActivity">
          <span class="state-tag" v-if="stateConfig" :class="stateConfig.cls">
            <span class="state-icon">{{ stateConfig.icon }}</span>
            {{ stateConfig.label }}
          </span>
          <span class="activity-text" :class="{ 'with-state': stateConfig }">{{ currentActivity }}</span>
        </div>
        <div class="progress-section" v-if="todoStats">
          <div class="progress-bar">
            <div class="progress-fill done" :style="{ width: (todoStats.done / todoStats.total * 100) + '%' }"></div>
            <div class="progress-fill in-progress" :style="{ width: (todoStats.inProgress / todoStats.total * 100) + '%' }"></div>
          </div>
          <span class="progress-label">{{ todoStats.done }}/{{ todoStats.total }} {{ todoStats.percent }}%</span>
        </div>
        <div class="todo-list" v-if="activeTodos.length">
          <div
            v-for="(todo, idx) in activeTodos"
            :key="idx"
            class="todo-item"
            :class="todo.status"
          >
            <span class="todo-marker">{{ todo.status === 'in_progress' ? '▸' : '○' }}</span>
            <span class="todo-text">{{ todo.content }}</span>
          </div>
        </div>
      </div>

      <!-- Session Info -->
      <div class="session-bar" v-if="process.session_info" @click="sessionExpanded = !sessionExpanded">
        <div class="session-bar-row">
          <span class="session-kv">
            <span class="session-label">MSG</span>
            <span class="session-val">{{ process.session_info.message_count }}</span>
          </span>
          <span class="session-sep">│</span>
          <span class="session-kv">
            <span class="session-label">LAST</span>
            <span class="session-val">{{ formatTime(process.session_info.last_activity) }}</span>
          </span>
          <span class="session-sep">│</span>
          <span class="session-kv">
            <span class="session-label">VER</span>
            <span class="session-val">{{ process.session_info.version || '--' }}</span>
          </span>
          <span class="session-chevron" :class="{ expanded: sessionExpanded }">▼</span>
        </div>
        <Transition name="expand">
          <div class="session-detail" v-if="sessionExpanded">
            <div class="session-kv">
              <span class="session-label">SESSION</span>
              <span class="session-val">{{ process.session_info.session_id }}</span>
            </div>
            <div class="session-kv">
              <span class="session-label">PROJECT</span>
              <span class="session-val">{{ process.session_info.project_name }}</span>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Token Usage -->
      <div class="token-bar" v-if="tokenUsage">
        <div class="token-bar-row">
          <span class="token-kv">
            <span class="token-label">IN</span>
            <span class="token-val">{{ formatTokens(tokenUsage.input_tokens) }}</span>
          </span>
          <span class="token-sep">│</span>
          <span class="token-kv">
            <span class="token-label">OUT</span>
            <span class="token-val">{{ formatTokens(tokenUsage.output_tokens) }}</span>
          </span>
          <span class="token-sep">│</span>
          <span class="token-kv">
            <span class="token-label">CACHE</span>
            <span class="token-val">{{ formatTokens(tokenUsage.cache_read_tokens) }}</span>
          </span>
          <span class="token-sep">│</span>
          <span class="token-kv" v-if="tokenUsage.model">
            <span class="token-label">MODEL</span>
            <span class="token-val model-name">{{ tokenUsage.model }}</span>
          </span>
          <span class="token-sep" v-if="tokenUsage.model">│</span>
          <span class="token-kv">
            <span class="token-label">DURATION</span>
            <span class="token-val">{{ formatSessionDuration(durationSec) }}</span>
          </span>
        </div>
      </div>

      <!-- Subagents -->
      <div class="section" v-if="subagents.length">
        <h3 class="section-title clickable" @click="subagentsExpanded = !subagentsExpanded">
          <span class="section-chevron" :class="{ expanded: subagentsExpanded }">▼</span>
          // SUBAGENTS <span class="sa-count">{{ subagents.length }}</span>
        </h3>
        <Transition name="expand">
          <div class="sa-list" v-if="subagentsExpanded">
            <div
              v-for="sa in subagents"
              :key="sa.agent_id"
              class="sa-card"
              :class="sa.status"
            >
              <div class="sa-header">
                <span class="sa-dot" :class="sa.status"></span>
                <span class="sa-id">{{ sa.agent_id }}</span>
                <span class="sa-type-tag" v-if="sa.subagent_type">{{ sa.subagent_type.toUpperCase() }}</span>
                <span class="sa-status-tag" :class="sa.status">{{ sa.status.toUpperCase() }}</span>
              </div>
              <div class="sa-desc" v-if="sa.description">{{ sa.description }}</div>
              <div class="sa-activity" v-if="sa.current_activity">
                <span class="sa-activity-marker">▶</span>
                <span class="sa-activity-text">{{ sa.current_activity }}</span>
              </div>
              <div class="sa-meta">
                <span class="sa-meta-item" v-if="sa.model">
                  <span class="sa-meta-label">MODEL</span>
                  <span class="sa-meta-val">{{ sa.model }}</span>
                </span>
                <span class="sa-meta-item">
                  <span class="sa-meta-label">MSG</span>
                  <span class="sa-meta-val">{{ sa.message_count }}</span>
                </span>
                <span class="sa-meta-item">
                  <span class="sa-meta-label">TOKENS</span>
                  <span class="sa-meta-val">{{ formatTokens(sa.total_tokens) }}</span>
                </span>
                <span class="sa-meta-item">
                  <span class="sa-meta-label">TIME</span>
                  <span class="sa-meta-val">{{ formatDuration(sa.total_duration_ms) }}</span>
                </span>
                <span class="sa-meta-item" v-if="sa.total_tool_use_count != null">
                  <span class="sa-meta-label">TOOLS</span>
                  <span class="sa-meta-val">{{ sa.total_tool_use_count }}</span>
                </span>
              </div>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Logs -->
      <div class="section" v-if="sortedLogs.length">
        <h3 class="section-title">// RECENT LOGS</h3>
        <div class="log-list">
          <div
            v-for="(log, idx) in sortedLogs"
            :key="idx"
            class="log-card"
            :class="[log.role, { expanded: expandedLogs.has(idx) }]"
          >
            <div
              class="log-card-header"
              @click="hasDetail(log) && toggleExpand(idx)"
              :class="{ clickable: hasDetail(log) }"
            >
              <div class="log-left">
                <span class="role-badge" :class="log.role">{{ roleIcon(log.role) }}</span>
                <span class="log-time">{{ formatTime(log.timestamp) }}</span>
              </div>
              <div class="log-content">
                <div class="log-summary">
                  <span class="log-summary-text">{{ log.summary }}</span>
                  <span
                    v-if="hasDetail(log)"
                    class="expand-icon"
                    :class="{ expanded: expandedLogs.has(idx) }"
                  >▼</span>
                </div>
                <div class="log-tags">
                  <span class="tag type-tag" :class="log.content_type">{{ contentTypeLabel(log.content_type) }}</span>
                  <span class="tag tool-tag" v-if="log.tool_name">{{ log.tool_name }}</span>
                </div>
              </div>
            </div>
            <Transition name="expand">
              <div class="log-card-body" v-if="hasDetail(log) && expandedLogs.has(idx)">
                <template v-if="isEditDiff(log)">
                  <div class="diff-block">
                    <div class="diff-panel">
                      <div class="diff-label diff-label-old">--- OLD ---</div>
                      <pre class="diff-content diff-old">{{ parseEditDetail(log.detail)!.oldPart }}</pre>
                    </div>
                    <div class="diff-panel">
                      <div class="diff-label diff-label-new">+++ NEW +++</div>
                      <pre class="diff-content diff-new">{{ parseEditDetail(log.detail)!.newPart }}</pre>
                    </div>
                  </div>
                </template>
                <template v-else>
                  <pre class="detail-text">{{ log.detail }}</pre>
                </template>
              </div>
            </Transition>
          </div>
        </div>
      </div>

      <!-- No session info -->
      <div class="section" v-if="!process.session_info">
        <div class="no-logs">
          <p class="no-logs-frame">
          ┌──────────────────┐
          │  NO SESSION DATA  │
          │   PLEASE WAIT...  │
          └──────────────────┘
          </p>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.process-detail {
  flex: 1;
  overflow-y: auto;
  padding: 0;
  background: var(--bg-primary);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
}

.empty-frame {
  text-align: center;
}

.empty-line {
  font-family: var(--font-pixel);
  font-size: 8px;
  line-height: 2;
  color: var(--text-muted);
  white-space: pre;
}

.detail-header {
  padding: 16px 20px;
  border-bottom: 2px solid var(--border);
  background: var(--bg-secondary);
}

.header-top {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.header-info {
  flex: 1;
  min-width: 0;
}

.project-name {
  font-size: 14px;
  font-family: var(--font-body);
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
  text-shadow: 0 0 10px rgba(255, 170, 0, 0.2);
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 10px;
  color: var(--text-secondary);
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  gap: 4px;
  align-items: baseline;
}

.meta-label {
  color: var(--text-muted);
  font-family: var(--font-pixel);
  font-size: 7px;
  letter-spacing: 1px;
}

.meta-value {
  font-family: var(--font-pixel);
  font-size: 9px;
  color: var(--text-primary);
}

.meta-sep {
  color: var(--border);
  font-size: 12px;
}

.status-badge {
  font-family: var(--font-pixel);
  font-size: 8px;
  padding: 3px 10px;
  border: 2px solid;
  letter-spacing: 1px;
}

.status-badge.running {
  border-color: var(--success);
  color: var(--success);
  background: var(--success-bg);
  text-shadow: var(--glow-success);
}

.status-badge.idle {
  border-color: var(--warning);
  color: var(--warning);
  background: var(--warning-bg);
}

.header-cwd {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  background: var(--bg-primary);
  padding: 8px 12px;
  border: 2px solid var(--border);
}

.cwd-prefix {
  color: var(--accent);
  font-family: var(--font-pixel);
  font-size: 10px;
}

.cwd-value {
  color: var(--text-secondary);
  font-family: var(--font-body);
  font-size: 10px;
  word-break: break-all;
}

/* ===== Toolkit Toggle (in header-meta) ===== */
.toolkit-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-family: var(--font-pixel);
  font-size: 8px;
  padding: 3px 10px;
  border: 2px solid var(--border);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  letter-spacing: 1px;
  transition: all 0.1s step-end;
  user-select: none;
}

.toolkit-toggle:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-bg);
}

.toolkit-toggle.active {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-bg);
}

.toolkit-toggle .toolkit-icon {
  font-size: 11px;
  line-height: 1;
  color: var(--accent);
  animation: gear-spin 4s linear infinite;
}

.toolkit-toggle .toolkit-label {
  font-family: var(--font-pixel);
  font-size: 8px;
  letter-spacing: 1px;
  color: inherit;
}

.toolkit-toggle .toolkit-count {
  font-family: var(--font-pixel);
  font-size: 7px;
  background: var(--accent);
  color: var(--text-inverse);
  padding: 0px 5px;
  border: 1px solid var(--accent-light);
}

.toolkit-toggle .toolkit-chevron {
  font-family: var(--font-pixel);
  font-size: 7px;
  color: var(--text-muted);
  transition: transform 0.1s step-end;
}

.toolkit-toggle .toolkit-chevron.expanded {
  transform: rotate(180deg);
}

@keyframes gear-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ===== Toolkit Dropdown (inside detail-header) ===== */
.toolkit-dropdown {
  margin-top: 10px;
  background: var(--bg-primary);
  border: 2px solid var(--border);
  max-height: 450px;
  overflow-y: auto;
}

.toolkit-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
}

.toolkit-group {
  overflow: hidden;
}

.toolkit-group:first-child {
  border-right: 2px dashed var(--border);
}

.toolkit-group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px 6px;
  background: var(--bg-secondary);
  position: sticky;
  top: 0;
  z-index: 1;
  border-bottom: 2px solid var(--border);
}

.group-icon {
  font-size: 14px;
  line-height: 1;
}

.group-name {
  font-family: var(--font-pixel);
  font-size: 10px;
  color: var(--accent);
  letter-spacing: 2px;
}

.group-count {
  font-family: var(--font-pixel);
  font-size: 8px;
  color: var(--text-muted);
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  padding: 1px 6px;
  margin-left: auto;
}

.toolkit-items {
  padding: 6px 8px 10px;
}

.toolkit-item {
  display: flex;
  align-items: baseline;
  gap: 6px;
  padding: 5px 6px;
  border-bottom: 1px solid var(--border-light);
  transition: background 0.1s step-end;
}

.toolkit-item:hover {
  background: var(--bg-tertiary);
}

.toolkit-item:last-child {
  border-bottom: none;
}

.item-name {
  font-family: var(--font-pixel);
  font-size: 9px;
  color: var(--info);
  letter-spacing: 1px;
  white-space: nowrap;
  flex-shrink: 0;
  background: var(--info-bg);
  border: 1px solid var(--info);
  padding: 2px 6px;
  text-overflow: ellipsis;
  overflow: hidden;
}

.item-desc {
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
  word-break: break-word;
}

/* ===== Subagents ===== */
.sa-count {
  font-family: var(--font-pixel);
  font-size: 7px;
  color: var(--text-muted);
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  padding: 1px 6px;
  margin-left: 6px;
}

.sa-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sa-card {
  background: var(--bg-primary);
  border: 2px solid var(--border);
  border-left: 4px solid var(--text-muted);
  padding: 8px 10px;
}

.sa-card.running {
  border-left-color: var(--success);
}

.sa-card.completed {
  border-left-color: var(--accent);
}

.sa-card.error {
  border-left-color: var(--danger);
}

.sa-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.sa-dot {
  width: 8px;
  height: 8px;
  flex-shrink: 0;
  border: 2px solid;
}

.sa-dot.running {
  background: var(--success);
  border-color: var(--success);
  box-shadow: 0 0 6px var(--success);
  animation: sa-blink 1s step-end infinite;
}

.sa-dot.completed {
  background: var(--accent);
  border-color: var(--accent);
}

.sa-dot.error {
  background: var(--danger);
  border-color: var(--danger);
}

@keyframes sa-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.sa-id {
  font-family: var(--font-pixel);
  font-size: 9px;
  color: var(--text-primary);
  letter-spacing: 1px;
}

.sa-type-tag {
  font-family: var(--font-pixel);
  font-size: 7px;
  color: var(--info);
  background: var(--info-bg);
  border: 1px solid var(--info);
  padding: 1px 6px;
  letter-spacing: 1px;
}

.sa-status-tag {
  font-family: var(--font-pixel);
  font-size: 7px;
  padding: 1px 6px;
  border: 1px solid;
  letter-spacing: 1px;
  margin-left: auto;
}

.sa-status-tag.running {
  color: var(--success);
  border-color: var(--success);
  background: var(--success-bg);
}

.sa-status-tag.completed {
  color: var(--accent);
  border-color: var(--accent);
  background: var(--accent-bg);
}

.sa-status-tag.error {
  color: var(--danger);
  border-color: var(--danger);
  background: var(--danger-bg);
}

.sa-desc {
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
  margin-bottom: 4px;
  word-break: break-word;
}

.sa-activity {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-bottom: 4px;
}

.sa-activity-marker {
  color: var(--accent);
  font-family: var(--font-pixel);
  font-size: 9px;
  flex-shrink: 0;
  margin-top: 2px;
}

.sa-activity-text {
  font-family: var(--font-body);
  font-size: 11px;
  color: var(--text-secondary);
  word-break: break-word;
  line-height: 1.4;
}

.sa-meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.sa-meta-item {
  display: flex;
  gap: 3px;
  align-items: baseline;
}

.sa-meta-label {
  font-family: var(--font-pixel);
  font-size: 6px;
  color: var(--text-muted);
  letter-spacing: 1px;
}

.sa-meta-val {
  font-family: var(--font-pixel);
  font-size: 8px;
  color: var(--text-primary);
}

.status-section {
  padding: 10px 20px;
  border-bottom: 2px solid var(--border);
  background: var(--bg-secondary);
}

.status-section.active {
  border-left: 4px solid var(--success);
}

.status-section.idle {
  border-left: 4px solid var(--warning);
}

.status-section.waiting {
  border-left: 4px solid var(--info);
}

.status-title.active {
  color: var(--success);
}

.status-title.idle {
  color: var(--warning);
}

.status-title.waiting {
  color: var(--info);
  animation: blink 1.2s step-end infinite;
}

.user-input-alert {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  border: 2px solid var(--info);
  background: var(--info-bg);
  margin-bottom: 8px;
}

.alert-icon {
  font-size: 16px;
  color: var(--info);
}

.alert-text {
  font-family: var(--font-pixel);
  font-size: 10px;
  color: var(--info);
  letter-spacing: 2px;
  animation: blink 1.2s step-end infinite;
}

.activity-line {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 6px;
}

.activity-marker {
  color: var(--accent);
  font-family: var(--font-pixel);
  font-size: 10px;
  flex-shrink: 0;
  margin-top: 3px;
}

.activity-text {
  font-size: 12px;
  font-family: var(--font-body);
  color: var(--accent);
  word-break: break-word;
  line-height: 1.5;
}

.activity-text.with-state {
  color: var(--text-secondary);
}

.state-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-family: var(--font-pixel);
  font-size: 8px;
  padding: 3px 8px;
  border: 2px solid;
  letter-spacing: 1px;
  flex-shrink: 0;
}

.state-tag.thinking {
  border-color: var(--thinking-border);
  color: var(--thinking);
  background: var(--thinking-bg);
  animation: blink 1.2s step-end infinite;
}

.state-tag.executing {
  border-color: var(--success);
  color: var(--success);
  background: var(--success-bg);
}

.state-tag.responding {
  border-color: var(--info);
  color: var(--info);
  background: var(--info-bg);
}

.state-tag.waiting {
  border-color: var(--info);
  color: var(--info);
  background: var(--info-bg);
  animation: blink 1.2s step-end infinite;
}

.state-icon {
  font-size: 8px;
}

.progress-section {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.progress-bar {
  flex: 1;
  height: 10px;
  display: flex;
  background: var(--bg-tertiary);
  border: 2px solid var(--border);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  transition: width 0.2s step-end;
}

.progress-fill.done {
  background: var(--success);
}

.progress-fill.in-progress {
  background: var(--warning);
  animation: blink 1.2s step-end infinite;
}

.progress-label {
  font-family: var(--font-pixel);
  font-size: 8px;
  color: var(--text-muted);
  letter-spacing: 1px;
  white-space: nowrap;
}

.todo-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.todo-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 2px 0;
}

.todo-marker {
  font-family: var(--font-pixel);
  font-size: 9px;
  flex-shrink: 0;
  margin-top: 3px;
}

.todo-item.in_progress .todo-marker {
  color: var(--accent);
}

.todo-item.pending .todo-marker {
  color: var(--text-muted);
}

.todo-text {
  font-size: 11px;
  font-family: var(--font-body);
  color: var(--text-secondary);
  word-break: break-word;
  line-height: 1.5;
}

.todo-item.in_progress .todo-text {
  color: var(--text-primary);
}

.section {
  padding: 14px 20px;
  border-bottom: 2px solid var(--border);
}

.section-title {
  font-size: 8px;
  font-family: var(--font-pixel);
  color: var(--accent);
  letter-spacing: 2px;
  margin-bottom: 12px;
}

.section-title.clickable {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  user-select: none;
}

.section-title.clickable:hover {
  color: var(--text-primary);
}

.section-chevron {
  font-size: 8px;
  transition: transform 0.1s step-end;
}

.section-chevron:not(.expanded) {
  transform: rotate(-90deg);
}

.session-bar {
  padding: 8px 20px;
  border-bottom: 2px solid var(--border);
  cursor: pointer;
  transition: background 0.1s step-end;
}

.session-bar:hover {
  background: var(--bg-tertiary);
}

.session-bar-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.session-kv {
  display: flex;
  gap: 4px;
  align-items: baseline;
}

.session-label {
  font-family: var(--font-pixel);
  font-size: 7px;
  color: var(--text-muted);
  letter-spacing: 1px;
}

.session-val {
  font-size: 10px;
  font-family: var(--font-pixel);
  color: var(--text-primary);
}

.session-sep {
  color: var(--border);
  font-size: 12px;
}

.session-chevron {
  margin-left: auto;
  flex-shrink: 0;
  color: var(--text-muted);
  font-size: 10px;
  transition: transform 0.1s step-end;
  font-family: var(--font-pixel);
}

.session-chevron.expanded {
  transform: rotate(180deg);
}

.session-detail {
  display: flex;
  gap: 20px;
  padding-top: 8px;
  margin-top: 8px;
  border-top: 1px dashed var(--border);
}

.token-bar {
  padding: 8px 20px;
  border-bottom: 2px solid var(--border);
  cursor: default;
}

.token-bar-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.token-kv {
  display: flex;
  gap: 4px;
  align-items: baseline;
}

.token-label {
  font-family: var(--font-pixel);
  font-size: 7px;
  color: var(--text-muted);
  letter-spacing: 1px;
}

.token-val {
  font-size: 10px;
  font-family: var(--font-pixel);
  color: var(--accent);
}

.token-sep {
  color: var(--border);
  font-size: 12px;
}

.model-name {
  color: var(--text-secondary);
  font-size: 8px;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.log-card {
  background: var(--bg-primary);
  border: 2px solid var(--border);
  border-left: 4px solid transparent;
  overflow: hidden;
}

.log-card.assistant {
  border-left-color: var(--accent);
}

.log-card.user {
  border-left-color: var(--info);
}

.log-card.expanded {
  border-color: var(--accent);
}

.log-card-header {
  display: flex;
  gap: 10px;
  padding: 8px 10px;
}

.log-card-header.clickable {
  cursor: pointer;
}

.log-card-header.clickable:hover {
  background: var(--bg-secondary);
}

.log-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  min-width: 44px;
}

.role-badge {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 8px;
  font-family: var(--font-pixel);
  border: 2px solid;
}

.role-badge.assistant {
  background: rgba(255, 170, 0, 0.1);
  color: var(--accent);
  border-color: var(--accent);
}

.role-badge.user {
  background: rgba(0, 212, 255, 0.1);
  color: var(--info);
  border-color: var(--info);
}

.log-time {
  font-size: 7px;
  color: var(--text-muted);
  font-family: var(--font-pixel);
}

.log-content {
  flex: 1;
  min-width: 0;
}

.log-summary {
  font-size: 12px;
  font-family: var(--font-body);
  line-height: 1.4;
  word-break: break-word;
  color: var(--text-primary);
  display: flex;
  align-items: flex-start;
  gap: 6px;
}

.log-summary-text {
  flex: 1;
}

.expand-icon {
  flex-shrink: 0;
  color: var(--text-muted);
  transition: transform 0.1s step-end;
  font-size: 8px;
  margin-top: 3px;
  font-family: var(--font-pixel);
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.log-tags {
  display: flex;
  gap: 6px;
  margin-top: 4px;
}

.tag {
  font-size: 7px;
  font-family: var(--font-pixel);
  padding: 2px 6px;
  border: 1px solid;
  letter-spacing: 1px;
}

.type-tag {
  border-color: var(--border);
  color: var(--text-secondary);
  background: var(--bg-tertiary);
}

.type-tag.thinking {
  border-color: var(--thinking-border);
  color: var(--thinking);
  background: var(--thinking-bg);
  text-shadow: var(--thinking-glow);
}

.type-tag.tool_use {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-bg);
}

.type-tag.tool_result {
  border-color: var(--info);
  color: var(--info);
  background: var(--info-bg);
}

.tool-tag {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-bg);
}

.log-card-body {
  border-top: 1px dashed var(--border);
  background: var(--bg-inset);
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.15s step-end;
  max-height: 500px;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}

.detail-text {
  padding: 10px 14px;
  margin: 0;
  font-size: 11px;
  line-height: 1.6;
  font-family: var(--font-body);
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 400px;
  overflow-y: auto;
}

.diff-block {
  display: flex;
  gap: 0;
}

.diff-panel {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.diff-panel + .diff-panel {
  border-left: 2px solid var(--border);
}

.diff-label {
  font-family: var(--font-pixel);
  font-size: 7px;
  letter-spacing: 1px;
  padding: 4px 10px;
  border-bottom: 1px dashed var(--border);
}

.diff-label-old {
  color: var(--danger);
  background: var(--danger-bg);
}

.diff-label-new {
  color: var(--success);
  background: var(--success-bg);
}

.diff-content {
  padding: 8px 10px;
  margin: 0;
  font-size: 11px;
  line-height: 1.6;
  font-family: var(--font-body);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 300px;
  overflow-y: auto;
}

.diff-old {
  color: var(--danger);
  background: var(--danger-bg);
}

.diff-new {
  color: var(--success);
  background: var(--success-bg);
}

.no-logs {
  text-align: center;
  padding: 40px 16px;
}

.no-logs-frame {
  font-family: var(--font-pixel);
  font-size: 8px;
  line-height: 2;
  color: var(--text-muted);
  white-space: pre;
}
</style>
