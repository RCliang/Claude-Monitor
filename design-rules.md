# Claude Monitor - Design Rules

Design specification: a retro NES/CRT pixel-art aesthetic for a developer-oriented process monitoring tool. Dark-mode with neon accents, pixel fonts, and CRT visual effects.

---

## 1. Aesthetic Direction

**Mood**: Retro-gaming terminal — a dark-mode dashboard inspired by 8-bit/16-bit era RPG menus and CRT monitors. Pixel-perfect edges, neon glow effects, scanline overlays, and ASCII-art decorative elements create a nostalgic yet functional monitoring experience.

**Keywords**: Pixel art, NES palette, CRT scanlines, dark theme, neon glow, retro terminal, 8-bit, monospace, ASCII art.

---

## 2. Color System

### 2.1 Dark Theme (Primary)

| Token                | Value                          | Usage                           |
|----------------------|--------------------------------|----------------------------------|
| `--bg-primary`       | `#0a0a1a`                      | Page background, card surfaces   |
| `--bg-secondary`     | `#111128`                      | Header, sidebar, panel headers   |
| `--bg-tertiary`      | `#1a1a3e`                      | Hover states, nested panels      |
| `--bg-inset`         | `#0d0d24`                      | Code blocks, expanded detail     |
| `--border`           | `#2a2a5a`                      | All borders, dividers            |
| `--border-light`     | `#1e1e44`                      | Subtle separators                |

### 2.2 Text

| Token                | Value     | Usage                         |
|----------------------|-----------|-------------------------------|
| `--text-primary`     | `#e0e0ff` | Headings, primary content     |
| `--text-secondary`   | `#8888bb` | Descriptions, metadata        |
| `--text-muted`       | `#555580` | Hints, timestamps, tertiary   |
| `--text-inverse`     | `#0a0a1a` | Text on accent backgrounds    |

### 2.3 Accent & Status

| Token                | Value     | Usage                         |
|----------------------|-----------|-------------------------------|
| `--accent`           | `#ffaa00` | Brand accent, selection       |
| `--accent-light`     | `#ffcc44` | Hover state, secondary accent |
| `--accent-bg`        | `#1a1500` | Accent tinted background      |
| `--success`          | `#00ff41` | Running status, positive      |
| `--success-bg`       | `#001a00` | Success tinted background     |
| `--warning`          | `#ffcc00` | Idle status, caution          |
| `--warning-bg`       | `#1a1500` | Warning tinted background     |
| `--danger`           | `#ff4444` | Exited, errors                |
| `--danger-bg`        | `#1a0000` | Danger tinted background      |
| `--info`             | `#00d4ff` | Links, informational          |
| `--info-bg`          | `#001a22` | Info tinted background        |

### 2.4 Glow Effects

| Token                | Value                                  | Usage                    |
|----------------------|----------------------------------------|--------------------------|
| `--glow-accent`      | `0 0 8px rgba(255, 170, 0, 0.4)`      | Accent neon glow         |
| `--glow-success`     | `0 0 8px rgba(0, 255, 65, 0.4)`       | Success neon glow        |
| `--glow-danger`      | `0 0 8px rgba(255, 68, 68, 0.4)`      | Danger neon glow         |
| `--glow-info`        | `0 0 8px rgba(0, 212, 255, 0.4)`      | Info neon glow           |

### 2.5 Color Usage Rules

- **Backgrounds**: Use deep navy (`#0a0a1a`) as the dominant surface. `#111128` for grouped sections. Never use white or light backgrounds.
- **Borders**: Always `#2a2a5a`, 2px solid. No border-radius — all elements use sharp 90-degree corners.
- **Status colors**: Applied via `text-shadow` neon glow effects paired with dark tinted backgrounds. Status colors are used at full opacity for text and borders, never as large-area fills.
- **Accent (electric amber `#ffaa00`)**: Used sparingly — selection indicator, logo, primary action highlight, section markers. Glow via `text-shadow`.
- **Neon principle**: Key interactive and status elements should have a subtle neon glow via `text-shadow` or `box-shadow` using the same hue at reduced opacity.

---

## 3. Typography

### 3.1 Font Stack

```css
--font-pixel: 'Press Start 2P', monospace;
--font-body: 'Silkscreen', monospace;
--font-mono: 'Press Start 2P', monospace;
```

