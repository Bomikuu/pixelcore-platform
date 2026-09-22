<template>
  <div class="mx-4 mb-4 overflow-hidden rounded-[var(--card-radius)] border bg-muted/35">
    <div class="flex min-h-7 items-center justify-between bg-[var(--brand-secondary)] px-3 text-[8px] font-bold">
      <span>{{ business.tagline || 'Shop directly from your business' }}</span>
      <span>Orders · Help</span>
    </div>
    <div class="grid grid-cols-[auto_1fr_auto] items-center gap-2 border-b bg-background px-3 py-2">
      <div class="flex items-center gap-1.5">
        <div class="grid h-7 w-7 place-items-center overflow-hidden rounded-[var(--button-radius)] bg-white">
          <img v-if="logo" :src="logo" alt="" class="h-full w-full object-contain" />
          <span v-else class="text-[9px] font-black">{{ initial }}</span>
        </div>
        <strong class="max-w-20 truncate text-[9px]">{{ business.display_name || 'Your store' }}</strong>
      </div>
      <div class="flex h-7 items-center justify-between rounded-[var(--input-radius)] border-2 border-[var(--brand-primary)] px-2 text-[8px] text-muted-foreground">
        <span>Search products and categories</span>
        <Search class="h-3 w-3 text-[var(--brand-primary)]" aria-hidden="true" />
      </div>
      <div class="flex gap-1.5 text-[8px] font-bold"><span>Account</span><span>Cart</span></div>
    </div>
    <div class="flex h-7 items-center gap-3 border-b bg-background px-3 text-[8px] font-bold">
      <span>All products</span><span>Category</span><span>Collection</span><span>New arrivals</span>
    </div>
    <div class="grid gap-2 p-3 sm:grid-cols-[5rem_1fr]">
      <div class="hidden border bg-background p-2 text-[8px] font-bold sm:block">
        <p class="border-b pb-1.5">Categories</p>
        <div class="mt-2 space-y-2 text-muted-foreground"><p>Apparel</p><p>Accessories</p><p>Featured</p></div>
      </div>
      <div class="relative flex min-h-32 items-end overflow-hidden bg-[var(--brand-primary)] p-4 text-white">
        <img v-if="cover" :src="cover" alt="" class="absolute inset-0 h-full w-full object-cover opacity-55" />
        <div class="relative z-10 max-w-48">
          <p class="text-[8px] font-bold uppercase tracking-wider">Featured now</p>
          <h3 class="mt-1 text-base font-black leading-tight">{{ hero.heading || business.tagline || 'A store built for discovery' }}</h3>
          <span class="mt-2 inline-flex rounded-[var(--button-radius)] bg-white px-2 py-1 text-[8px] font-bold text-foreground">Shop now</span>
        </div>
      </div>
    </div>
    <div class="border-t bg-background p-3">
      <div class="flex items-end justify-between"><div><p class="text-[7px] font-bold uppercase tracking-wider text-[var(--brand-primary)]">Featured picks</p><h3 class="text-[10px] font-black">Browse products</h3></div><span class="text-[8px]">View all</span></div>
      <div class="mt-2 grid grid-cols-4 gap-1.5">
        <div v-for="index in 4" :key="index" class="border p-1.5">
          <div class="aspect-square bg-secondary" />
          <div class="mt-1 h-1.5 w-3/4 bg-muted" />
          <div class="mt-1 h-1.5 w-1/2 bg-[var(--brand-primary)]/50" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Search } from 'lucide-vue-next'

const props = defineProps({
  business: { type: Object, required: true },
  logo: { type: String, default: '' },
  cover: { type: String, default: '' },
})

const initial = computed(() =>
  (props.business.display_name || 'P').trim().charAt(0).toUpperCase(),
)
const hero = computed(() => props.business.branding?.storefront?.hero || {})
</script>
