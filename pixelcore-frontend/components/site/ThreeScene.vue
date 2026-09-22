<template>
  <div ref="container" class="relative min-h-[20rem] overflow-hidden rounded-[var(--radius)] bg-secondary" :style="backgroundStyle" aria-label="Decorative 3D scene">
    <img v-if="posterUrl" :src="posterUrl" alt="" class="absolute inset-0 h-full w-full object-cover transition-opacity" :class="ready ? 'opacity-0' : 'opacity-100'" />
    <div v-else-if="!ready" class="absolute inset-0 flex items-center justify-center text-sm font-semibold text-muted-foreground">3D preview loads when a model or particle scene is configured.</div>
    <canvas ref="canvas" class="absolute inset-0 h-full w-full" :class="ready ? 'opacity-100' : 'opacity-0'" aria-hidden="true" />
  </div>
</template>

<script setup>
const props = defineProps({
  kind: { type: String, default: 'three_hero' },
  settings: { type: Object, required: true },
  assetUrl: { type: String, default: '' },
  posterUrl: { type: String, default: '' },
  paused: { type: Boolean, default: false },
})
const container = ref(null)
const canvas = ref(null)
const ready = ref(false)
let cleanup = () => {}
let disposed = false
let resumeAnimation = () => {}
watch(() => props.paused, () => resumeAnimation())
const backgroundStyle = computed(() => ({ backgroundColor: props.settings.background_color || 'var(--brand-secondary)' }))

onMounted(async () => {
  if (!canvas.value || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  let THREE
  let renderer
  try {
    THREE = await import('three')
    if (disposed) return
    renderer = new THREE.WebGLRenderer({ canvas: canvas.value, antialias: true, alpha: true, powerPreference: 'low-power' })
  } catch { return }
  cleanup = () => renderer.dispose()
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5))
  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100)
  const cameraSettings = props.settings.camera || {}
  camera.position.set(Number(cameraSettings.x || 0), Number(cameraSettings.y || 0.4), Number(cameraSettings.z || 4.5))
  const ambient = new THREE.AmbientLight(0xffffff, Math.min(Number(props.settings.lighting?.ambient || 1.2), 2))
  const key = new THREE.DirectionalLight(0xffffff, Math.min(Number(props.settings.lighting?.key || 1.8), 3))
  key.position.set(3, 4, 5)
  scene.add(ambient, key)
  let subject
  if (props.kind === 'particle_scene') {
    const count = Math.min(Math.max(Number(props.settings.particle_count || 300), 1), 1500)
    const positions = new Float32Array(count * 3)
    for (let index = 0; index < positions.length; index += 3) {
      positions[index] = (Math.random() - 0.5) * 5
      positions[index + 1] = (Math.random() - 0.5) * 3
      positions[index + 2] = (Math.random() - 0.5) * 2
    }
    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    subject = new THREE.Points(geometry, new THREE.PointsMaterial({ color: props.settings.colors?.[0] || 0xd8922b, size: 0.035 }))
    scene.add(subject)
  } else if (props.assetUrl) {
    const { GLTFLoader } = await import('three/examples/jsm/loaders/GLTFLoader.js')
    if (disposed) return
    try {
      const gltf = await new GLTFLoader().loadAsync(props.assetUrl)
      if (disposed) { disposeObject(gltf.scene); return }
      let triangles = 0
      gltf.scene.traverse((node) => { if (node.isMesh) triangles += node.geometry.index ? node.geometry.index.count / 3 : node.geometry.attributes.position.count / 3 })
      if (triangles > 200000) { disposeObject(gltf.scene); throw new Error('Model exceeds the client complexity limit.') }
      subject = gltf.scene
      scene.add(subject)
    } catch { renderer.dispose(); return }
  } else {
    subject = new THREE.Mesh(new THREE.IcosahedronGeometry(1.1, 2), new THREE.MeshStandardMaterial({ color: 0x1c786a, roughness: 0.5, metalness: 0.15 }))
    scene.add(subject)
  }
  const resize = () => {
    const bounds = container.value.getBoundingClientRect()
    renderer.setSize(bounds.width, bounds.height, false)
    camera.aspect = bounds.width / Math.max(bounds.height, 1)
    camera.updateProjectionMatrix()
  }
  const observer = new ResizeObserver(resize)
  observer.observe(container.value)
  let frame
  let inViewport = true
  let pageVisible = !document.hidden
  const speed = Math.min(Number(props.settings.speed || 0.35), 1.5)
  const draw = () => {
    if (!inViewport || !pageVisible || props.paused) { frame = undefined; return }
    if (subject && props.settings.motion !== 'none') subject.rotation.y += 0.0025 * speed
    renderer.render(scene, camera)
    frame = requestAnimationFrame(draw)
  }
  const resume = () => { if (!frame && inViewport && pageVisible) frame = requestAnimationFrame(draw) }
  resumeAnimation = resume
  const visibilityObserver = new IntersectionObserver(([entry]) => { inViewport = entry.isIntersecting; if (!inViewport && frame) { cancelAnimationFrame(frame); frame = undefined } else resume() }, { rootMargin: '120px' })
  visibilityObserver.observe(container.value)
  const onVisibility = () => { pageVisible = !document.hidden; if (!pageVisible && frame) { cancelAnimationFrame(frame); frame = undefined } else resume() }
  document.addEventListener('visibilitychange', onVisibility)
  const onPointerMove = (event) => {
    if (!subject || props.settings.motion !== 'interactive') return
    const bounds = container.value.getBoundingClientRect()
    subject.rotation.x = Math.max(-0.18, Math.min(0.18, ((event.clientY - bounds.top) / bounds.height - 0.5) * 0.22))
    subject.rotation.y += Math.max(-0.01, Math.min(0.01, ((event.clientX - bounds.left) / bounds.width - 0.5) * 0.012))
  }
  container.value.addEventListener('pointermove', onPointerMove, { passive: true })
  resize()
  renderer.render(scene, camera)
  ready.value = true
  draw()
  cleanup = () => {
    if (frame) cancelAnimationFrame(frame)
    observer.disconnect()
    visibilityObserver.disconnect()
    document.removeEventListener('visibilitychange', onVisibility)
    container.value?.removeEventListener('pointermove', onPointerMove)
    scene.traverse((node) => {
      node.geometry?.dispose?.()
      const materials = Array.isArray(node.material) ? node.material : node.material ? [node.material] : []
      for (const material of materials) {
        for (const value of Object.values(material)) if (value?.isTexture) value.dispose()
        material.dispose?.()
      }
    })
    renderer.renderLists?.dispose?.()
    renderer.dispose()
    renderer.forceContextLoss?.()
  }
})

function disposeObject(root) {
  root.traverse((node) => { node.geometry?.dispose?.(); const materials = Array.isArray(node.material) ? node.material : node.material ? [node.material] : []; for (const material of materials) { for (const value of Object.values(material)) if (value?.isTexture) value.dispose(); material.dispose?.() } })
}
onBeforeUnmount(() => { disposed = true; cleanup() })
</script>
