<template>
  <div>
    <section class="relative isolate min-h-[22rem] overflow-hidden border-b bg-primary text-primary-foreground sm:min-h-[28rem]">
      <img
        v-if="heroImage"
        :src="heroImage.url"
        :alt="heroImage.alt_text || ''"
        class="absolute inset-0 -z-20 h-full w-full object-cover"
      />
      <div v-if="heroImage" class="absolute inset-0 -z-10 bg-black/45" />
      <div class="mx-auto flex min-h-[22rem] max-w-screen-2xl items-end px-5 py-10 sm:min-h-[28rem] sm:px-8 sm:py-14 lg:px-12">
        <div class="max-w-3xl">
          <p class="text-xs font-bold uppercase tracking-[0.14em] opacity-75">Collection</p>
          <h1 class="mt-3 text-4xl font-black leading-[0.98] tracking-[-0.035em] sm:text-6xl lg:text-7xl">
            {{ collection.name }}
          </h1>
          <p v-if="collection.description" class="mt-5 max-w-2xl text-base leading-7 opacity-80">
            {{ collection.description }}
          </p>
        </div>
      </div>
    </section>

    <section class="mx-auto max-w-screen-2xl px-4 py-6 sm:px-6 lg:px-8" aria-label="Collection products">
      <div class="mb-5 flex flex-wrap items-center justify-between gap-3 border bg-background px-5 py-4">
        <p class="text-sm font-semibold text-muted-foreground">
          {{ products.length }} products in {{ collection.name }}
        </p>
        <ButtonAnchor :href="`${base}/shop`" variant="outline" size="sm">
          Explore all products
          <ArrowRight class="h-4 w-4" aria-hidden="true" />
        </ButtonAnchor>
      </div>

      <div v-if="products.length" class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-5">
        <MarketplaceProductCard
          v-for="product in products"
          :key="product.public_id"
          :product="product"
          :base="base"
          :slug="slug"
          :currency="identity.currency"
        />
      </div>
      <StatePanel
        v-else
        class="border bg-background"
        title="No products in this collection"
        message="Published products will appear here when assigned."
      />
    </section>
  </div>
</template>

<script setup>
import { ArrowRight } from 'lucide-vue-next'
import { productImages } from '@/utils/productImages'
import MarketplaceProductCard from './MarketplaceProductCard.vue'

const props = defineProps({
  collection: { type: Object, required: true },
  products: { type: Array, default: () => [] },
  identity: { type: Object, required: true },
  base: { type: String, required: true },
  slug: { type: String, required: true },
})

const heroImage = computed(() => {
  const settings = props.collection.hero_settings || {}
  if (settings.image_url) return { url: settings.image_url, alt_text: settings.alt_text || '' }
  if (settings.asset?.url) return settings.asset
  return productImages(props.products[0])[0] || null
})
</script>
