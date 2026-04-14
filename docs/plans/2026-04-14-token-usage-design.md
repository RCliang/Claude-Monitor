# Token Usage Tracking Design

## Goal

Add token consumption visibility to the Claude Monitor dashboard. Display aggregated token statistics (input, output, cache) for both the global dashboard and individual process details. No USD cost estimation — pure token counts, since the user is on a GLM Coding Plan (flat-rate subscription).

## Data Source

Every `type: "assistant"` JSONL entry contains a `message.usage` object:

```json
{
  "input_tokens": 94517,
  "output_tokens": 130,
  "cache_read_input_tokens": 512,
  "server_tool_use": { "web_search_requests": 0 }
}
```

Many entries have `0, 0` usage (placeholder for thinking/tool_result intermediates). Only entries with `input_tokens > 0` carry real data. Some entries appear duplicated (same message ID) — deduplicate by message ID.

Subagents already have `total_tokens` from `toolUseResult.totalTokens` in the parent session.

---

## Changes

### 1. Backend: `backend/log_reader.py`

**Add `TokenUsage` dataclass:**

```python
@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    model: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "model": self.model,
        }
```

**Modify `SessionInfo`:**

- Add field: `token_usage: TokenUsage = field(default_factory=TokenUsage)`
- Add field: `duration_seconds: Optional[int] = None`

**Modify `_parse_session_jsonl`:**

- Track `seen_msg_ids: set[str]` for deduplication
- For each `entry.type == "assistant"` with `message.usage.input_tokens > 0`:
  - Get message ID from `message.get("id")`
  - Skip if already seen
  - Accumulate `input_tokens`, `output_tokens`, `cache_read_input_tokens`
  - Capture `message.get("model")` on first non-zero usage entry
- After parsing: calculate `duration_seconds` from `start_time` and `last_activity` timestamps
- Assign accumulated `TokenUsage` to `session_info.token_usage`

### 2. Backend: `backend/main.py` — No changes needed

`SessionInfo.to_dict()` serializes `token_usage` automatically. Existing enrichment flow already passes full session data.

### 3. Frontend: `frontend/src/composables/useWebSocket.ts`

Add TypeScript interface:

```typescript
export interface TokenUsage {
  input_tokens: number
  output_tokens: number
  cache_read_tokens: number
  model: string | null
}
```

Add fields to `SessionInfo`:

```typescript
token_usage: TokenUsage
duration_seconds: number | null
```

### 4. Frontend: `frontend/src/components/Dashboard.vue`

Add a second row of 4 stat cards below the existing process count row:

```
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ INPUT    │ │ OUTPUT   │ │ CACHE    │ │ DURATION │
│ 1.2M     │ │ 89.3K    │ │ 5.1M     │ │ 02:34:17 │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

- Aggregate all `processes[i].session_info.token_usage` for totals
- `DURATION` = sum of all `session_info.duration_seconds`
- Format: K for thousands, M for millions
- Style: same pixel font, border, background as existing stat cards

### 5. Frontend: `frontend/src/components/ProcessDetail.vue`

Add a TOKEN USAGE bar between the session info bar and the subagents section:

```
// TOKEN USAGE ──────────────────────────────────────
│ IN: 234,567 │ OUT: 12,345 │ CACHE: 567,890 │
│ Messages: 48 │ Model: glm-5 │ Duration: 15m  │
└────────────────────────────────────────────────────┘
```

- Data from `process.session_info.token_usage`
- Compact horizontal layout, pixel font
- `Model` field shows which model the session is using

---

## Files to Modify

| File | Change |
|------|--------|
| `backend/log_reader.py` | Add `TokenUsage`, modify `SessionInfo`, accumulate in `_parse_session_jsonl` |
| `frontend/src/composables/useWebSocket.ts` | Add `TokenUsage` interface, update `SessionInfo` |
| `frontend/src/components/Dashboard.vue` | Add token summary cards row |
| `frontend/src/components/ProcessDetail.vue` | Add TOKEN USAGE bar |

## Verification

1. Run `python run.py` to start the app
2. Open dashboard — verify INPUT/OUTPUT/CACHE/DURATION cards appear with non-zero values
3. Click a process — verify TOKEN USAGE bar shows correct per-session stats
4. Cross-check: manually sum token values from a JSONL file and compare with dashboard display
5. Verify deduplication works (no double-counting)
