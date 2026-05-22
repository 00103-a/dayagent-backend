<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  weatherType: {
    type: String,   // 'sunny' | 'rainy' | 'snowy' | 'cloudy'
    default: 'sunny',
  },
})

const canvasRef = ref(null)
const rainCanvasRef = ref(null)
const canvasOpacity = ref(1)
const W = 320
const H = 180
let tick = 0
let rafId = null
let rainRafId = null

/* ═══════════════════════════════════════════════════════════
   Time period
   ═══════════════════════════════════════════════════════════ */
function getPeriod(h) {
  if (h >= 5 && h < 8) return 'dawn'
  if (h >= 8 && h < 17) return 'day'
  if (h >= 17 && h < 20) return 'dusk'
  return 'night'
}

/* ═══════════════════════════════════════════════════════════
   Sky gradient — darkened, purple/gray shift
   ═══════════════════════════════════════════════════════════ */
function drawSky(ctx, period, weather) {
  const grad = ctx.createLinearGradient(0, 0, 0, H)

  // Weather-adjusted sky colors (desaturated, dark)
  if (weather === 'snowy') {
    grad.addColorStop(0, '#080c14')
    grad.addColorStop(0.6, '#0e1420')
    grad.addColorStop(1, '#121828')
  } else if (weather === 'rainy') {
    grad.addColorStop(0, '#060810')
    grad.addColorStop(0.6, '#0a1018')
    grad.addColorStop(1, '#0d1218')
  } else if (weather === 'cloudy') {
    grad.addColorStop(0, '#080808')
    grad.addColorStop(0.6, '#0e0e0e')
    grad.addColorStop(1, '#111111')
  } else if (weather === 'fog') {
    grad.addColorStop(0, '#0d0a08')
    grad.addColorStop(0.6, '#14100c')
    grad.addColorStop(1, '#1a1510')
  } else {
    // sunny / default — slight blue shift
    switch (period) {
      case 'dawn':
        grad.addColorStop(0, '#080810')
        grad.addColorStop(0.5, '#0d1628')
        grad.addColorStop(0.8, '#120e18')
        grad.addColorStop(1, '#1a1214')
        break
      case 'day':
        grad.addColorStop(0, '#080810')
        grad.addColorStop(0.5, '#0d1628')
        grad.addColorStop(1, '#141820')
        break
      case 'dusk':
        grad.addColorStop(0, '#060412')
        grad.addColorStop(0.4, '#0a0c20')
        grad.addColorStop(0.75, '#140e18')
        grad.addColorStop(1, '#1a1016')
        break
      case 'night':
      default:
        grad.addColorStop(0, '#040408')
        grad.addColorStop(0.6, '#060810')
        grad.addColorStop(1, '#0a0c14')
        break
    }
  }

  ctx.fillStyle = grad
  ctx.fillRect(0, 0, W, H)

  // Extra darkening for cloudy/fog
  if (weather === 'cloudy') {
    ctx.fillStyle = 'rgba(0,0,0,0.30)'
    ctx.fillRect(0, 0, W, H)
  }
  if (weather === 'fog') {
    ctx.fillStyle = 'rgba(200,180,150,0.04)'
    ctx.fillRect(0, 0, W, H)
  }
}

/* ═══════════════════════════════════════════════════════════
   Celestial body
   ═══════════════════════════════════════════════════════════ */
function drawCelestial(ctx, period) {
  const mx = 260, my = 30
  ctx.imageSmoothingEnabled = false

  if (period === 'night') {
    ctx.fillStyle = '#d8d0c0'
    ctx.fillRect(mx, my, 8, 8)
    ctx.fillStyle = '#b8b0a0'
    ctx.fillRect(mx + 2, my + 2, 2, 2)
    ctx.fillRect(mx + 5, my + 4, 1, 1)
    ctx.fillRect(mx + 3, my + 5, 2, 1)
    ctx.fillStyle = 'rgba(200, 190, 170, 0.06)'
    ctx.fillRect(mx - 4, my - 4, 16, 16)
  } else if (period === 'dawn' || period === 'dusk') {
    const sx = mx, sy = my + 10
    ctx.fillStyle = '#e07030'
    ctx.fillRect(sx, sy, 8, 8)
    ctx.fillStyle = '#d08030'
    ctx.fillRect(sx + 2, sy + 2, 4, 4)
    ctx.fillStyle = '#c87828'
    ctx.fillRect(sx + 3, sy + 3, 2, 2)
    ctx.fillStyle = 'rgba(224, 112, 48, 0.06)'
    ctx.fillRect(sx - 6, sy - 6, 20, 20)
    ctx.fillStyle = 'rgba(224, 112, 48, 0.03)'
    ctx.fillRect(sx - 12, sy - 12, 32, 32)
  }
}

