<template>
  <canvas ref="canvas" class="fixed inset-0 pointer-events-none" style="z-index:0"></canvas>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'

const canvas = ref(null)
let ctx = null
let particles = []
let animationId = null
let mouseX = -1000
let mouseY = -1000
let targetMode = false
let wasTargetMode = false
let smileyCenterX = 0
let smileyCenterY = 0
let smileyVX = 0
let smileyVY = 0
const SPRING_K = 0.25   // 弹簧刚度
const SPRING_D = 0.45   // 阻尼
let leaveTimer = null
const LEAVE_DELAY = 800
const PARTICLE_COUNT = 1200

let currentIcon = 'sun'  // 'sun' or 'moon'

function isDaytime() {
  const hour = new Date().getHours()
  return hour >= 6 && hour < 18
}

// 生成太阳或月亮的目标点
function generateIconPoints(size, daytime) {
  const cx = 0
  const cy = 0
  const radius = size / 2
  const points = []

  if (daytime) {
    // === 太阳 ===
    // 主体圆圈
    const coreRadius = radius * 0.55
    for (let i = 0; i < 180; i++) {
      const angle = (i / 180) * Math.PI * 2
      points.push({ x: cx + Math.cos(angle) * coreRadius, y: cy + Math.sin(angle) * coreRadius })
    }
    // 填充内部
    for (let i = 0; i < 60; i++) {
      const a = Math.random() * Math.PI * 2
      const r = Math.random() * coreRadius * 0.8
      points.push({ x: cx + Math.cos(a) * r, y: cy + Math.sin(a) * r })
    }
    // 光芒射线（8条）
    const rayCount = 8
    const rayInner = coreRadius * 1.05
    const rayOuter = radius
    for (let r = 0; r < rayCount; r++) {
      const baseAngle = (r / rayCount) * Math.PI * 2
      for (let i = 0; i < 20; i++) {
        const t = i / 20
        const dist = rayInner + t * (rayOuter - rayInner)
        const spread = (1 - t) * 0.08 + 0.02
        const angle = baseAngle + (Math.random() - 0.5) * spread
        points.push({ x: cx + Math.cos(angle) * dist, y: cy + Math.sin(angle) * dist })
      }
    }
  } else {
    // === 月亮 ===
    // 外圆
    for (let i = 0; i < 150; i++) {
      const angle = (i / 150) * Math.PI * 2
      points.push({ x: cx + Math.cos(angle) * radius, y: cy + Math.sin(angle) * radius })
    }
    // 内切弧（形成月牙）
    const cutRadius = radius * 0.75
    const cutCx = radius * 0.3
    for (let i = 0; i < 60; i++) {
      const angle = Math.PI * 0.6 + (i / 60) * Math.PI * 1.6
      points.push({ x: cx + cutCx + Math.cos(angle) * cutRadius, y: cy + Math.sin(angle) * cutRadius })
    }
    // 月牙内部填充
    for (let i = 0; i < 40; i++) {
      const a = Math.random() * Math.PI * 2
      const r = Math.random() * radius * 0.65
      // 只在月牙区域（偏移中心右侧）
      const px = cx + Math.cos(a) * r
      const py = cy + Math.sin(a) * r
      const distToCut = Math.sqrt((px - (cx + cutCx)) ** 2 + (py - cy) ** 2)
      if (distToCut < cutRadius) continue // 切掉的部分不填充
      points.push({ x: px, y: py })
    }
    // 星星（5颗散布在周围）
    const starPositions = [
      { angle: Math.PI * 0.2, dist: radius * 1.3 },
      { angle: Math.PI * 0.5, dist: radius * 1.25 },
      { angle: Math.PI * 0.8, dist: radius * 1.35 },
      { angle: Math.PI * 1.3, dist: radius * 1.2 },
      { angle: Math.PI * 1.7, dist: radius * 1.3 },
    ]
    for (const star of starPositions) {
      for (let i = 0; i < 8; i++) {
        const a = star.angle + (i / 8) * Math.PI * 2
        const r = radius * 0.08
        points.push({ x: cx + star.dist * Math.cos(star.angle) + Math.cos(a) * r, y: cy + star.dist * Math.sin(star.angle) + Math.sin(a) * r })
      }
    }
  }

  return points
}

let smileyPoints = []

function createParticle() {
  return {
    x: Math.random() * canvas.value.width,
    y: Math.random() * canvas.value.height,
    vx: (Math.random() - 0.5) * 0.8,
    vy: (Math.random() - 0.5) * 0.8,
    size: Math.random() * 2.5 + 1,
    opacity: Math.random() * 0.5 + 0.3,
    // 分配给笑脸的某个目标点
    targetIndex: Math.floor(Math.random() * smileyPoints.length),
    // 动画进度
    gatherProgress: 0,
  }
}

function initParticles() {
  particles = []
  for (let i = 0; i < PARTICLE_COUNT; i++) {
    particles.push(createParticle())
  }
}

function getSmileySize() {
  return Math.min(window.innerWidth, window.innerHeight) / 3.5
}

function refreshIconPoints() {
  currentIcon = isDaytime() ? 'sun' : 'moon'
  smileyPoints = generateIconPoints(getSmileySize(), isDaytime())
}

