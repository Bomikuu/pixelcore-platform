<template>
  <!-- DESIGN_CONTRACT: editorial asymmetric hero; voxel core expresses one shared record system feeding Site, Sell, Schedule, and Operate. -->
  <div ref="root" class="core-stage" aria-label="A living pixel core connecting the four PixelCore capabilities">
    <canvas ref="canvas" class="core-canvas" :class="{ 'is-ready': ready }" aria-hidden="true" />
    <svg class="core-fallback" :class="{ 'is-hidden': ready }" viewBox="0 0 680 620" role="img" aria-labelledby="core-title core-description">
      <title id="core-title">The PixelCore operating system</title>
      <desc id="core-description">A central modular core connects Site, Sell, Schedule, and Operate.</desc>
      <g fill="none" stroke="currentColor" stroke-width="2"><path d="M340 308H108V130" /><path d="M340 308H572V130" /><path d="M340 308H108V490" /><path d="M340 308H572V490" /></g>
      <g fill="currentColor"><rect x="270" y="238" width="56" height="56" /><rect x="332" y="238" width="56" height="56" opacity=".72" /><rect x="270" y="300" width="56" height="56" opacity=".72" /><rect x="332" y="300" width="56" height="56" /><rect x="301" y="207" width="56" height="25" opacity=".42" /><rect x="301" y="362" width="56" height="25" opacity=".42" /></g>
      <g fill="currentColor"><rect x="92" y="114" width="32" height="32" /><rect x="556" y="114" width="32" height="32" /><rect x="92" y="474" width="32" height="32" /><rect x="556" y="474" width="32" height="32" /></g>
    </svg>
    <div class="signal-label signal-site"><span>01</span> Site</div><div class="signal-label signal-sell"><span>02</span> Sell</div>
    <div class="signal-label signal-schedule"><span>03</span> Schedule</div><div class="signal-label signal-operate"><span>04</span> Operate</div>
    <p class="core-caption">One source of truth. Four ways to move the business.</p>
  </div>
</template>

<script setup>
const root = ref(null)
const canvas = ref(null)
const ready = ref(false)
let cleanup = () => {}