/* ═══════════════════════════════════════════════════════════
   Stars
   ═══════════════════════════════════════════════════════════ */
const starSeeds = Array.from({ length: 40 }, () => ({
  x: Math.floor(Math.random() * W),
  y: Math.floor(Math.random() * H * 0.55),
  phase: Math.random() * Math.PI * 2,
  speed: 0.02 + Math.random() * 0.04,
}))

function drawStars(ctx, period, tick) {
  if (period !== 'night') return
  for (const s of starSeeds) {
    const alpha = 0.2 + 0.5 * (0.5 + 0.5 * Math.sin(tick * s.speed + s.phase))
    ctx.fillStyle = `rgba(255,250,240,${alpha.toFixed(2)})`
    ctx.fillRect(s.x, s.y, 1, 1)
    if (Math.sin(s.phase * 7) > 0.7) {
      ctx.fillRect(s.x + 1, s.y, 1, 1)
    }
  }
}

/* ═══════════════════════════════════════════════════════════
   City silhouette
   ═══════════════════════════════════════════════════════════ */
const buildings = [
  { x: 0, w: 30, h: 22 }, { x: 34, w: 20, h: 30 }, { x: 58, w: 28, h: 18 },
  { x: 90, w: 16, h: 38 }, { x: 110, w: 24, h: 26 }, { x: 138, w: 32, h: 20 },
  { x: 174, w: 18, h: 34 }, { x: 196, w: 26, h: 24 }, { x: 226, w: 22, h: 30 },
  { x: 252, w: 30, h: 16 }, { x: 286, w: 18, h: 28 }, { x: 300, w: 20, h: 20 },
]

const litWindows = []
for (let i = 0; i < 25; i++) {
  const b = buildings[Math.floor(Math.random() * buildings.length)]
  litWindows.push({
    bx: b.x, bw: b.w, bh: b.h,
    wx: 3 + Math.floor(Math.random() * Math.max(1, b.w - 6)),
    wy: 4 + Math.floor(Math.random() * Math.max(1, b.h - 10)),
    phase: Math.random() * Math.PI * 2,
  })
}

function drawCity(ctx, tick) {
  const groundY = H - 28
  for (const b of buildings) {
    ctx.fillStyle = '#0c0a08'
    ctx.fillRect(b.x, groundY - b.h, b.w, b.h)
  }
  for (const lw of litWindows) {
    const alpha = 0.15 + 0.25 * (0.5 + 0.5 * Math.sin(tick * 0.03 + lw.phase))
    ctx.fillStyle = `rgba(224,180,120,${alpha.toFixed(2)})`
    ctx.fillRect(lw.bx + lw.wx, groundY - lw.bh + lw.wy, 2, 2)
  }
  // Ground
  ctx.fillStyle = '#0a0806'
  ctx.fillRect(0, groundY, W, H - groundY)

  // City darkening overlay - darken to blend with content
  ctx.fillStyle = 'rgba(4, 3, 2, 0.50)'
  ctx.fillRect(0, groundY - 40, W, 40 + H - groundY)
}

/* ═══════════════════════════════════════════════════════════
   Street lamp
   ═══════════════════════════════════════════════════════════ */
function drawLamp(ctx, tick) {
  const lx = 100, baseY = H - 28
  const poleH = 34
  ctx.fillStyle = '#1a1815'
  ctx.fillRect(lx + 1, baseY - poleH, 2, poleH)
  ctx.fillStyle = '#2a2820'
  ctx.fillRect(lx - 1, baseY - poleH - 3, 6, 3)
  const glowAlpha = 0.04 + 0.015 * Math.sin(tick * 0.02)
  ctx.fillStyle = `rgba(224,160,100,${glowAlpha.toFixed(3)})`
  ctx.fillRect(lx - 10, baseY - poleH - 14, 24, 24)
  ctx.fillStyle = `rgba(224,160,80,${(glowAlpha * 1.8).toFixed(3)})`
  ctx.fillRect(lx - 4, baseY - poleH - 8, 12, 12)
  ctx.fillStyle = '#e0b870'
  ctx.fillRect(lx + 1, baseY - poleH - 2, 2, 2)
}

