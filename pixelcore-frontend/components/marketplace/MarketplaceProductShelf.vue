<template>
  <section class="border bg-background p-4 sm:p-6" :aria-labelledby="headingId">
    <div class="flex items-end justify-between gap-4">
      <div>
        <p class="text-xs font-bold uppercase tracking-[0.12em] text-primary">{{ eyebrow }}</p>
        <h2 :id="headingId" class="mt-1 text-2xl font-black tracking-tight">{{ title }}</h2>
      </div>
      <ButtonAnchor :href="`${base}/shop`" variant="outline" size="sm">
        Shop all
        <ArrowRight class="h-4 w-4" aria-hidden="true" />
      </ButtonAnchor>
    </div>
    <div class="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      <MarketplaceProductCard
        v-for="product in products"
        :key="product.public_id"
        :product="product"
        :base="base"
        :slug="identity.slug"
        :currency="identity.currency"
      />
    </div>
  </section>
</template>

<script setup>
import { ArrowRight } from 'lucide-vue-next'
import MarketplaceProductCard from './MarketplaceProductCard.vue'

const props = defineProps({
  eyebrow: { type: String, required: true },
  title: { type: String, required: true },
  products: { type: Array, default: () => [] },
  identity: { type: Object, required: true },
  base: { type: String, required: true },
})

const headingId = computed(() =>
  `marketplace-shelf-${props.title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`,
)
</script>
