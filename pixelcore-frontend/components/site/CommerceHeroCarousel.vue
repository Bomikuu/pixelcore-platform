<template>
  <CustomHeroCarousel v-if="settings.slides?.length" :slides="settings.slides" :assets="assets" :base="siteBase" :heading="settings.heading" :body="settings.body" :mode="mode" :autoplay="settings.autoplay !== false" />
  <section
    v-else
    class="relative min-h-[calc(100dvh-4.5rem)] overflow-hidden text-white"
    :class="isLuxury ? 'bg-black' : 'bg-[var(--brand-secondary)]'"
    aria-roledescription="carousel"
    aria-label="Featured products"
    @mouseenter="paused = true"
    @mouseleave="paused = false"
    @focusin="paused = true"
    @focusout="paused = false"
  >
    <Transition name="commerce-hero" mode="out-in">
      <div
        :key="activeSlide?.id || 'empty'"
        class="min-h-[calc(100dvh-4.5rem)]"
        :class="isLuxury ? 'relative' : 'grid lg:grid-cols-[0.78fr_1.22fr] lg:items-stretch'"
      >
        <div
          class="relative z-10 flex flex-col px-6 sm:px-10 lg:px-16"
          :class="isLuxury ? 'min-h-[calc(100dvh-4.5rem)] justify-end pb-28 pt-32 lg:px-[clamp(3rem,6vw,7rem)] lg:pb-32' : 'justify-center py-16 lg:py-20'"
        >
          <p v-if="isLuxury" class="text-xs font-semibold uppercase tracking-[0.22em] text-white/70">Featured selection</p>
          <h1 class="display-face max-w-3xl text-5xl font-semibold leading-[0.96] tracking-[-0.03em] sm:text-6xl" :class="isLuxury ? 'mt-4 lg:text-8xl' : 'lg:text-7xl'">{{ activeSlide?.heading || settings.heading }}</h1>
          <p class="mt-5 max-w-xl text-base leading-7 text-white/75">{{ activeSlide?.body || settings.body }}</p>
          <div class="mt-8 flex flex-wrap gap-3">
            <ButtonAnchor v-if="activeSlide?.primaryLabel" :href="activeSlide.primaryHref" class="bg-white text-foreground hover:bg-white/90">{{ activeSlide.primaryLabel }}</ButtonAnchor>
            <ButtonAnchor v-if="activeIndex === 0 && settings.secondary_label" :href="basePath(settings.secondary_path)" variant="outline" class="border-white/40 bg-transparent text-white hover:bg-white hover:text-foreground">{{ settings.secondary_label }}</ButtonAnchor>
          </div>
        </div>

        <div class="overflow-hidden bg-secondary" :class="isLuxury ? 'absolute inset-0 min-h-full' : 'relative min-h-[25rem]'">
          <ClientOnly v-if="slides.length === 1 && activeSlide?.model">
            <ThreeScene class="h-full min-h-[25rem] rounded-none" kind="product_model" :settings="sceneSettings" :asset-url="activeSlide.model.url" :poster-url="activeSlide.poster?.url || activeSlide.image?.url" />
            <template #fallback><img v-if="activeSlide.poster || activeSlide.image" :src="(activeSlide.poster || activeSlide.image).url" :alt="(activeSlide.poster || activeSlide.image).alt_text || activeSlide.heading" class="h-full w-full object-cover" /></template>
          </ClientOnly>
          <img v-else-if="activeSlide?.image" :src="activeSlide.image.url" :alt="activeSlide.image.alt_text || activeSlide.heading" class="absolute inset-0 h-full w-full object-cover" />
          <div v-else class="flex h-full items-center justify-center p-12 text-center font-semibold text-muted-foreground">Add product photography to complete this hero.</div>
          <div class="pointer-events-none absolute inset-0" :class="isLuxury ? 'bg-[linear-gradient(90deg,rgba(0,0,0,0.68)_0%,rgba(0,0,0,0.18)_55%,rgba(0,0,0,0.04)_80%),linear-gradient(0deg,rgba(0,0,0,0.45)_0%,transparent_50%)]' : 'bg-gradient-to-t from-black/25 via-transparent to-transparent lg:bg-gradient-to-r lg:from-black/10 lg:via-transparent'" />
        </div>
      </div>
    </Transition>

    <div v-if="slides.length > 1" class="absolute inset-x-0 bottom-0 z-20 flex items-center justify-between gap-4 border-t border-white/15 px-5 py-4 backdrop-blur-sm sm:px-10" :class="isLuxury ? 'bg-black/10 lg:px-[clamp(3rem,6vw,7rem)]' : 'bg-black/20 lg:px-16'">
      <div class="flex items-center gap-2" aria-label="Choose featured product">
        <Button
          v-for="(slide, index) in slides"
          :key="slide.id"
          type="button"
          variant="ghost"
          size="icon"
          class="h-8 w-8 text-white hover:bg-white/15 hover:text-white"
          :aria-label="`Show slide ${index + 1}: ${slide.heading}`"
          :aria-current="index === activeIndex ? 'true' : undefined"
          @click="goTo(index)"
        >
          <span class="h-1.5 rounded-full bg-current transition-all" :class="index === activeIndex ? 'w-6' : 'w-2 opacity-50'" />
        </Button>
      </div>
      <div class="flex items-center gap-2">
        <span class="mr-2 text-xs font-bold tabular-nums text-white/70">{{ String(activeIndex + 1).padStart(2, '0') }} / {{ String(slides.length).padStart(2, '0') }}</span>
        <Button type="button" variant="outline" size="icon" class="border-white/30 bg-transparent text-white hover:bg-white hover:text-foreground" aria-label="Previous featured product" @click="previous"><ChevronLeft class="h-4 w-4" /></Button>
        <Button type="button" variant="outline" size="icon" class="border-white/30 bg-transparent text-white hover:bg-white hover:text-foreground" aria-label="Next featured product" @click="next"><ChevronRight class="h-4 w-4" /></Button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