/* ═══════════════════════════════════════════════════════════
   Window frame
   ═══════════════════════════════════════════════════════════ */
function drawWindow(ctx) {
  ctx.fillStyle = '#0a0806'
  ctx.fillRect(0, 0, 18, H)
  ctx.fillStyle = '#0c0a07'
  for (let y = 0; y < H; y += 10) ctx.fillRect(14, y, 4, 6)
  ctx.fillStyle = '#0e0c08'
  ctx.fillRect(0, 0, 6, H)

  ctx.fillStyle = '#0a0806'
  ctx.fillRect(W - 18, 0, 18, H)
  ctx.fillStyle = '#0c0a07'
  for (let y = 0; y < H; y += 10) ctx.fillRect(W - 18, y, 4, 6)
  ctx.fillStyle = '#0e0c08'
  ctx.fillRect(W - 6, 0, 6, H)

  ctx.fillStyle = '#0a0806'
  ctx.fillRect(0, 0, W, 8)
  ctx.fillStyle = '#0c0a07'
  ctx.fillRect(0, 0, W, 4)

  ctx.fillStyle = '#0c0a08'
  ctx.fillRect(0, H - 10, W, 10)
  ctx.fillStyle = '#0e0c08'
  ctx.fillRect(0, H - 10, W, 3)
}

/* ═══════════════════════════════════════════════════════════
   Pixel cat — round sitting pose, 2×2 ears, pupils, tail wrap
   0=empty 1=#e07030 2=#c05820 3=#fff(eye) 4=#080604(pupil)
   ═══════════════════════════════════════════════════════════ */
const CAT_W = 16
const CAT_H = 16
const catPixels = [
  // 0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F
  [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ], // row 0
  [ 0, 0, 0, 0, 0, 2, 2, 0, 0, 2, 2, 0, 0, 0, 0, 0 ], // row 1  rounded ear tops
  [ 0, 0, 0, 0, 1, 1, 1, 2, 2, 1, 1, 1, 0, 0, 0, 0 ], // row 2  ears meet head
  [ 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0 ], // row 3  head top (wide, round)
  [ 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0 ], // row 4  head
  [ 0, 0, 0, 1, 1, 3, 4, 1, 1, 3, 4, 1, 1, 0, 0, 0 ], // row 5  eyes: white(3)+pupil(4)
  [ 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0 ], // row 6  head
  [ 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0 ], // row 7  chin (narrower)
  [ 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0 ], // row 8  neck
  [ 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0 ], // row 9  body top
  [ 0, 0, 0, 0, 2, 1, 1, 1, 1, 1, 1, 2, 0, 0, 0, 0 ], // row A  body (dark sides)
  [ 0, 0, 0, 0, 2, 1, 1, 1, 1, 1, 1, 2, 0, 0, 0, 0 ], // row B  body
  [ 0, 0, 0, 0, 0, 1, 2, 0, 0, 2, 1, 0, 0, 0, 0, 0 ], // row C  front legs
  [ 0, 0, 0, 0, 0, 2, 1, 0, 0, 1, 2, 0, 0, 0, 0, 0 ], // row D  back paws
  [ 0, 0, 0, 0, 0, 0, 2, 1, 1, 1, 2, 0, 0, 0, 0, 0 ], // row E  tail base (wraps right)
  [ 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 0, 0, 0, 0, 0 ], // row F  tail tip
]