onMounted(async () => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || !canvas.value || !root.value) return
  let stopped = false; let frame = 0; let observer; let resizeObserver; let renderer; let scene; let camera; let core; let signals
  let visible = true; let pointerX = 0; let pointerY = 0
  const initTimer = window.setTimeout(() => { if (!ready.value) stopped = true }, 5000)
  try {
    const THREE = await import('three')
    if (stopped) return
    renderer = new THREE.WebGLRenderer({ canvas: canvas.value, antialias: true, alpha: true, powerPreference: 'high-performance' })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75)); renderer.outputColorSpace = THREE.SRGBColorSpace
    scene = new THREE.Scene(); camera = new THREE.PerspectiveCamera(34, 1, 0.1, 100); camera.position.set(0, 0.1, 8.8)
    scene.add(new THREE.AmbientLight(0xffffff, 1.4))
    const key = new THREE.DirectionalLight(0xf4b34a, 5.2); key.position.set(-3, 4, 5); scene.add(key)
    const edge = new THREE.DirectionalLight(0x45c8ad, 3.6); edge.position.set(4, -2, 3); scene.add(edge)
    core = new THREE.Group(); scene.add(core)
    const cubeGeometry = new THREE.BoxGeometry(0.42, 0.42, 0.42)
    const cubeMaterial = new THREE.MeshStandardMaterial({ color: 0xf4efe4, roughness: 0.36, metalness: 0.14 })
    const cubes = new THREE.InstancedMesh(cubeGeometry, cubeMaterial, 98); const matrix = new THREE.Matrix4(); let instance = 0
    for (let x = -2; x <= 2; x += 1) for (let y = -2; y <= 2; y += 1) for (let z = -2; z <= 2; z += 1) {
      if (Math.abs(x) + Math.abs(y) + Math.abs(z) > 4 || (x + y + z) % 4 === 0) continue
      const scale = 0.78 + ((x * x + y * 3 + z * 5 + 20) % 5) * 0.045
      matrix.compose(new THREE.Vector3(x * 0.48, y * 0.48, z * 0.48), new THREE.Quaternion(), new THREE.Vector3(scale, scale, scale)); cubes.setMatrixAt(instance, matrix); instance += 1
    }
    cubes.count = instance; cubes.instanceMatrix.needsUpdate = true; core.add(cubes)
    signals = new THREE.Group(); scene.add(signals)
    const signalGeometry = new THREE.BoxGeometry(0.14, 0.14, 0.14); const colors = [0x55bea8, 0xe9a33b, 0x8fb9e8, 0xe38270]; const directions = [[-1, 1], [1, 1], [-1, -1], [1, -1]]
    directions.forEach(([dx, dy], pathIndex) => {
      const material = new THREE.MeshStandardMaterial({ color: colors[pathIndex], roughness: 0.42 }); const path = new THREE.InstancedMesh(signalGeometry, material, 15)
      for (let index = 0; index < 15; index += 1) { const progress = (index + 1) / 15; const x = dx * (1.15 * Math.min(progress * 2, 1) + 1.5 * Math.max(progress - 0.5, 0) * 2); const y = dy * (1.48 * Math.max(progress - 0.42, 0) * 1.72); matrix.makeTranslation(x, y, 0.12 * Math.sin(index * 0.8 + pathIndex)); path.setMatrixAt(index, matrix) }
      path.instanceMatrix.needsUpdate = true; signals.add(path)
    })
    const resize = () => { const bounds = root.value.getBoundingClientRect(); const width = Math.max(1, bounds.width); const height = Math.max(1, bounds.height); renderer.setSize(width, height, false); camera.aspect = width / height; camera.updateProjectionMatrix() }
    resizeObserver = new ResizeObserver(resize); resizeObserver.observe(root.value); resize()
    observer = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting }, { rootMargin: '120px' }); observer.observe(root.value)
    const onPointer = (event) => { const bounds = root.value.getBoundingClientRect(); pointerX = ((event.clientX - bounds.left) / bounds.width - 0.5) * 0.28; pointerY = ((event.clientY - bounds.top) / bounds.height - 0.5) * 0.2 }
    root.value.addEventListener('pointermove', onPointer, { passive: true })
    const start = performance.now()
    const render = (time) => { if (stopped) return; if (visible && !document.hidden) { const elapsed = (time - start) / 1000; const scrollInfluence = Math.min(window.scrollY / Math.max(window.innerHeight, 1), 1) * 0.16; core.rotation.y += (pointerX + elapsed * 0.075 + scrollInfluence - core.rotation.y) * 0.035; core.rotation.x += (-pointerY + Math.sin(elapsed * 0.42) * 0.035 - core.rotation.x) * 0.04; signals.rotation.z = Math.sin(elapsed * 0.22) * 0.018; renderer.render(scene, camera) } frame = requestAnimationFrame(render) }
    frame = requestAnimationFrame(render); window.clearTimeout(initTimer); ready.value = true
    cleanup = () => { stopped = true; cancelAnimationFrame(frame); observer?.disconnect(); resizeObserver?.disconnect(); root.value?.removeEventListener('pointermove', onPointer); scene?.traverse((object) => { object.geometry?.dispose?.(); if (Array.isArray(object.material)) object.material.forEach((material) => material.dispose()); else object.material?.dispose?.() }); renderer?.dispose(); renderer?.forceContextLoss() }
  } catch { window.clearTimeout(initTimer); ready.value = false }
})

onBeforeUnmount(() => cleanup())
</script>

<style scoped>
.core-stage { position: relative; min-height: 34rem; overflow: hidden; border-left: 1px solid hsl(var(--border)); color: hsl(var(--primary)); background: hsl(var(--card)); }
.core-stage::before { content: ''; position: absolute; inset: 0; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 40 40'%3E%3Cpath d='M0 0H40M0 0V40' fill='none' stroke='%2391a09d' stroke-opacity='.22'/%3E%3C/svg%3E"); opacity: .6; pointer-events: none; }
.core-canvas, .core-fallback { position: absolute; inset: 0; width: 100%; height: 100%; transition: opacity .35s ease; }.core-canvas { opacity: 0; }.core-canvas.is-ready { opacity: 1; }.core-fallback { padding: 3rem; }.core-fallback.is-hidden { opacity: 0; }
.signal-label { position: absolute; display: flex; align-items: center; gap: .55rem; font-size: .72rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; color: hsl(var(--foreground)); }.signal-label span { color: hsl(var(--muted-foreground)); font-variant-numeric: tabular-nums; }
.signal-site { left: 5%; top: 10%; }.signal-sell { right: 5%; top: 10%; }.signal-schedule { left: 5%; bottom: 13%; }.signal-operate { right: 5%; bottom: 13%; }
.core-caption { position: absolute; bottom: 1.15rem; left: 50%; width: max-content; max-width: 78%; transform: translateX(-50%); font-size: .72rem; color: hsl(var(--muted-foreground)); }
@media (max-width: 767px) { .core-stage { min-height: 27rem; border-left: 0; border-top: 1px solid hsl(var(--border)); }.core-fallback { padding: 2rem 1rem 3rem; } }
@media (prefers-reduced-motion: reduce) { .core-canvas { display: none; }.core-fallback { opacity: 1 !important; transition: none; } }
</style>
