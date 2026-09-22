<template>
  <div class="mx-auto max-w-[var(--content-max-width)] px-4 pb-12 sm:px-6 lg:px-10 lg:pb-20">
    <section v-if="showCategories && categories.length" class="py-10 sm:py-16" aria-labelledby="home-categories-heading">
      <div class="flex flex-wrap items-end justify-between gap-4">
        <h2 id="home-categories-heading" class="display-face text-3xl font-semibold tracking-tight sm:text-4xl">Find your category.</h2>
        <a :href="`${base}/shop`" class="inline-flex min-h-11 items-center gap-2 text-sm font-semibold underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Explore the shop<ArrowUpRight class="h-4 w-4" aria-hidden="true" /></a>
      </div>
      <div class="mt-7 grid grid-cols-2 gap-x-3 gap-y-7 lg:grid-cols-4 lg:gap-x-5">
        <a v-for="category in categories" :key="category.slug" :href="`${base}/shop?category=${encodeURIComponent(category.slug)}`" class="group min-w-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
          <div class="aspect-[4/5] overflow-hidden bg-secondary">
            <img v-if="category.image" :src="category.image" :alt="category.name" class="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105 motion-reduce:transition-none" loading="lazy" />
            <div v-else class="flex h-full items-center justify-center"><ImageIcon class="h-8 w-8 text-muted-foreground" aria-hidden="true" /></div>
          </div>
          <div class="flex items-center justify-between gap-2 border-b py-4"><span class="text-sm font-semibold sm:text-base">{{ category.name }}</span><ArrowUpRight class="h-4 w-4 shrink-0" aria-hidden="true" /></div>
        </a>
      </div>
    </section>

    <section v-if="featured" class="grid overflow-hidden border bg-card md:grid-cols-2" aria-labelledby="home-feature-heading">
      <a :href="`${base}/product/${featured.slug}`" class="group block min-w-0 bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring" :aria-label="`Explore ${featured.name}`">
        <img :src="featuredImage.url" :alt="featuredImage.alt_text || featured.name" class="aspect-square h-full w-full object-contain p-5 transition-transform duration-700 group-hover:scale-[1.025] motion-reduce:transition-none sm:p-10" loading="lazy" />
      </a>
      <div class="flex flex-col justify-center px-6 py-10 sm:p-10 lg:p-16">
        <h2 id="home-feature-heading" class="display-face text-3xl font-semibold tracking-tight sm:text-4xl lg:text-5xl">{{ featured.name }}</h2>
        <p v-if="featured.summary" class="mt-5 max-w-lg text-base leading-7 text-muted-foreground">{{ featured.summary }}</p>
        <p class="mt-6 font-semibold tabular-nums">{{ money(featured.base_price) }}</p>
        <div class="mt-8 flex flex-wrap items-center gap-3">
          <ButtonAnchor :href="`${base}/product/${featured.slug}`" class="min-h-12 gap-3 px-6">Explore the product<ArrowUpRight class="h-4 w-4" aria-hidden="true" /></ButtonAnchor>
          <ButtonAnchor :href="`${base}/shop`" variant="ghost" class="min-h-12">Continue shopping</ButtonAnchor>
        </div>
      </div>
    </section>
    <section v-else class="flex flex-col justify-between gap-6 border-y py-10 sm:flex-row sm:items-center" aria-labelledby="home-shop-heading">
      <h2 id="home-shop-heading" class="display-face text-3xl font-semibold sm:text-4xl">Explore {{ identity.display_name }}.</h2>
      <ButtonAnchor :href="`${base}/shop`" class="min-h-12 self-start gap-3">Visit the shop<ArrowUpRight class="h-4 w-4" aria-hidden="true" /></ButtonAnchor>
    </section>
  </div>
</template>

<script setup>
import { ArrowUpRight, ImageIcon } from 'lucide-vue-next'
import { productImages } from '~/utils/productImages'

const props = defineProps({ identity: { type: Object, required: true }, offerings: { type: Array, default: () => [] }, base: { type: String, required: true }, showCategories: { type: Boolean, default: true } })
const config = useRuntimeConfig()
const baseURL = import.meta.server ? config.apiInternalBaseUrl : config.public.apiBaseUrl
const { data: discovery } = useAsyncData(
  `storefront-discovery:${props.identity.slug}`,
  () => $fetch(`public/${props.identity.slug}/storefront/products/`, { baseURL, query: { page_size: 12 } }),
)
const products = computed(() => [...new Map([...props.offerings, ...(discovery.value?.results || [])].filter((item) => item.offering_type !== 'service').map((item) => [item.public_id, item])).values()])
const categories = computed(() => (discovery.value?.facets?.categories || []).map((category) => ({
  ...category,
  image: category.image || productImages(products.value.find((item) => item.category === category.name))[0]?.url,
})).slice(0, 8))
const featured = computed(() => {
  const photographed = products.value.filter((item) => productImages(item).length)
  return photographed.find((item) => item.product_profile?.storefront_highlighted) || photographed[0] || null
})
const featuredImage = computed(() => productImages(featured.value)[0])
const money = (value) => new Intl.NumberFormat(props.identity.locale || 'en-PH', { style: 'currency', currency: props.identity.currency || 'PHP' }).format(Number(value || 0))
</script>