function drawCat(ctx, tick) {
  const px = 2
  const cx = Math.floor(W / 2 - (CAT_W * px) / 2)
  const cy = H - 10 - CAT_H * px

  // Idle bob: 1.2s cycle, translateY 0 → -2px visual
  const idlePhase = tick * Math.PI / 6
  const bobY = Math.floor((Math.cos(idlePhase) - 1) / 2)

  const blinkPhase = (tick + 11) % 200

  for (let row = 0; row < CAT_H; row++) {
    for (let col = 0; col < CAT_W; col++) {
      const v = catPixels[row][col]
      if (v === 0) continue
      const x = cx + col * px
      const y = cy + row * px + bobY

      if (v === 1) ctx.fillStyle = '#e07030'
      else if (v === 2) ctx.fillStyle = '#c05820'
      else if (v === 3) ctx.fillStyle = (blinkPhase > 196) ? '#c05820' : '#ffffff'
      else if (v === 4) ctx.fillStyle = (blinkPhase > 196) ? '#c05820' : '#080604'

      ctx.fillRect(x, y, px, px)
    }
  }

  // Lamp glow wash
  const glowX = cx - 4
  const glowY = cy - 2 + bobY
  ctx.fillStyle = 'rgba(224, 160, 80, 0.05)'
  ctx.fillRect(glowX, glowY, CAT_W * px + 8, CAT_H * px + 6)
}

/* ═══════════════════════════════════════════════════════════
   Vignette
   ═══════════════════════════════════════════════════════════ */
function drawVignette(ctx) {
  const grad = ctx.createRadialGradient(W / 2, H / 2, W * 0.4, W / 2, H / 2, W * 0.75)
  grad.addColorStop(0, 'transparent')
  grad.addColorStop(1, 'rgba(4,3,2,0.60)')
  ctx.fillStyle = grad
  ctx.fillRect(0, 0, W, H)

  const topGrad = ctx.createLinearGradient(0, 0, 0, H * 0.3)
  topGrad.addColorStop(0, 'rgba(0,0,0,0.45)')
  topGrad.addColorStop(1, 'transparent')
  ctx.fillStyle = topGrad
  ctx.fillRect(0, 0, W, H * 0.3)
}

/* ═══════════════════════════════════════════════════════════
   Snow (stays on main canvas — pixel snow is fine)
   ═══════════════════════════════════════════════════════════ */
const snowFlakes = Array.from({ length: 35 }, () => ({
  x: Math.random() * (W - 36) + 18,
  y: Math.random() * H,
  speed: 0.3 + Math.random() * 0.8,
  drift: (Math.random() - 0.5) * 0.4,
  size: Math.random() > 0.7 ? 2 : 1,
}))

function drawSnow(ctx) {
  for (const s of snowFlakes) {
    ctx.fillStyle = 'rgba(255,255,255,0.5)'
    ctx.fillRect(Math.floor(s.x), Math.floor(s.y), s.size, s.size)
    s.y += s.speed
    s.x += s.drift
    if (s.y > H) { s.y = -4; s.x = Math.random() * (W - 36) + 18 }
    if (s.x < 18 || s.x > W - 18) s.drift *= -1
  }
}

/* ═══════════════════════════════════════════════════════════
   Cloud overlay
   ═══════════════════════════════════════════════════════════ */
const clouds = [
  { x: 40, y: 20, w: 40, h: 10 },
  { x: 120, y: 35, w: 55, h: 12 },
  { x: 220, y: 18, w: 35, h: 9 },
]

function drawClouds(ctx, tick) {
  for (const c of clouds) {
    const driftX = c.x + Math.sin(tick * 0.005 + c.x) * 4
    ctx.fillStyle = 'rgba(20,18,22,0.5)'
    ctx.fillRect(driftX, c.y, c.w, c.h)
    ctx.fillStyle = 'rgba(24,22,26,0.4)'
    ctx.fillRect(driftX + 4, c.y - 3, c.w - 8, c.h + 2)
    ctx.fillStyle = 'rgba(18,16,20,0.45)'
    ctx.fillRect(driftX + 8, c.y + c.h - 2, c.w - 16, 4)
  }
}

/* ═══════════════════════════════════════════════════════════
   Main scene render (no rain here — rain is separate canvas)
   ═══════════════════════════════════════════════════════════ */
function render() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  ctx.imageSmoothingEnabled = false

  const now = new Date()
  const hour = now.getHours()
  const period = getPeriod(hour)
  const weather = props.weatherType || 'sunny'

  ctx.clearRect(0, 0, W, H)

  drawSky(ctx, period, weather)
  drawCelestial(ctx, period)
  drawStars(ctx, period, tick)
  if (weather === 'cloudy') drawClouds(ctx, tick)
  drawCity(ctx, tick)
  drawLamp(ctx, tick)
  if (weather === 'snowy') drawSnow(ctx)
  drawWindow(ctx)
  drawCat(ctx, tick)
  drawVignette(ctx)
}