import CustomHeroCarousel from './CustomHeroCarousel.vue'

const props = defineProps({ settings: { type: Object, required: true }, offerings: { type: Array, default: () => [] }, assets: { type: Object, default: () => ({}) }, siteBase: { type: String, default: '' }, mode: { type: String, default: 'default' } })
const activeIndex = ref(0)
const paused = ref(false)
const reducedMotion = ref(false)
let timer = null
const isLuxury = computed(() => props.mode === 'luxury')

const requestedIds = computed(() => {
  if (Array.isArray(props.settings.offering_ids) && props.settings.offering_ids.length) return props.settings.offering_ids
  return props.settings.offering_id ? [props.settings.offering_id] : []
})
const slides = computed(() => requestedIds.value.map((id, index) => {
  const offering = props.offerings.find((item) => item.public_id === id)
  if (!offering) return null
  const media = offering.ordered_media || []
  const images = media.filter((item) => ['cover', 'gallery'].includes(item.role))
  const image = images[0] || offering.media?.[0] || null
  return {
    id: offering.public_id,
    heading: index === 0 && props.settings.heading ? props.settings.heading : offering.name,
    body: index === 0 && props.settings.body ? props.settings.body : (offering.summary || offering.description),
    primaryLabel: index === 0 && props.settings.primary_label ? props.settings.primary_label : `View ${offering.name}`,
    primaryHref: index === 0 && props.settings.primary_path ? basePath(props.settings.primary_path) : `${props.siteBase}/product/${offering.slug}`,
    image,
    model: media.find((item) => item.role === 'model'),
    poster: media.find((item) => item.role === 'poster'),
  }
}).filter(Boolean))
const activeSlide = computed(() => slides.value[activeIndex.value] || null)
const sceneSettings = { motion: 'interactive', speed: 0.35, background_color: '#f1efe8', camera: { x: 0, y: 0.3, z: 4.2 }, lighting: { ambient: 1.2, key: 1.8 } }
const basePath = (path) => path ? `${props.siteBase}${path === '/' ? '' : path}` : props.siteBase

function goTo(index) { activeIndex.value = index; restartTimer() }
function previous() { goTo((activeIndex.value - 1 + slides.value.length) % slides.value.length) }
function next() { goTo((activeIndex.value + 1) % slides.value.length) }
function stopTimer() { if (timer) window.clearInterval(timer); timer = null }
function startTimer() {
  stopTimer()
  if (slides.value.length < 2 || reducedMotion.value || props.settings.autoplay === false) return
  timer = window.setInterval(() => { if (!paused.value && !document.hidden) activeIndex.value = (activeIndex.value + 1) % slides.value.length }, 6500)
}
function restartTimer() { if (import.meta.client) startTimer() }

onMounted(() => {
  reducedMotion.value = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  startTimer()
})
onBeforeUnmount(stopTimer)
watch(slides, () => { if (activeIndex.value >= slides.value.length) activeIndex.value = 0; restartTimer() })
</script>

<style scoped>
.commerce-hero-enter-active,
.commerce-hero-leave-active { transition: opacity 280ms ease; }
.commerce-hero-enter-from,
.commerce-hero-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) {
  .commerce-hero-enter-active,
  .commerce-hero-leave-active { transition: none; }
}
</style>
