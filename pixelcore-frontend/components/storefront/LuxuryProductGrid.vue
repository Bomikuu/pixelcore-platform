<template>
  <div v-if="products.length" class="grid w-full grid-cols-1 border-l border-t border-border/70 sm:grid-cols-2 lg:grid-cols-4">
    <LuxuryProductTile
      v-for="(product, index) in products"
      :key="product.public_id"
      :product="product"
      :featured="index === 0"
      :class="index === 0 ? 'lg:col-span-2 lg:row-span-2' : ''"
      :base="base"
      :slug="slug"
      :currency="currency"
    />
  </div>
  <StatePanel v-else class="mx-auto my-20 max-w-3xl px-5" title="No products in this collection" message="Published products will appear here when assigned." />
</template>

<script setup>
import LuxuryProductTile from './LuxuryProductTile.vue'
defineProps({
  products: { type: Array, default: () => [] },
  base: { type: String, required: true },
  slug: { type: String, required: true },
  currency: { type: String, default: 'PHP' },
})
</script>
