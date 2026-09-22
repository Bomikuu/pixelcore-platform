<template>
  <CustomHeroCarousel v-if="heroSettings.slides?.length" :slides="heroSettings.slides" :assets="customAssets" :base="base" :heading="collection.name" :body="collection.description" :mode="mode" :autoplay="heroSettings.autoplay !== false" />
  <section
    v-else
    class="relative isolate min-h-[calc(100svh-4.5rem)] overflow-hidden bg-foreground text-background"
    aria-roledescription="carousel"
    :aria-label="`${collection.name} highlights`"
    @mouseenter="paused = true"
    @mouseleave="paused = false"
    @focusin="paused = true"
    @focusout="paused = false"
  >
    <Transition name="luxury-hero" mode="out-in">
      <div :key="activeSlide?.id || collection.slug" class="absolute inset-0">
        <img
          v-if="activeSlide?.image || collection.cover_url"
          :src="activeSlide?.image?.url || collection.cover_url"
          :alt="activeSlide?.image?.alt_text || activeSlide?.name || collection.name"
          class="h-full w-full object-cover"
        />
        <div v-else class="h-full w-full bg-[linear-gradient(135deg,hsl(var(--foreground)),hsl(var(--foreground)/0.76))]" />
      </div>
    </Transition>

    <div class="pointer-events-none absolute inset-0 bg-[linear-gradient(90deg,rgba(0,0,0,0.72)_0%,rgba(0,0,0,0.28)_48%,rgba(0,0,0,0.05)_75%),linear-gradient(0deg,rgba(0,0,0,0.42)_0%,transparent_45%)]" />

    <div class="relative z-10 flex min-h-[calc(100svh-4.5rem)] items-end px-5 pb-28 pt-24 sm:px-10 lg:px-[clamp(3rem,6vw,7rem)] lg:pb-32">
      <div class="max-w-2xl">
        <h1 class="text-balance text-5xl leading-[1.02] tracking-[-0.035em] text-white sm:text-6xl lg:text-8xl" :class="mode === 'luxury' ? 'display-face font-medium' : 'font-bold'">
          {{ heroSettings.heading || collection.name }}
        </h1>
        <p v-if="heroSettings.body || collection.description" class="mt-6 max-w-xl text-base leading-7 text-white/78">
          {{ heroSettings.body || collection.description }}
        </p>
        <div class="mt-8 flex flex-wrap items-center gap-4"><ButtonAnchor href="#collection-products" size="lg" class="bg-white px-7 text-black hover:bg-white/90">Shop collection <ArrowDown class="ml-2 h-4 w-4" /></ButtonAnchor><ButtonAnchor
          v-if="activeSlide"
          :href="`${base}/product/${activeSlide.slug}`"
          size="lg"
          variant="link" class="h-auto whitespace-normal px-0 text-left text-white underline-offset-4 hover:text-white"
        >
          Explore {{ activeSlide.name }}
          <ArrowUpRight class="ml-2 h-4 w-4" />
        </ButtonAnchor></div>
      </div>
    </div>

    <div v-if="slides.length > 1" class="absolute bottom-5 right-5 z-20 flex items-center gap-3 sm:right-10 lg:right-[clamp(3rem,6vw,7rem)]">
      <Button v-if="heroSettings.autoplay !== false && !reducedMotion" type="button" variant="outline" size="icon" class="border-white/40 bg-black/15 text-white hover:bg-white hover:text-black" :aria-label="rotationStopped ? 'Play slideshow' : 'Pause slideshow'" @click="rotationStopped = !rotationStopped"><Play v-if="rotationStopped" class="h-4 w-4" /><Pause v-else class="h-4 w-4" /></Button>
      <span class="text-xs font-semibold tabular-nums text-white/75">{{ displayIndex }} / {{ displayTotal }}</span>
      <Button type="button" variant="outline" size="icon" class="border-white/40 bg-black/15 text-white hover:bg-white hover:text-black" aria-label="Previous collection highlight" @click="previous">
        <ChevronLeft class="h-4 w-4" />
      </Button>
      <Button type="button" variant="outline" size="icon" class="border-white/40 bg-black/15 text-white hover:bg-white hover:text-black" aria-label="Next collection highlight" @click="next">
        <ChevronRight class="h-4 w-4" />
      </Button>
    </div>
  </section>
</template>

<script setup>
import { ArrowDown, ArrowUpRight, ChevronLeft, ChevronRight, Pause, Play } from 'lucide-vue-next'
import CustomHeroCarousel from '~/components/site/CustomHeroCarousel.vue'

const props = defineProps({
  collection: { type: Object, required: true },
  products: { type: Array, default: () => [] },
  base: { type: String, required: true },
  mode: { type: String, default: 'default' },
})

const activeIndex = ref(0)
const paused = ref(false)
const reducedMotion = ref(false)
const rotationStopped = ref(false)
let timer = null

const heroSettings = computed(() => props.collection.hero_settings || {})
const customAssets = computed(() => Object.fromEntries((props.collection.hero_assets || []).map((asset) => [asset.public_id, asset])))
const slides = computed(() => {
  const requested = heroSettings.value.offering_ids || []
  const ordered = requested.length
    ? requested.map((id) => props.products.find((product) => product.public_id === id)).filter(Boolean)
    : props.products.slice(0, 5)
  return ordered.map((product) => ({
    id: product.public_id,
    name: product.name,
    slug: product.slug,
    image: imageFor(product),
  }))
})
const activeSlide = computed(() => slides.value[activeIndex.value] || null)
const displayIndex = computed(() => String(activeIndex.value + 1).padStart(2, '0'))
const displayTotal = computed(() => String(slides.value.length).padStart(2, '0'))

function imageFor(product) {
  const media = product.ordered_media || []
  return media.find((item) => item.role === 'cover') || media.find((item) => item.role === 'gallery') || product.media?.[0] || null
}
function stopTimer() {
  if (timer) window.clearInterval(timer)
  timer = null
}
function startTimer() {
  stopTimer()
  if (slides.value.length < 2 || reducedMotion.value || heroSettings.value.autoplay === false) return
  timer = window.setInterval(() => {
    if (!paused.value && !rotationStopped.value && !document.hidden) activeIndex.value = (activeIndex.value + 1) % slides.value.length
  }, 6500)
}
function goTo(index) {
  activeIndex.value = index
  startTimer()
}
function previous() { goTo((activeIndex.value - 1 + slides.value.length) % slides.value.length) }
function next() { goTo((activeIndex.value + 1) % slides.value.length) }

onMounted(() => {
  reducedMotion.value = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  startTimer()
})
onBeforeUnmount(stopTimer)
watch(slides, () => {
  if (activeIndex.value >= slides.value.length) activeIndex.value = 0
  if (import.meta.client) startTimer()
})
</script>

<style scoped>
.luxury-hero-enter-active,
.luxury-hero-leave-active { transition: opacity 320ms ease; }
.luxury-hero-enter-from,
.luxury-hero-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) {
  .luxury-hero-enter-active,
  .luxury-hero-leave-active { transition: none; }
}
</style>
