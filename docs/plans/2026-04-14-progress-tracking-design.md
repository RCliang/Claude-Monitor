# Progress Tracking & Activity State Design

## Goal

Solve two monitoring pain points:
1. **Progress visibility** — TODO-based progress bar showing how far along Claude Code is
2. **Activity state clarity** — Distinguish between "thinking", "executing tools", and "responding" at a glance

No changes to subagent nesting — YAGNI (no nested subagents exist in current data).

---

## Data Source

### TODO Progress
Already available in `SessionInfo.current_todos`. Each item has `status: "completed" | "in_progress" | "pending"`. Frontend calculates `done / total`.

### Activity State
Every assistant JSONL entry has `message.content[]` with typed blocks:
- `type: "thinking"` — Claude is reasoning
- `type: "tool_use"` — Claude is calling a tool (with `name` and `input`)
- `type: "text"` — Claude is writing a response to the user

The **last** content block's type determines the current state.

---

## Changes

### 1. Backend: `backend/log_reader.py`

**Modify `_parse_session_jsonl` — improve `current_activity` derivation:**

Currently derives activity from last log entry's `summary`. Change to analyze the actual content blocks:

```python
# In the log-building loop, track the last content type per assistant message
# After loop, when deriving current_activity:
for log in reversed(logs):
    if log.role == "assistant" and log.content_type != "tool_result":
        if log.content_type == "thinking":
            session_info.current_activity = f"THINKING: {_truncate(log.summary, 60)}"
        elif log.content_type == "tool_use":
            session_info.current_activity = f"EXECUTING: {log.summary}"
        else:
            session_info.current_activity = f"RESPONDING: {_truncate(log.summary, 60)}"
        break
```

**Add `activity_state` field to `SessionInfo`:**

```python
activity_state: Optional[str] = None  # "thinking", "executing", "responding", "waiting", "idle"
```

Derivation logic:
- Last assistant log is `thinking` → `"thinking"`
- Last assistant log is `tool_use` → `"executing"`
- Last assistant log is `text` and process is idle → `"waiting"`
- Process idle with no recent activity → `"idle"`

### 2. Frontend: `frontend/src/composables/useWebSocket.ts`

Add field to `SessionInfo`:
```typescript
activity_state: string | null  // "thinking" | "executing" | "responding" | "waiting" | "idle"
```

### 3. Frontend: `frontend/src/components/ProcessDetail.vue`

**TODO Progress Bar:**

Add above the existing TODO list section:

```
// PROGRESS ━━━━━━━━━━━░░░░ 3/6  50%
```

- Completed segments: green (`--success`), solid fill
- In-progress segment: yellow (`--warning`), blinking
- Pending segments: dark (`--bg-tertiary`)
- Pixel font for numbers
- Only shown when `current_todos.length > 0`

**Activity State Label:**

Replace plain text `current_activity` with a tagged state display:

```
● THINKING...                    (yellow blink)
■ EXECUTING: Edit src/main.ts    (green)
▶ RESPONDING                     (blue)
◇ WAITING INPUT                  (blue blink)
```

Each state has its own color and indicator icon (Unicode: ● ■ ▶ ◇).

### 4. Frontend: `frontend/src/components/ProcessList.vue`

**Replace status text:**

Current: `ACTIVE` / `IDLE` badges.
New: Show specific activity state based on `session_info.activity_state`:

- `THINKING` — yellow text, yellow border
- `EXECUTING` — green text, green border (existing running indicator stays)
- `IDLE` — yellow text, yellow border (unchanged)
- `WAITING` — blue text, blue border (existing input indicator stays)

Only change the label text and color. The blinking square indicators remain as-is.

---

## Files to Modify

| File | Change |
|------|--------|
| `backend/log_reader.py` | Add `activity_state` to `SessionInfo`, improve `current_activity` derivation |
| `frontend/src/composables/useWebSocket.ts` | Add `activity_state` to `SessionInfo` interface |
| `frontend/src/components/ProcessDetail.vue` | Add TODO progress bar, tag activity state display |
| `frontend/src/components/ProcessList.vue` | Replace ACTIVE/IDLE labels with specific state text |

## Verification

1. Run `python run.py` to start the app
2. Open Claude Code and start a task that creates TODOs
3. Verify progress bar appears and updates as tasks complete
4. Watch status labels change: THINKING → EXECUTING → THINKING → RESPONDING
5. Verify left sidebar shows the same state labels with correct colors
6. Verify WAITING state appears when Claude waits for input