- Use `--font-pixel` for headings, badges, labels, PIDs, tags, section titles, and all uppercase display text.
- Use `--font-body` for body content, descriptions, log summaries, and readable paragraphs.
- Use `--font-mono` for technical values (PIDs, paths, session IDs, code-related values).

### 3.2 Scale

| Level           | Size   | Weight | Line-height | Font         | Usage                           |
|-----------------|--------|--------|-------------|--------------|---------------------------------|
| Logo Title      | 12px   | 400    | 1           | `--font-pixel` | App title with glow            |
| Logo Mark       | 10px   | 400    | 1           | `--font-pixel` | Logo icon [CM]                 |
| Section Title   | 8px    | 400    | 1.5         | `--font-pixel` | Section headings, `// RECENT LOGS` |
| Label           | 7-9px  | 400    | 1           | `--font-pixel` | Metadata labels, badges, keys  |
| Value           | 9-10px | 400    | 1           | `--font-pixel` | Metadata values, PIDs, counts  |
| Tag             | 7px    | 400    | 1           | `--font-pixel` | Content type tags, tool tags   |
| Body            | 12px   | 400    | 1.4         | `--font-body`  | Log summaries, descriptions    |
| Detail          | 11px   | 400    | 1.6         | `--font-body`  | Expanded log detail text       |
| Project Name    | 14px   | 700    | 1.3         | `--font-body`  | Card titles, project names     |

### 3.3 Rules

- **No border-radius**: All elements use sharp rectangular edges. Zero `border-radius` everywhere.
- **No font-weight variation in pixel font**: `Press Start 2P` only has one weight (400). Use `Silkscreen` with `700` for bold body text.
- **Letter-spacing**: `1-2px` for all `--font-pixel` uppercase labels and section titles.
- **Uppercase**: All labels, badges, status text, section titles use `UPPERCASE` text (via `text-transform` or manual).
- **Anti-aliasing disabled**: Set `-webkit-font-smoothing: none` and `-moz-osx-font-smoothing: unset` to preserve pixel-perfect rendering.
- **text-transform: uppercase** on all labels and section titles.

---

## 4. Layout

### 4.1 Grid System

```
+==================================================================+
|  Header (full width, h=56px, border-bottom: 3px solid accent)    |
+==================================================================+
|  Dashboard Stats Bar (full width, h=32px)                        |
+================+=================================================+
|  Process List  |  Process Detail Panel                           |
|  w=300px       |  flex: 1                                        |
|  fixed sidebar |  scrollable                                     |
|                |                                                 |
+================+=================================================+
```

### 4.2 Spacing Scale

| Token   | Value | Usage                               |
|---------|-------|--------------------------------------|
| `--sp-1` | 4px  | Tight gaps (icon-text, badge)        |
| `--sp-2` | 6px  | Tag gaps, inline spacing             |
| `--sp-3` | 8px  | Inner component gaps                 |
| `--sp-4` | 10px | Card padding, list item gaps         |
| `--sp-5` | 14-16px | Section padding, component gaps   |
| `--sp-6` | 20px | Panel horizontal padding             |

### 4.3 Rules

- Header: fixed height 56px, `padding: 0 20px`, `border-bottom: 3px solid var(--accent)`.
- Sidebar: fixed width 300px, full height, `border-right: 2px solid var(--border)`.
- Main content area: `flex: 1`, overflow-y auto.
- Dashboard stats: horizontal flex row, `gap: 16px`, `padding: 6px 20px`, height 32px.

---

## 5. Components

### 5.1 Pixel Avatar

```css
.pixel-avatar {
  border: 2px solid var(--border);
  box-shadow: 4px 4px 0px rgba(0, 0, 0, 0.4);
  /* No border-radius */
}

.pixel-avatar.running .status-indicator {
  background: var(--success);
  box-shadow: var(--glow-success);
}
```

- 8x8 pixel grid with symmetric identicon pattern.
- NES-inspired saturated color palette, dark background (12% lightness).
- Status indicator: 10px square at bottom-right corner with 2px solid border.
- `image-rendering: pixelated` on canvas.

### 5.2 Process List Items

```css
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
```

- Transitions use `step-end` timing for pixel-perfect state changes.
- PID displayed as `PID:12345` in pixel font.
- Empty state uses ASCII art box.

### 5.3 Status Badges

```css
.status-badge {
  font-family: var(--font-pixel);
  font-size: 8px;
  padding: 3px 10px;
  border: 2px solid;
  letter-spacing: 1px;
  /* No border-radius */
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
```