/* ═══════════════════════════════════════════════════════════
   Rain system — separate high-res canvas, slanted line segments
   ═══════════════════════════════════════════════════════════ */
const RAIN_COUNT = 100
const rainDrops = []

function initRain(w, h) {
  rainDrops.length = 0
  for (let i = 0; i < RAIN_COUNT; i++) {
    rainDrops.push({
      x: Math.random() * w,
      y: Math.random() * h,
      len: 12 + Math.random() * 20,          // 12–32px length
      speedY: 12 + Math.random() * 18,       // fast fall
      speedX: 2 + Math.random() * 3,         // slight horizontal drift (15° wind)
      alpha: 0.2 + Math.random() * 0.25,
    })
  }
}

function drawRain(ctx, w, h) {
  ctx.clearRect(0, 0, w, h)
  ctx.strokeStyle = 'rgba(160, 190, 220, 0.35)'
  ctx.lineWidth = 1
  ctx.lineCap = 'round'

  for (const d of rainDrops) {
    ctx.beginPath()
    ctx.moveTo(d.x, d.y)
    // 15° slant: horizontal offset ≈ tan(15°) * len ≈ 0.268 * len
    const slantX = d.len * 0.27
    ctx.lineTo(d.x + slantX, d.y + d.len)
    ctx.stroke()

    d.y += d.speedY
    d.x += d.speedX
    if (d.y > h + 20) { d.y = -30; d.x = Math.random() * w }
    if (d.x > w + 20) d.x = -20
    if (d.x < -20) d.x = w + 20
  }
}

/* ── Window water drops (on rain canvas, drawn first) ────── */
const windowDrops = []
const WINDOW_DROP_COUNT = 10

function initWindowDrops(w, h) {
  windowDrops.length = 0
  for (let i = 0; i < WINDOW_DROP_COUNT; i++) {
    windowDrops.push({
      x: w * 0.05 + Math.random() * w * 0.9,  // spread across window
      y: Math.random() * h,
      height: 8 + Math.random() * 14,          // tall teardrop
      width: 1.5 + Math.random() * 2,
      speed: 0.3 + Math.random() * 0.6,        // very slow slide
      trail: 6 + Math.random() * 10,           // teardrop trail length
    })
  }
}

function drawWindowDrops(ctx, w, h) {
  for (const d of windowDrops) {
    // Teardrop: narrow top, wider bottom
    const opacity = 0.25 + Math.random() * 0.15

    // Trail (fading)
    ctx.fillStyle = `rgba(180, 210, 240, ${(opacity * 0.4).toFixed(2)})`
    ctx.fillRect(d.x, d.y - d.trail, d.width * 0.4, d.trail)

    // Main drop body (elongated)
    ctx.fillStyle = `rgba(180, 210, 240, ${opacity.toFixed(2)})`
    // Narrow top
    ctx.fillRect(d.x, d.y, d.width * 0.5, d.height * 0.4)
    // Wider bottom
    ctx.fillRect(d.x - 0.5, d.y + d.height * 0.3, d.width + 1, d.height * 0.7)

    d.y += d.speed
    if (d.y > h + 20) {
      d.y = -20
      d.x = w * 0.05 + Math.random() * w * 0.9
    }
  }
}

/* ── Rain animation loop (runs only when rainy) ──────────── */
function startRainLoop() {
  const canvas = rainCanvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')

  function resizeRainCanvas() {
    const c = rainCanvasRef.value
    if (!c) return
    const w = window.innerWidth
    const h = window.innerHeight
    if (c.width !== w || c.height !== h) {
      c.width = w
      c.height = h
      initRain(w, h)
      initWindowDrops(w, h)
    }
  }
  resizeRainCanvas()

  // Listen for window resize (Electron maximize fix)
  window.addEventListener('resize', resizeRainCanvas)

  function rainLoop() {
    const c = rainCanvasRef.value
    if (!c) return
    const ctx2 = c.getContext('2d')
    drawWindowDrops(ctx2, c.width, c.height)
    drawRain(ctx2, c.width, c.height)
    rainRafId = requestAnimationFrame(rainLoop)
  }

  rainRafId = requestAnimationFrame(rainLoop)

  // Return cleanup
  return () => {
    window.removeEventListener('resize', resizeRainCanvas)
  }
}

