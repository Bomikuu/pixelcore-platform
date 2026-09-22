<template>
  <div class="grid min-h-[25rem] gap-10 px-8 py-8 lg:grid-cols-[16rem_minmax(0,1fr)] lg:px-12 xl:px-16">
    <div class="flex flex-col">
      <div>
        <h2 class="text-lg font-extrabold tracking-[-0.02em]">Explore the catalog</h2>
        <p class="mt-2 text-sm leading-6 text-muted-foreground">Browse the full range or start with a curated collection.</p>
      </div>
      <nav class="mt-6 grid gap-1" aria-label="Catalog shortcuts">
        <a :href="`${base}/shop`" class="group flex min-h-11 items-center justify-between rounded-lg px-3 py-2 text-sm font-bold transition-colors hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
          Shop all
          <ArrowUpRight class="h-4 w-4 transition-transform duration-200 group-hover:-translate-y-0.5 group-hover:translate-x-0.5 motion-reduce:transform-none" aria-hidden="true" />
        </a>
        <a v-for="collection in collections.slice(0, 4)" :key="collection.slug" :href="`${base}/collection/${collection.slug}`" class="group flex min-h-11 items-center justify-between rounded-lg px-3 py-2 text-sm font-semibold text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
          {{ collection.name }}
          <ArrowRight class="h-4 w-4 opacity-0 transition group-hover:translate-x-0.5 group-hover:opacity-100 group-focus-visible:opacity-100 motion-reduce:transform-none" aria-hidden="true" />
        </a>
      </nav>
      <p v-if="error" class="mt-auto pt-6 text-xs leading-5 text-muted-foreground">Catalog previews are temporarily unavailable. Shop all products to continue.</p>
    </div>

    <div>
      <div class="flex items-center justify-between gap-4">
        <h2 class="text-sm font-extrabold">Shop by category</h2>
        <div class="flex items-center gap-2"><template v-if="layout === 'carousel'"><Button variant="outline" size="icon" class="h-8 w-8 rounded-full" aria-label="Previous categories" @click="scrollCategories(-1)"><ChevronLeft class="h-4 w-4" /></Button><Button variant="outline" size="icon" class="h-8 w-8 rounded-full" aria-label="Next categories" @click="scrollCategories(1)"><ChevronRight class="h-4 w-4" /></Button></template><a :href="`${base}/shop`" class="ml-2 text-xs font-bold text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">View all products</a></div>
      </div>
      <div v-if="pending" class="mt-4 grid grid-cols-3 gap-3" aria-label="Loading categories" aria-busy="true">
        <div v-for="index in 3" :key="index" class="space-y-3">
          <Skeleton class="aspect-[4/3] w-full rounded-xl" />
          <Skeleton class="h-4 w-24" />
        </div>
      </div>
      <div ref="categoryTrack" v-else-if="categories.length" class="mt-4 grid gap-3" :class="layout === 'carousel' ? 'grid-flow-col auto-cols-[minmax(14rem,24%)] overflow-x-auto scroll-smooth pb-3' : 'grid-cols-3 xl:grid-cols-4'">
        <a v-for="category in categories.slice(0, layout === 'carousel' ? 12 : 4)" :key="category.slug" :href="`${base}/shop?category=${encodeURIComponent(category.slug)}`" class="group min-w-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">
          <div class="aspect-[4/3] overflow-hidden bg-secondary">
            <img v-if="category.image" :src="category.image.url" :alt="category.image.alt_text || category.name" class="h-full w-full object-cover transition duration-500 ease-out group-hover:scale-[1.035] motion-reduce:transform-none" />
            <div v-else class="flex h-full items-center justify-center text-muted-foreground"><Package class="h-8 w-8" aria-hidden="true" /></div>
          </div>
          <div class="mt-3 flex items-center justify-between gap-2 px-0.5">
            <span class="truncate text-sm font-extrabold">{{ category.name }}</span>
            <ArrowUpRight class="h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200 group-hover:-translate-y-0.5 group-hover:translate-x-0.5 motion-reduce:transform-none" aria-hidden="true" />
          </div>
        </a>
      </div>
      <div v-else class="mt-4 flex min-h-40 items-center justify-center rounded-xl bg-secondary px-6 text-center text-sm text-muted-foreground">Categories will appear here as products are published.</div>
    </div>
  </div>
</template>

<script setup>
import { ArrowRight, ArrowUpRight, ChevronLeft, ChevronRight, Package } from 'lucide-vue-next'
defineProps({
  base: { type: String, required: true },
  categories: { type: Array, default: () => [] },
  collections: { type: Array, default: () => [] },
  pending: { type: Boolean, default: false },
  error: { type: Boolean, default: false },
  layout: { type: String, default: 'grid' },
})
const categoryTrack = ref(null)
function scrollCategories(direction) { categoryTrack.value?.scrollBy({ left: direction * Math.max(280, categoryTrack.value.clientWidth * 0.72), behavior: 'smooth' }) }
</script>
