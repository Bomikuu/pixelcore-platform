<template>
  <div
    :class="settings.carousel_width === 'contained' ? 'mx-auto max-w-screen-2xl px-4 py-5 sm:px-6 lg:px-8' : ''"
  >
    <CustomHeroCarousel
      v-if="slides.length"
      :slides="slides"
      :assets="combinedAssets"
      :base="base"
      :autoplay="settings.autoplay ?? true"
      :interval="settings.interval || 7"
      :height="carouselHeight"
      :center-content="showSearch"
    >
      <template v-if="showSearch" #content>
        <MarketplaceHeroSearch :categories="categories" :base="base" />
      </template>
    </CustomHeroCarousel>
    <MarketplaceHero v-else :identity="identity" :featured-product="products[0]" :base="base">
      <template v-if="showSearch" #content>
        <MarketplaceHeroSearch :categories="categories" :base="base" />
      </template>
    </MarketplaceHero>
  </div>
</template>

<script setup>
import { productImages } from '@/utils/productImages'
import CustomHeroCarousel from '@/components/site/CustomHeroCarousel.vue'
import MarketplaceHero from './MarketplaceHero.vue'

const props = defineProps({
  identity: { type: Object, required: true },
  products: { type: Array, default: () => [] },
  heroBlock: { type: Object, default: null },
  assets: { type: Object, default: () => ({}) },
  categories: { type: Array, default: () => [] },
  showSearch: { type: Boolean, default: false },
  base: { type: String, required: true },
})
const settings = computed(() => props.identity.branding?.storefront?.marketplace || {})
const carouselHeight = computed(() => {
  const configuredHeight = settings.value.carousel_height || 'medium'

  return props.showSearch ? 'screen' : configuredHeight
})
const photoProducts = computed(() => {
  const source = props.heroBlock?.settings || {}
  const ids = source.offering_ids?.length ? source.offering_ids : source.offering_id ? [source.offering_id] : []
  const unique = [...new Map(props.products.map((product) => [product.public_id, product])).values()]
  const selected = ids.length ? ids.map((id) => unique.find((product) => product.public_id === id)).filter(Boolean) : unique
  return selected.filter((product) => productImages(product)[0]).slice(0, 5)
})
const combinedAssets = computed(() => ({
  ...props.assets,
  ...props.identity.branding_assets,
  ...Object.fromEntries(photoProducts.value.map((product) => [product.public_id, productImages(product)[0]])),
  ...Object.fromEntries(photoProducts.value.flatMap((product) =>
    (product.ordered_media || []).filter((item) => ['model', 'poster'].includes(item.role)).map((item) => [`${product.public_id}-${item.role}`, item]),
  )),
}))
const slides = computed(() => {
  if (settings.value.slides?.length) return settings.value.slides
  if (props.identity.branding?.storefront?.hero?.enabled) return []
  if (props.heroBlock?.settings?.slides?.length) return props.heroBlock.settings.slides
  const source = props.heroBlock?.settings || {}
  return photoProducts.value.map((product, index) => ({
    id: product.public_id,
    type: product.ordered_media?.some((item) => item.role === 'model') ? 'model' : 'image',
    asset_id: product.ordered_media?.some((item) => item.role === 'model') ? `${product.public_id}-model` : product.public_id,
    poster_asset_id: product.ordered_media?.some((item) => item.role === 'poster') ? `${product.public_id}-poster` : product.public_id,
    heading: index === 0 && source.heading ? source.heading : product.name,
    body: index === 0 && source.body ? source.body : product.summary || '',
    label: index === 0 && source.primary_label ? source.primary_label : 'View product',
    path: index === 0 && source.primary_path ? source.primary_path : `/product/${product.slug}`,
    background_color: props.identity.branding?.primary_color || '#17362F',
  }))
})
</script>
