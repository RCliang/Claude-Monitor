<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'
import { useTheme } from '../composables/useTheme'

const props = defineProps<{
  seed: string
  size?: number
  status?: 'running' | 'idle' | 'exited'
}>()

const { theme } = useTheme()
const canvasRef = ref<HTMLCanvasElement>()

function hashSeed(str: string): number {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  return Math.abs(hash)
}

function generatePalette(seed: string, isDark: boolean): { bg: string; fg: string[] } {
  const h = hashSeed(seed)
  const hues = [0, 30, 60, 120, 180, 210, 270, 300]
  const hue = hues[h % hues.length]
  const sat = isDark ? 90 : 65

  const fg: string[] = []
  for (let i = 0; i < 3; i++) {
    const h2 = hues[(h + i * 3) % hues.length]
    const l = isDark
      ? 50 + ((h >> (i * 4)) & 15)
      : 30 + ((h >> (i * 4)) & 15)
    fg.push(`hsl(${h2}, ${sat}%, ${l}%)`)
  }

  const bgLightness = isDark ? 12 : 88
  const bg = `hsl(${hue}, ${isDark ? 30 : 15}%, ${bgLightness}%)`

  return { bg, fg }
}

function generatePattern(seed: string): boolean[][] {
  const h = hashSeed(seed)
  const grid: boolean[][] = []

  for (let y = 0; y < 8; y++) {
    grid[y] = []
    for (let x = 0; x < 4; x++) {
      const bit = (h >> ((y * 4 + x) % 32)) & 1
      grid[y][x] = bit === 1
      grid[y][7 - x] = bit === 1
    }
  }

  grid[2][2] = true; grid[2][5] = true
  grid[5][3] = true; grid[5][4] = true

  return grid
}

const pixelSize = computed(() => Math.floor((props.size || 40) / 8))

function drawAvatar() {
  if (!canvasRef.value) return
  const canvas = canvasRef.value
  const totalSize = props.size || 40
  canvas.width = totalSize
  canvas.height = totalSize

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const isDark = theme.value === 'dark'
  const palette = generatePalette(props.seed, isDark)
  const pattern = generatePattern(props.seed)
  const px = pixelSize.value

  ctx.fillStyle = palette.bg
  ctx.fillRect(0, 0, totalSize, totalSize)

  for (let y = 0; y < 8; y++) {
    for (let x = 0; x < 8; x++) {
      if (pattern[y][x]) {
        const colorIdx = ((x + y) % palette.fg.length)
        ctx.fillStyle = palette.fg[colorIdx]
        ctx.fillRect(x * px, y * px, px, px)
      }
    }
  }
}

onMounted(drawAvatar)
watch(() => props.seed, drawAvatar)
watch(() => props.size, drawAvatar)
watch(theme, drawAvatar)
</script>

<template>
  <div class="pixel-avatar" :class="status">
    <canvas ref="canvasRef" :width="size || 40" :height="size || 40" />
    <span class="status-indicator" v-if="status"></span>
  </div>
</template>

<style scoped>
.pixel-avatar {
  position: relative;
  display: inline-flex;
  overflow: hidden;
  image-rendering: pixelated;
  flex-shrink: 0;
  border: 2px solid var(--border);
  background: var(--bg-tertiary);
  box-shadow: var(--shadow-subtle);
}

.pixel-avatar canvas {
  image-rendering: pixelated;
  image-rendering: crisp-edges;
  display: block;
}

.status-indicator {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 10px;
  height: 10px;
  border: 2px solid var(--bg-primary);
}

.pixel-avatar.running .status-indicator {
  background: var(--success);
  box-shadow: var(--glow-success);
}

.pixel-avatar.idle .status-indicator {
  background: var(--warning);
}

.pixel-avatar.exited .status-indicator {
  background: var(--danger);
}
</style>