- Square bordered boxes with neon glow. No rounded corners.
- Use Unicode symbols: `▶ ACTIVE`, `■ IDLE`.

### 5.4 Status Dot

```css
.status-dot {
  width: 8px;
  height: 8px;
  /* Square, no border-radius */
}

.status-dot.running {
  background: var(--success);
  box-shadow: var(--glow-success);
}
```

- Square dots (no `border-radius`), not circles.
- Running dot has pulsing glow animation.

### 5.5 Buttons

| Variant   | Background        | Text              | Border            | Usage            |
|-----------|-------------------|-------------------|-------------------|------------------|
| Primary   | `var(--accent)`   | `var(--text-inverse)` | `2px solid var(--accent-light)` | Main actions     |
| Secondary | `var(--bg-tertiary)` | `var(--text-primary)` | `2px solid var(--border)` | Secondary actions |
| Ghost     | transparent       | `var(--text-secondary)` | `2px solid transparent` | Icon buttons     |

```css
button {
  border: 2px solid;
  padding: 6px 14px;
  font-family: var(--font-pixel);
  font-size: 9px;
  cursor: pointer;
  transition: all 0.1s step-end;
}
```

- All buttons use pixel font. No border-radius.

### 5.6 Connection Badge

```css
.connection-badge {
  font-family: var(--font-pixel);
  font-size: 9px;
  padding: 4px 12px;
  border: 2px solid;
  letter-spacing: 1px;
}

.connection-badge.connected {
  border-color: var(--success);
  color: var(--success);
  background: var(--success-bg);
  text-shadow: var(--glow-success);
}

.connection-badge.disconnected {
  border-color: var(--danger);
  color: var(--danger);
  background: var(--danger-bg);
  animation: blink 1.2s step-end infinite;
}
```

- Use `◆` / `◇` icons for connected/disconnected.
- Disconnected state blinks with `step-end` timing.

### 5.7 Log Entry

```css
.log-card {
  background: var(--bg-primary);
  border: 2px solid var(--border);
  border-left: 4px solid transparent;
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
```

- Role badges are 28x28px square boxes with 2px border (no border-radius).
- Content type tags use 7px pixel font with `1px solid` borders.
- `▼` text chevron for expand/collapse (not SVG).
- Expanded detail uses `1px dashed` border separator.

### 5.8 Notification Panel

```css
.notification-panel {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  width: 340px;
  max-height: 400px;
  background: var(--bg-primary);
  border: 2px solid var(--border);
  box-shadow: 8px 8px 0px rgba(0, 0, 0, 0.6);
  z-index: 100;
}
```

- Uses flat offset shadow instead of blurred shadow.
- Bell button uses `◆` / `■` glyphs.
- Close button uses `[X]` text.
- Notification icons: `+` for start, `x` for exit.

---

## 6. Visual Effects

### 6.1 Shadows

| Level    | Value                                  | Usage                    |
|----------|----------------------------------------|--------------------------|
| Subtle   | `4px 4px 0px rgba(0, 0, 0, 0.4)`      | Avatars, small elements  |
| Medium   | `6px 6px 0px rgba(0, 0, 0, 0.5)`      | Cards, panels            |
| Elevated | `8px 8px 0px rgba(0, 0, 0, 0.6)`      | Dropdowns, notifications |

- All shadows are **flat offset shadows** (no blur). This creates the pixel-art depth illusion.
- No blurred `box-shadow` anywhere.

### 6.2 Borders

- Default: `2px solid var(--border)` (`#2a2a5a`).
- Accent left-border: `3-4px solid var(--accent)` for selected/active items.
- **No border-radius**: All elements are sharp rectangles. `border-radius: 0` everywhere.
- Separators: `1px dashed var(--border)` for internal divisions (session detail, log body).

### 6.3 Transitions

```css
transition: all 0.1s step-end;
```

- All transitions use `step-end` timing function for instant, pixel-perfect state changes.
- No smooth easing (`ease`, `ease-in-out`). No transform/scale animations.

### 6.4 CRT Scanline Overlay

```css
.scanlines {
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 100%;
  pointer-events: none;
  z-index: 9999;
  background: repeating-linear-gradient(
    0deg,
    rgba(0, 0, 0, 0.08) 0px,
    rgba(0, 0, 0, 0.08) 1px,
    transparent 1px,
    transparent 3px
  );
}
```

