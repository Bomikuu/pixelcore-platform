<template>
  <section class="relative min-h-[calc(100dvh-4.5rem)] w-full overflow-hidden bg-foreground text-background" aria-labelledby="featured-product-title">
    <img v-if="image" :src="image.url" :alt="image.alt_text || product.name" class="absolute inset-0 h-full w-full object-cover" />
    <div class="absolute inset-0 bg-gradient-to-r from-black/75 via-black/25 to-transparent" />
    <div class="relative flex min-h-[calc(100dvh-4.5rem)] items-end px-5 py-12 sm:px-10 lg:px-16 lg:py-16">
      <div class="max-w-3xl">
        <Badge variant="secondary" class="mb-5">Featured product</Badge>
        <p v-if="product.product_profile?.brand" class="text-xs font-black uppercase tracking-[0.18em] text-white/70">{{ product.product_profile.brand }}</p>
        <h1 id="featured-product-title" class="display-face mt-3 text-5xl font-semibold tracking-[-0.05em] text-white sm:text-7xl lg:text-[7rem] lg:leading-[0.9]">{{ product.name }}</h1>
        <p v-if="product.summary" class="mt-6 max-w-2xl text-base leading-7 text-white/75 sm:text-lg">{{ product.summary }}</p>
        <div class="mt-8 flex flex-wrap items-center gap-4"><ButtonAnchor :href="`${base}/product/${product.slug}`" size="lg">Explore product <ArrowUpRight class="h-4 w-4" /></ButtonAnchor><strong class="text-lg tabular-nums text-white">{{ money(product.base_price) }}</strong></div>
      </div>
    </div>
  </section>
</template>
<script setup>
import { ArrowUpRight } from 'lucide-vue-next'
const props = defineProps({ product: { type: Object, required: true }, base: { type: String, required: true }, currency: { type: String, default: 'PHP' } })
const image = computed(() => props.product.ordered_media?.find((item) => item.role === 'cover') || props.product.media?.[0] || null)
const money = (value) => new Intl.NumberFormat('en-PH', { style: 'currency', currency: props.currency }).format(Number(value || 0))
</script>
