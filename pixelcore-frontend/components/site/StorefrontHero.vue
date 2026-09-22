<template>
  <section v-if="hero.enabled" class="relative isolate flex w-full overflow-hidden" :class="[heightClass, positionClass]" :style="surfaceStyle">
    <img v-if="hero.type === 'image' && media" :src="media.url" :alt="media.title || ''" class="absolute inset-0 -z-20 h-full w-full object-cover" />
    <video v-else-if="hero.type === 'video' && media" :src="media.url" :poster="poster?.url || identity.cover_image" class="absolute inset-0 -z-20 h-full w-full object-cover" :autoplay="motionAllowed" muted loop playsinline preload="metadata" />
    <ClientOnly v-else-if="hero.type === 'three' && media"><ThreeScene class="absolute inset-0 -z-20 h-full w-full rounded-none" kind="product_model" :settings="sceneSettings" :asset-url="media.url" :poster-url="poster?.url || identity.cover_image" /><template #fallback><img v-if="poster?.url || identity.cover_image" :src="poster?.url || identity.cover_image" alt="" class="absolute inset-0 -z-20 h-full w-full object-cover" /></template></ClientOnly>
    <div v-if="['image', 'video', 'three'].includes(hero.type)" class="absolute inset-0 -z-10" :style="{ backgroundColor: hero.overlay_color, opacity: hero.overlay_opacity }" />
    <div class="w-full px-5 py-14 sm:px-8 lg:px-12" :class="textClass"><div class="max-w-3xl"><h1 class="display-face text-5xl font-semibold tracking-[-0.03em] sm:text-6xl lg:text-7xl">{{ hero.heading || identity.tagline || identity.display_name }}</h1><p v-if="hero.description || identity.description" class="mt-5 max-w-2xl text-base leading-7 opacity-80">{{ hero.description || identity.description }}</p><div v-if="hero.primary_cta_label || hero.secondary_cta_label" class="mt-8 flex flex-wrap gap-3" :class="actionClass"><ButtonAnchor v-if="hero.primary_cta_label" :href="resolveLink(hero.primary_cta_url)">{{ hero.primary_cta_label }}</ButtonAnchor><ButtonAnchor v-if="hero.secondary_cta_label" :href="resolveLink(hero.secondary_cta_url)" variant="outline" class="border-current bg-transparent text-current hover:bg-white hover:text-foreground">{{ hero.secondary_cta_label }}</ButtonAnchor></div></div></div>
  </section>
</template>
<script setup>
import { ButtonAnchor } from '@/components/ui/button-anchor'
import { readableForeground } from '@/utils/businessTheme'
const props = defineProps({ identity: { type: Object, required: true }, base: { type: String, required: true } })
const motionAllowed = ref(false)
const hero = computed(() => props.identity.branding?.storefront?.hero || {})
const assets = computed(() => props.identity.branding_assets || {})
const media = computed(() => assets.value[hero.value.asset_id])
const poster = computed(() => assets.value[hero.value.poster_asset_id])
const heightClass = computed(() => ({ compact: 'min-h-[32rem]', medium: 'min-h-[70dvh]', tall: 'min-h-[88dvh]', screen: 'min-h-[calc(100dvh-4.5rem)]' }[hero.value.minimum_height] || 'min-h-[calc(100dvh-4.5rem)]'))
const positionClass = computed(() => ({ center_left: 'items-center', center: 'items-center', center_right: 'items-center', bottom_left: 'items-end', bottom_center: 'items-end', bottom_right: 'items-end' }[hero.value.position] || 'items-center'))
const textClass = computed(() => `${hero.value.alignment === 'center' ? 'text-center [&>div]:mx-auto' : hero.value.alignment === 'right' ? 'text-right [&>div]:ml-auto' : 'text-left'} ${hero.value.type === 'color' || hero.value.type === 'gradient' ? '' : 'text-white'}`)
const actionClass = computed(() => hero.value.alignment === 'center' ? 'justify-center' : hero.value.alignment === 'right' ? 'justify-end' : '')
const surfaceStyle = computed(() => ({ color: ['color', 'gradient'].includes(hero.value.type) ? readableForeground(hero.value.type === 'gradient' ? hero.value.gradient_from : hero.value.background_color) : undefined, background: hero.value.type === 'gradient' ? `linear-gradient(${hero.value.gradient_angle || 135}deg, ${hero.value.gradient_from}, ${hero.value.gradient_to})` : hero.value.background_color }))
const sceneSettings = computed(() => ({ motion: motionAllowed.value ? hero.value.motion : 'none', speed: 0.25, background_color: hero.value.background_color, camera: { x: 0, y: 0.2, z: 4.4 }, lighting: { ambient: 1.2, key: 1.8 } }))
onMounted(() => { motionAllowed.value = !window.matchMedia('(prefers-reduced-motion: reduce)').matches })
function resolveLink(value) { return value?.startsWith('/') ? `${props.base}${value === '/' ? '' : value}` : value }
</script>