- Applied globally via a fixed overlay div.
- Does not block pointer events.
- Creates authentic CRT monitor scanline effect.

### 6.5 Neon Glow

```css
text-shadow: 0 0 8px rgba(color, 0.4);
box-shadow: 0 0 8px rgba(color, 0.4);
```

- Applied to status badges, active connection indicator, running status dots.
- Use the element's primary color at 40% opacity.
- Keep glow subtle — 8px spread maximum.

### 6.6 Animations

```css
@keyframes blink {
  50% { opacity: 0.3; }
}
/* Applied with: animation: blink 1.2s step-end infinite; */

@keyframes pulse-glow {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
```

- Blink for disconnected/error states.
- Pulse-glow for running status indicators.
- Always use `step-end` timing.

---

## 7. Iconography

- **No SVG icons**. Use Unicode/ASCII symbols exclusively:
  - Status: `▶` (active), `■` (idle/stopped)
  - Connection: `◆` (connected), `◇` (disconnected)
  - Notifications: `+` (start), `x` (exit)
  - Close: `[X]`
  - Expand: `▼`
  - Prompt: `>` (cwd prefix)
  - Divider: `│`
- Role badges: 28x28px square with 2px border, containing text `AI` (assistant) or `U` (user).
- Status dots: 8x8px squares (no border-radius).

### Role Badge Colors

| Role      | Border / Text          | Background                     |
|-----------|------------------------|--------------------------------|
| Assistant | `var(--accent)`        | `rgba(255, 170, 0, 0.1)`      |
| User      | `var(--info)`          | `rgba(0, 212, 255, 0.1)`      |

---

## 8. Scrollbar

```css
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
```

Chunky, pixelated scrollbar with visible borders. Hover turns amber.

---

## 9. Empty States

```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
}
```

- ASCII art box patterns for empty state content:
  ```
  ┌──────────────────┐
  │  SELECT A        │
  │  PROCESS TO      │
  │  VIEW DETAILS    │
  └──────────────────┘
  ```
- Use `--font-pixel` at 8px, `line-height: 2`, `white-space: pre`.
- Muted color, centered.

---

## 10. Text Selection

```css
::selection {
  background: var(--accent);
  color: var(--text-inverse);
}
```

Selection highlight uses the amber accent.

---

## 11. Content Type Tags

| Type         | Border          | Text           | Background     | Extra                  |
|--------------|-----------------|----------------|----------------|------------------------|
| TOOL         | `--accent`      | `--accent`     | `--accent-bg`  | —                      |
| RESULT       | `--info`        | `--info`       | `--info-bg`    | —                      |
| TEXT         | `--border`      | `--text-secondary` | `--bg-tertiary` | —                  |
| THINK        | `#7C3AED`       | `#A78BFA`      | `#1a0a3e`      | `text-shadow: 0 0 6px rgba(124, 58, 237, 0.4)` |

---

## 12. Responsive Behavior

- **Minimum width**: 800px (dashboard tools don't need mobile).
- **Sidebar**: Fixed 300px, does not collapse.
- **Detail panel**: Fills remaining space, scrolls independently.
- **Dashboard stats**: Horizontal flex row, no wrapping.

---

## 13. Design Principles

1. **Pixel-perfect edges**: No border-radius anywhere. All elements are sharp rectangles.
2. **Flat offset shadows**: Use `Npx Npx 0px` shadows with no blur for depth. No CSS drop shadows.
3. **Neon glow accents**: Key status elements emit a subtle glow via `text-shadow` or `box-shadow`. Glow is restrained, never overpowering.
4. **Step-end transitions**: All state changes use `step-end` timing for instant, non-interpolated pixel transitions.
5. **CRT atmosphere**: The scanline overlay is always present, creating an authentic retro monitor feel.
6. **ASCII art decoration**: Empty states and decorative elements use box-drawing characters (`┌─┐│└─┘`).
7. **Information density**: Show relevant data compactly. Pixel font for all technical values (PIDs, tags, labels).
8. **Restraint with glow**: Neon glow effects are applied only to interactive/active elements and status indicators, not decorative text.
9. **No SVGs**: All icons use Unicode symbols and ASCII characters. No vector graphics.
10. **Font anti-aliasing off**: Explicitly disable font smoothing to preserve pixel font rendering at all sizes.
