<template>
  <section
    ref="surface"
    class="relative isolate min-h-[var(--hero-height)] overflow-hidden bg-foreground text-white"
    :style="{ '--hero-height': heroHeight }"
    aria-roledescription="carousel"
    aria-label="Featured stories"
    @mouseenter="hovered = true"
    @mouseleave="hovered = false"
    @focusin="focused = true"
    @focusout="focused = Boolean($event.currentTarget.contains($event.relatedTarget))"
  >
    <Transition name="custom-hero" mode="out-in">
      <div :key="active.id" class="absolute inset-0" :style="{ backgroundColor: active.background_color }">
        <img
          v-if="active.type === 'image' && asset(active.asset_id)"
          :src="asset(active.asset_id).url"
          :alt="asset(active.asset_id).alt_text || ''"
          class="h-full w-full object-cover"
        />
        <video
          v-else-if="active.type === 'video' && asset(active.asset_id) && !reducedMotion"
          ref="video"
          :src="asset(active.asset_id).url"
          :poster="asset(active.poster_asset_id)?.url"
          muted
          loop
          playsinline
          preload="metadata"
          class="h-full w-full object-cover"
          @loadeddata="syncVideo"
          @error="videoFailed = true"
        />
        <ClientOnly v-else-if="['model', 'particles'].includes(active.type) && !reducedMotion">
          <ThreeScene
            :key="active.id"
            class="h-full min-h-full rounded-none"
            :kind="active.type === 'model' ? 'product_model' : 'particle_scene'"
            :settings="sceneSettings"
            :paused="paused"
            :asset-url="asset(active.asset_id)?.url || ''"
            :poster-url="asset(active.poster_asset_id)?.url || ''"
          />
          <template #fallback>
            <img v-if="asset(active.poster_asset_id)" :src="asset(active.poster_asset_id).url" alt="" class="h-full w-full object-cover" />
          </template>
        </ClientOnly>
        <img v-else-if="asset(active.poster_asset_id)" :src="asset(active.poster_asset_id).url" alt="" class="h-full w-full object-cover" />
        <img v-if="videoFailed && asset(active.poster_asset_id)" :src="asset(active.poster_asset_id).url" alt="" class="absolute inset-0 h-full w-full object-cover" />
      </div>
    </Transition>
    <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/85 via-black/35 to-black/10" />
    <div
      class="pointer-events-none relative z-10 flex min-h-[var(--hero-height)] px-5 sm:px-10 lg:px-16"
      :class="centerContent ? 'items-center justify-center py-24 text-center' : 'items-end pb-28 pt-20'"
    >
      <div
        class="pointer-events-auto"
        :class="centerContent ? 'flex w-full max-w-4xl flex-col items-center' : 'max-w-3xl'"
      >
        <h1
          class="text-balance font-semibold leading-[1.02] tracking-[-0.03em]"
          :class="[mode === 'luxury' ? 'display-face' : '', height === 'screen' ? 'text-5xl sm:text-6xl lg:text-8xl' : 'text-3xl sm:text-5xl lg:text-6xl']"
        >{{ active.heading || heading }}</h1>
        <p v-if="active.body || body" class="mt-5 max-w-xl text-base leading-7 text-white/85">{{ active.body || body }}</p>
        <ButtonAnchor
          v-if="active.label && active.path"
          :href="`${base}${active.path === '/' ? '' : active.path}`"
          variant="secondary"
          size="lg"
          class="mt-6 gap-2 bg-white text-black hover:bg-white/90"
          @click="preview && $event.preventDefault()"
        >
          {{ active.label }}<ArrowUpRight class="h-4 w-4" aria-hidden="true" />
        </ButtonAnchor>
        <slot name="content" />
      </div>
    </div>
    <div class="absolute inset-x-5 bottom-5 z-20 flex flex-wrap items-center justify-between gap-3 sm:inset-x-10 lg:inset-x-16">
      <div v-if="slides.length > 1" class="flex items-center gap-1" aria-label="Choose a slide">
        <Button
          v-for="(slide, slideIndex) in slides"
          :key="slide.id"
          type="button"
          variant="ghost"
          size="icon"
          class="h-9 w-9 text-white hover:bg-white/15 hover:text-white"
          :aria-label="`Show slide ${slideIndex + 1}: ${slide.heading || 'Featured story'}`"
          :aria-pressed="index === slideIndex"
          @click="goTo(slideIndex)"
        >
          <span class="h-2 rounded-full bg-white" :class="index === slideIndex ? 'w-6' : 'w-2 opacity-50'" />
        </Button>
      </div>
      <div class="ml-auto flex items-center gap-2">
        <span v-if="slides.length > 1" class="mr-2 text-xs tabular-nums">{{ index + 1 }} / {{ slides.length }}</span>
        <Button
          v-if="!reducedMotion && (autoplay || active.type !== 'image')"
          type="button"
          variant="outline"
          size="icon"
          class="border-white/40 bg-black/20 text-white hover:bg-white hover:text-black"
          :aria-label="stopped ? 'Play hero' : 'Pause hero'"
          @click="stopped = !stopped"
        >
          <Play v-if="stopped" class="h-4 w-4" aria-hidden="true" />
          <Pause v-else class="h-4 w-4" aria-hidden="true" />
        </Button>
        <template v-if="slides.length > 1">
          <Button type="button" variant="outline" size="icon" class="border-white/40 bg-black/20 text-white hover:bg-white hover:text-black" aria-label="Previous slide" @click="move(-1)">
            <ChevronLeft class="h-4 w-4" aria-hidden="true" />
          </Button>
          <Button type="button" variant="outline" size="icon" class="border-white/40 bg-black/20 text-white hover:bg-white hover:text-black" aria-label="Next slide" @click="move(1)">
            <ChevronRight class="h-4 w-4" aria-hidden="true" />
          </Button>
        </template>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ArrowUpRight, ChevronLeft, ChevronRight, Pause, Play } from 'lucide-vue-next'
