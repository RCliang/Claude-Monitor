import { ref, onMounted, onUnmounted } from 'vue'

export interface ProcessInfo {
  pid: number
  name: string
  cmdline: string[]
  cwd: string | null
  create_time: string
  cpu_percent: number
  memory_mb: number
  status: 'running' | 'idle' | 'exited'
  session_id: string | null
  project_name: string | null
  last_seen: string
  session_info?: SessionInfo
}

export interface TokenUsage {
  input_tokens: number
  output_tokens: number
  cache_read_tokens: number
  model: string | null
}

export interface SessionInfo {
  session_id: string
  project_dir: string
  project_name: string
  cwd: string | null
  version: string | null
  start_time: string | null
  last_activity: string | null
  message_count: number
  recent_logs: LogEntry[]
  current_todos: TodoItem[]
  current_activity: string | null
  subagents: SubagentInfo[]
  token_usage: TokenUsage
  duration_seconds: number | null
  activity_state: string | null
}

export interface SubagentInfo {
  agent_id: string
  slug: string | null
  subagent_type: string | null
  description: string | null
  status: string
  message_count: number
  total_tokens: number | null
  total_duration_ms: number | null
  total_tool_use_count: number | null
  model: string | null
  last_activity: string | null
  current_activity: string | null
}

export interface LogEntry {
  timestamp: string
  role: string
  content_type: string
  summary: string
  tool_name: string | null
  detail: string | null
}

export interface TodoItem {
  content: string
  status: string
  activeForm: string
}

export interface Notification {
  type: string
  pid?: number
  project?: string
  cwd?: string
}

const processes = ref<ProcessInfo[]>([])
const notifications = ref<Notification[]>([])
const connected = ref(false)
let ws: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null

function connect() {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const url = `${protocol}//${location.host}/ws`

  ws = new WebSocket(url)

  ws.onopen = () => {
    connected.value = true
  }

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data)

    switch (msg.type) {
      case 'initial':
      case 'processes':
        processes.value = msg.data.processes
        break

      case 'notification':
        notifications.value.push(msg.data)
        // Keep only last 50 notifications
        if (notifications.value.length > 50) {
          notifications.value = notifications.value.slice(-50)
        }
        break
    }
  }

  ws.onclose = () => {
    connected.value = false
    // Reconnect after 3 seconds
    reconnectTimer = setTimeout(connect, 3000)
  }

  ws.onerror = () => {
    ws?.close()
  }
}

function disconnect() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
  }
  ws?.close()
  ws = null
}

export function useWebSocket() {
  onMounted(connect)
  onUnmounted(disconnect)

  function requestSessionLogs(cwd: string) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'get_session_logs', cwd }))
    }
  }

  return {
    processes,
    notifications,
    connected,
    requestSessionLogs,
  }
}
