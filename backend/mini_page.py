"""Self-contained mini HTML page for the desktop floating window."""


def get_mini_html() -> str:
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }

:root {
  --bg-primary: rgba(10, 10, 26, 0.95);
  --bg-secondary: #111128;
  --bg-tertiary: #1a1a3e;
  --border: #2a2a5a;
  --border-light: #1e1e44;
  --text-primary: #e0e0ff;
  --text-secondary: #8888bb;
  --text-muted: #555580;
  --accent: #ffaa00;
  --success: #00ff41;
  --warning: #ffcc00;
  --danger: #ff4444;
  --info: #00d4ff;
  --thinking: #A78BFA;
  --font-pixel: 'Press Start 2P', monospace;
}

body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font-pixel);
  overflow: hidden;
  -webkit-font-smoothing: none;
  user-select: none;
}

/* Title bar — draggable */
.titlebar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: var(--bg-secondary);
  border-bottom: 2px solid var(--accent);
  cursor: grab;
}
.titlebar:active { cursor: grabbing; }

.logo { color: var(--accent); font-size: 8px; letter-spacing: 1px; }
.logo-bracket { color: var(--text-muted); }

.conn { font-size: 6px; }
.conn.on { color: var(--success); }
.conn.off { color: var(--danger); }

.summary {
  font-size: 7px; color: var(--text-secondary);
  flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.sum-run { color: var(--success); }
.sum-wait { color: var(--info); }

.close-btn {
  background: none; border: none; color: var(--text-muted);
  cursor: pointer; font-family: var(--font-pixel); font-size: 9px;
  padding: 0 4px;
}
.close-btn:hover { color: var(--danger); }

/* Process list */
.body { max-height: 200px; overflow-y: auto; }

.row {
  display: flex; align-items: center; gap: 6px;
  padding: 5px 8px; cursor: pointer;
  border-bottom: 1px solid var(--border-light);
  font-size: 7px;
  line-height: 1.8;
  transition: background 0.1s step-end;
}
.row:hover { background: var(--bg-tertiary); }
.row:last-child { border-bottom: none; }

.dot {
  width: 8px; height: 8px; flex-shrink: 0;
}
.dot.running, .dot.executing { background: var(--success); box-shadow: 0 0 6px rgba(0,255,65,0.4); }
.dot.thinking { background: var(--thinking); box-shadow: 0 0 6px rgba(167,139,250,0.4); animation: blink 1.2s step-end infinite; }
.dot.idle { background: var(--warning); }
.dot.waiting { background: var(--info); box-shadow: 0 0 6px rgba(0,212,255,0.4); animation: input-blink 1s step-end infinite; }

.name { color: var(--text-primary); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.status { font-size: 6px; letter-spacing: 1px; flex-shrink: 0; }
.status.running, .status.executing { color: var(--success); }
.status.thinking { color: var(--thinking); }
.status.idle { color: var(--warning); }
.status.waiting { color: var(--info); }
.sa { font-size: 6px; color: var(--text-muted); flex-shrink: 0; }

/* Token bar */
.token-bar {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 5px 8px; background: var(--bg-tertiary);
  border-top: 2px solid var(--border);
}
.tok { font-size: 6px; color: var(--accent); letter-spacing: 1px; }
.tok-sep { font-size: 8px; color: var(--border); }

/* Empty state */
.empty { padding: 20px 8px; text-align: center; font-size: 7px; color: var(--text-muted); line-height: 2; }

@keyframes blink { 50% { opacity: 0.3; } }
@keyframes input-blink { 0%,100% { opacity: 1; } 50% { opacity: 0.2; } }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); }
</style>
</head>
<body>

<div class="titlebar">
  <span class="logo"><span class="logo-bracket">[</span>CM<span class="logo-bracket">]</span></span>
  <span class="conn off" id="conn-dot">◇</span>
  <span class="summary" id="summary">CONNECTING...</span>
  <button class="close-btn" id="close-btn">[X]</button>
</div>

<div class="body" id="process-list">
  <div class="empty">
    ┌──────────┐<br>
    │ LOADING  │<br>
    └──────────┘
  </div>