import ThreeScene from './ThreeScene.vue'

const props = defineProps({
  slides: { type: Array, required: true },
  assets: { type: Object, default: () => ({}) },
  base: { type: String, default: '' },
  heading: { type: String, default: '' },
  body: { type: String, default: '' },
  mode: { type: String, default: 'default' },
  autoplay: { type: Boolean, default: true },
  height: { type: String, default: 'screen' },
  interval: { type: Number, default: 7 },
  preview: { type: Boolean, default: false },
  centerContent: { type: Boolean, default: false },
})
const surface = ref(null)
const video = ref(null)
const index = ref(0)
const stopped = ref(false)
const hovered = ref(false)
const focused = ref(false)
const hidden = ref(false)
const offscreen = ref(false)
const reducedMotion = ref(false)
const videoFailed = ref(false)
const heroHeight = computed(() => ({
  compact: '24rem',
  medium: '32rem',
  tall: '42rem',
  screen: 'calc(100svh - 4.5rem)',
}[props.height] || '32rem'))
const active = computed(() => props.slides[index.value] || props.slides[0] || {})
const paused = computed(() => stopped.value || hidden.value || offscreen.value || reducedMotion.value)
const asset = (id) => props.assets[id]
const sceneSettings = computed(() => ({
  motion: active.value.motion || 'subtle',
  background_color: active.value.background_color || '#17362F',
  particle_count: 400,
  speed: 0.35,
}))
let timer
let observer
let mediaQuery

function syncVideo() {
  if (!video.value) return
  if (paused.value) video.value.pause()
  else video.value.play().catch(() => {})
}
function goTo(value) {
  index.value = value
  videoFailed.value = false
}
function move(step) {
  if (!props.slides.length) return
  goTo((index.value + step + props.slides.length) % props.slides.length)
}
function visibility() { hidden.value = document.hidden }
function preference() { reducedMotion.value = mediaQuery.matches }
function startTimer() {
  clearInterval(timer)
  timer = setInterval(() => {
    if (props.autoplay && props.slides.length > 1 && !paused.value && !hovered.value && !focused.value) move(1)
  }, Math.max(4, Math.min(30, props.interval)) * 1000)
}
watch(paused, syncVideo)
watch(video, syncVideo)
watch(() => props.slides.length, () => { index.value = 0 })
watch(() => props.interval, () => { if (import.meta.client) startTimer() })
onMounted(() => {
  mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  preference()
  mediaQuery.addEventListener('change', preference)
  visibility()
  document.addEventListener('visibilitychange', visibility)
  observer = new IntersectionObserver(([entry]) => { offscreen.value = !entry.isIntersecting })
  observer.observe(surface.value)
  startTimer()
})
onBeforeUnmount(() => {
  clearInterval(timer)
  observer?.disconnect()
  mediaQuery?.removeEventListener('change', preference)
  document.removeEventListener('visibilitychange', visibility)
  video.value?.pause()
})
</script>

<style scoped>
.custom-hero-enter-active,
.custom-hero-leave-active {
  transition: opacity 240ms ease;
}
.custom-hero-enter-from,
.custom-hero-leave-to {
  opacity: 0;
}
@media (prefers-reduced-motion: reduce) {
  .custom-hero-enter-active,
  .custom-hero-leave-active {
    transition: none;
  }
}
</style>