function stopRainLoop() {
  if (rainRafId) {
    cancelAnimationFrame(rainRafId)
    rainRafId = null
  }
  const canvas = rainCanvasRef.value
  if (canvas) {
    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, canvas.width, canvas.height)
  }
}

let rainCleanup = null

watch(() => props.weatherType, (val, oldVal) => {
  if (val === oldVal) return

  // Main scene smooth transition
  if (canvasRef.value) {
    canvasOpacity.value = 0
    if (transitionTimer) clearTimeout(transitionTimer)
    transitionTimer = setTimeout(() => {
      render()
      canvasOpacity.value = 1
      transitionTimer = null
    }, 500)
  }

  // Rain start/stop
  if (val === 'rainy' && oldVal !== 'rainy') {
    rainCleanup = startRainLoop()
  } else if (val !== 'rainy' && oldVal === 'rainy') {
    stopRainLoop()
    if (rainCleanup) { rainCleanup(); rainCleanup = null }
  }
})

/* ═══════════════════════════════════════════════════════════
   Weather transition timer
   ═══════════════════════════════════════════════════════════ */
let transitionTimer = null

/* ═══════════════════════════════════════════════════════════
   Scene animation loop (~10 fps pixel feel)
   ═══════════════════════════════════════════════════════════ */
let lastFrame = 0
const FRAME_INTERVAL = 100

function loop(timestamp) {
  if (timestamp - lastFrame >= FRAME_INTERVAL) {
    tick++
    render()
    lastFrame = timestamp
  }
  rafId = requestAnimationFrame(loop)
}

/* ═══════════════════════════════════════════════════════════
   Resize handler for main canvas (Electron maximize fix)
   ═══════════════════════════════════════════════════════════ */
function handleResize() {
  // Main canvas stays at internal resolution 320x180;
  // CSS scales it to 100vw×100vh via width/height: 100%
  // Just force re-render after resize
  if (canvasRef.value) render()
}

/* ═══════════════════════════════════════════════════════════
   Lifecycle
   ═══════════════════════════════════════════════════════════ */
onMounted(() => {
  const canvas = canvasRef.value
  if (canvas) {
    canvas.width = W
    canvas.height = H
    canvas.style.width = '100%'
    canvas.style.height = '100%'
    canvas.style.imageRendering = 'pixelated'
  }
  lastFrame = performance.now()
  rafId = requestAnimationFrame(loop)

  window.addEventListener('resize', handleResize)

  // Start rain if already rainy
  if (props.weatherType === 'rainy') {
    rainCleanup = startRainLoop()
  }
})

onUnmounted(() => {
  if (rafId) cancelAnimationFrame(rafId)
  if (rainRafId) cancelAnimationFrame(rainRafId)
  if (transitionTimer) clearTimeout(transitionTimer)
  if (rainCleanup) rainCleanup()
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div class="scene-bg" aria-hidden="true">
    <!-- Layer 0: Main scene (pixel art, 320x180 → 100% scaled) -->
    <canvas
      ref="canvasRef"
      class="scene-bg__canvas"
      :style="{ opacity: canvasOpacity }"
    />
    <!-- Layer 1: Rain + window drops (high-res full window) -->
    <canvas
      ref="rainCanvasRef"
      class="scene-bg__rain"
    />
    <!-- CRT scanlines overlay -->
    <div class="scene-bg__scanlines" />
  </div>
</template>

<style scoped>
.scene-bg {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  background: #080604;
}

.scene-bg__canvas {
  display: block;
  width: 100%;
  height: 100%;
  image-rendering: pixelated;
  image-rendering: crisp-edges;
  transition: opacity 0.5s ease;
}

/* Rain overlay canvas — high resolution, above scene, below UI */
.scene-bg__rain {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  z-index: 1;
  pointer-events: none;
  will-change: transform;
}

/* CRT scanlines */
.scene-bg__scanlines {
  pointer-events: none;
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.06) 2px,
    rgba(0, 0, 0, 0.06) 4px
  );
}
</style>
