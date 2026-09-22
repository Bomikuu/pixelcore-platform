<template>
  <section class="relative isolate min-h-[28rem] overflow-hidden border bg-foreground text-background lg:min-h-[34rem]">
    <img
      v-if="visualUrl && visualType === 'image'"
      :src="visualUrl"
      :alt="visualAlt"
      class="absolute inset-0 -z-20 h-full w-full object-cover"
    />
    <video
      v-else-if="visualUrl && visualType === 'video'"
      :src="visualUrl"
      :poster="posterUrl"
      class="absolute inset-0 -z-20 h-full w-full object-cover"
      :autoplay="motionAllowed"
      muted
      loop
      playsinline
      preload="metadata"
    />
    <ClientOnly v-else-if="visualUrl && visualType === 'three'">
      <ThreeScene
        class="absolute inset-0 -z-20 h-full w-full rounded-none"
        kind="product_model"
        :settings="sceneSettings"
        :asset-url="visualUrl"
        :poster-url="posterUrl"
      />
      <template #fallback>
        <img v-if="posterUrl" :src="posterUrl" alt="" class="absolute inset-0 -z-20 h-full w-full object-cover" />
      </template>
    </ClientOnly>
    <div v-else class="absolute inset-0 -z-20 bg-primary" />
    <div class="absolute inset-0 -z-10 bg-black/45" />

    <div class="flex min-h-[28rem] items-end p-6 sm:p-10 lg:min-h-[34rem] lg:p-14">
      <div class="max-w-2xl">
        <Badge class="mb-5 bg-background text-foreground hover:bg-background">Featured now</Badge>
        <h1 class="display-face text-4xl font-black leading-[0.98] tracking-[-0.035em] sm:text-6xl lg:text-7xl">
          {{ heading }}
        </h1>
        <p v-if="description" class="mt-5 max-w-xl text-base leading-7 text-white/80">
          {{ description }}
        </p>
        <div class="mt-7 flex flex-wrap gap-3">
          <ButtonAnchor :href="primaryLink" size="lg" class="bg-background text-foreground hover:bg-background/90">
            {{ primaryLabel }}
            <ArrowRight class="h-4 w-4" aria-hidden="true" />
          </ButtonAnchor>
          <ButtonAnchor v-if="featuredProduct" :href="`${base}/product/${featuredProduct.slug}`" size="lg" variant="outline" class="border-white/60 bg-transparent text-white hover:bg-white hover:text-foreground">
            View product
          </ButtonAnchor>
        </div>
        <slot name="content" />
      </div>
    </div>
  </section>
</template>

<script setup>
import { ArrowRight } from 'lucide-vue-next'
import { productImages } from '@/utils/productImages'

const props = defineProps({
  identity: { type: Object, required: true },
  featuredProduct: { type: Object, default: null },
  base: { type: String, required: true },
})

const motionAllowed = ref(false)
const hero = computed(() => props.identity.branding?.storefront?.hero || {})
const assets = computed(() => props.identity.branding_assets || {})
const configuredMedia = computed(() => assets.value[hero.value.asset_id] || null)
const configuredPoster = computed(() => assets.value[hero.value.poster_asset_id] || null)
const productCover = computed(() => productImages(props.featuredProduct)[0] || null)
const visualType = computed(() => configuredMedia.value ? hero.value.type : 'image')
const visualUrl = computed(() => configuredMedia.value?.url || productCover.value?.url || props.identity.cover_image || '')
const posterUrl = computed(() => configuredPoster.value?.url || productCover.value?.url || props.identity.cover_image || '')
const visualAlt = computed(() => productCover.value?.alt_text || props.featuredProduct?.name || '')
const heading = computed(() => hero.value.heading || props.featuredProduct?.name || props.identity.tagline || props.identity.display_name)
const description = computed(() => hero.value.description || props.featuredProduct?.summary || props.identity.description)
const primaryLabel = computed(() => hero.value.primary_cta_label || 'Shop all products')
const primaryLink = computed(() => resolveLink(hero.value.primary_cta_url || '/shop'))
const sceneSettings = computed(() => ({
  motion: motionAllowed.value ? hero.value.motion : 'none',
  speed: 0.25,
  background_color: hero.value.background_color,
  camera: { x: 0, y: 0.2, z: 4.4 },
  lighting: { ambient: 1.2, key: 1.8 },
}))

onMounted(() => {
  motionAllowed.value = !window.matchMedia('(prefers-reduced-motion: reduce)').matches
})

function resolveLink(value) {
  return value?.startsWith('/') ? `${props.base}${value === '/' ? '' : value}` : value
}
</script>