function getSmileyTarget(particle) {
  const target = smileyPoints[particle.targetIndex % smileyPoints.length]
  // 加随机抖动，图标边缘不规整
  const jitter = 8 + Math.random() * 6
  const jx = (Math.random() - 0.5) * jitter * 2
  const jy = (Math.random() - 0.5) * jitter * 2
  return {
    x: smileyCenterX + target.x + jx,
    y: smileyCenterY + target.y + jy,
  }
}

function updateParticles() {
  const speed = 0.03

  // 果冻弹簧：平滑跟随鼠标 + 刹停弹跳
  const ax = (mouseX - smileyCenterX) * SPRING_K - smileyVX * SPRING_D
  const ay = (mouseY - smileyCenterY) * SPRING_K - smileyVY * SPRING_D
  smileyVX += ax
  smileyVY += ay
  smileyCenterX += smileyVX
  smileyCenterY += smileyVY

  // 检测从聚合→散开的切换，触发爆发扩散
  const scatterBurst = wasTargetMode && !targetMode
  const gatherStart = !wasTargetMode && targetMode
  wasTargetMode = targetMode

  // 开始聚合时重置弹簧位置到鼠标
  if (gatherStart) {
    smileyCenterX = mouseX
    smileyCenterY = mouseY
    smileyVX = 0
    smileyVY = 0
  }

  for (const p of particles) {
    if (targetMode) {
      p.gatherProgress = Math.min(1, p.gatherProgress + speed)
    } else {
      p.gatherProgress = Math.max(0, p.gatherProgress - speed * 1.5)
      // 散开瞬间给爆发速度
      if (scatterBurst) {
        // 随机方向爆发，覆盖全屏
        const angle = Math.random() * Math.PI * 2
        const force = 4 + Math.random() * 8
        p.vx = Math.cos(angle) * force
        p.vy = Math.sin(angle) * force
      }
    }

    const t = easeInOutCubic(p.gatherProgress)
    const target = getSmileyTarget(p)

    if (targetMode) {
      // lerp 到目标位置
      p.x += (target.x - p.x) * 0.06
      p.y += (target.y - p.y) * 0.06
    } else {
      p.x += p.vx
      p.y += p.vy
      // 边界反弹
      if (p.x < 0 || p.x > canvas.value.width) p.vx *= -1
      if (p.y < 0 || p.y > canvas.value.height) p.vy *= -1
      // 阻尼衰减
      p.vx *= 0.995
      p.vy *= 0.995
      // 随机轻微扰动
      p.vx += (Math.random() - 0.5) * 0.05
      p.vy += (Math.random() - 0.5) * 0.05
    }
  }
}

function drawParticles() {
  ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)

  for (const p of particles) {
    const alpha = targetMode
      ? p.opacity * (0.5 + p.gatherProgress * 0.5)
      : p.opacity * 0.5

    ctx.beginPath()
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)

    if (targetMode && p.gatherProgress > 0.3) {
      if (currentIcon === 'sun') {
        // 太阳：暖金色
        const r = Math.round(255)
        const g = Math.round(180 + p.gatherProgress * 75)
        const b = Math.round(30 + (1 - p.gatherProgress) * 30)
        ctx.fillStyle = `rgba(${r},${g},${b},${alpha})`
      } else {
        // 月亮：银蓝
        const v = Math.round(180 + p.gatherProgress * 75)
        ctx.fillStyle = `rgba(${v},${v + 40},${Math.round(v + 75)},${alpha})`
      }
    } else {
      ctx.fillStyle = `rgba(96,130,255,${alpha})`
    }
    ctx.fill()
  }
}

function easeInOutCubic(t) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
}

function animate() {
  updateParticles()
  drawParticles()
  animationId = requestAnimationFrame(animate)
}

function resize() {
  nextTick(() => {
    if (!canvas.value) return
    canvas.value.width = window.innerWidth
    canvas.value.height = window.innerHeight
    refreshIconPoints()
    for (const p of particles) {
      p.targetIndex = Math.floor(Math.random() * smileyPoints.length)
    }
  })
}

function onMouseMove(e) {
  mouseX = e.clientX
  mouseY = e.clientY
  targetMode = true
  // 重置离开计时器
  clearTimeout(leaveTimer)
  leaveTimer = setTimeout(() => {
    targetMode = false
  }, LEAVE_DELAY)
}

function onMouseLeave() {
  targetMode = false
  clearTimeout(leaveTimer)
}

function onMouseEnter() {
  targetMode = true
  clearTimeout(leaveTimer)
}

onMounted(() => {
  nextTick(() => {
    if (!canvas.value) return
    ctx = canvas.value.getContext('2d')
    canvas.value.width = window.innerWidth
    canvas.value.height = window.innerHeight
    refreshIconPoints()
    initParticles()
    animate()
  })
  window.addEventListener('resize', resize)
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseleave', onMouseLeave)
  document.addEventListener('mouseenter', onMouseEnter)
  document.addEventListener('mouseout', (e) => {
    // 鼠标移出 document 时散开
    if (!e.relatedTarget || e.relatedTarget.nodeName === 'HTML') {
      targetMode = false
      clearTimeout(leaveTimer)
    }
  })
})

onUnmounted(() => {
  cancelAnimationFrame(animationId)
  clearTimeout(leaveTimer)
  window.removeEventListener('resize', resize)
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseleave', onMouseLeave)
  document.removeEventListener('mouseenter', onMouseEnter)
})
</script>