</div>

<div class="token-bar" id="token-bar"></div>

<script>
const connDot = document.getElementById('conn-dot');
const summary = document.getElementById('summary');
const processList = document.getElementById('process-list');
const tokenBar = document.getElementById('token-bar');
const closeBtn = document.getElementById('close-btn');

closeBtn.addEventListener('click', () => {
  if (window.pywebview) pywebview.api.close_window();
  else window.close();
});

// Sound notification
let notifyAudio = null;
function playNotify() {
  if (!notifyAudio) {
    notifyAudio = new Audio('/notify.wav');
  }
  notifyAudio.currentTime = 0;
  notifyAudio.play().catch(() => {});
}

function formatTokens(n) {
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
  return String(n);
}

function getState(proc) {
  const st = proc.session_info?.activity_state;
  if (proc.status === 'running') {
    if (st === 'thinking') return { label: 'THINK', cls: 'thinking' };
    if (st === 'executing') return { label: 'EXEC', cls: 'executing' };
    return { label: 'RUN', cls: 'running' };
  }
  if (st === 'waiting') return { label: 'WAIT', cls: 'waiting' };
  return { label: 'IDLE', cls: 'idle' };
}

function render(processes) {
  let runCount = 0, waitCount = 0;
  let totalIn = 0, totalOut = 0;
  let html = '';

  for (const p of processes) {
    const s = getState(p);
    if (s.cls === 'running' || s.cls === 'executing') runCount++;
    if (s.cls === 'waiting') waitCount++;

    const si = p.session_info || {};
    totalIn += si.token_usage?.input_tokens || 0;
    totalOut += si.token_usage?.output_tokens || 0;

    const saList = si.subagents || [];
    const runSA = saList.filter(x => x.status === 'running').length;
    const totSA = saList.length;
    const saHtml = totSA > 0 ? '<span class="sa">SA:' + runSA + '/' + totSA + '</span>' : '';

    html += '<div class="row" onclick="openDetail(' + p.pid + ')">'
      + '<span class="dot ' + s.cls + '"></span>'
      + '<span class="name">' + (p.project_name || '???') + '</span>'
      + '<span class="status ' + s.cls + '">' + s.label + '</span>'
      + saHtml
      + '</div>';
  }

  if (processes.length === 0) {
    html = '<div class="empty">┌──────────┐<br>│ NO PROC  │<br>└──────────┘</div>';
  }

  processList.innerHTML = html;

  // Summary
  let sumText = processes.length + ' PROC';
  if (runCount) sumText += ' <span class="sum-run">| ' + runCount + ' RUN</span>';
  if (waitCount) sumText += ' <span class="sum-wait">| ' + waitCount + ' WAIT</span>';
  summary.innerHTML = sumText;

  // Token bar
  if (totalIn > 0 || totalOut > 0) {
    tokenBar.innerHTML = '<span class="tok">IN:' + formatTokens(totalIn) + '</span>'
      + '<span class="tok-sep">|</span>'
      + '<span class="tok">OUT:' + formatTokens(totalOut) + '</span>';
  } else {
    tokenBar.innerHTML = '';
  }
}

function openDetail(pid) {
  // Open full dashboard in browser via pywebview bridge
  if (window.pywebview && pywebview.api && pywebview.api.open_detail) {
    pywebview.api.open_detail(pid);
  } else {
    window.open('http://localhost:8765/', '_blank');
  }
}

// WebSocket
let ws;
function connect() {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(proto + '//' + location.host + '/ws');

  ws.onopen = () => {
    connDot.className = 'conn on';
    connDot.textContent = '◆';
  };

  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === 'initial' || msg.type === 'processes') {
      render(msg.data.processes || []);
    }
    if (msg.type === 'notification' && msg.data.type === 'user_input_required') {
      playNotify();
    }
  };

  ws.onclose = () => {
    connDot.className = 'conn off';
    connDot.textContent = '◇';
    setTimeout(connect, 3000);
  };

  ws.onerror = () => ws.close();
}

connect();
</script>
</body>
</html>'''
