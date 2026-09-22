<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="!left-0 !top-0 !flex !h-dvh !w-screen !max-w-none !translate-x-0 !translate-y-0 flex-col gap-0 overflow-hidden !rounded-none !border-0 p-0">
      <DialogHeader class="border-b px-5 pb-7 pt-8 pr-16 sm:px-10 lg:px-16 lg:pb-10 lg:pt-12">
        <DialogTitle class="text-3xl font-black tracking-[-0.045em] sm:text-5xl">Search the collection</DialogTitle>
        <DialogDescription class="mt-1">Find products by name, category, brand, or material.</DialogDescription>
        <form class="relative mt-5" role="search" @submit.prevent="viewAll">
          <Search class="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
          <Input v-model="query" class="h-16 !rounded-none !border-x-0 !border-t-0 !pl-12 !pr-12 text-lg shadow-none focus-visible:ring-0" placeholder="What are you looking for?" autocomplete="off" aria-label="Search this store" />
          <Button v-if="query" type="button" variant="ghost" size="icon" class="absolute right-1.5 top-1/2 -translate-y-1/2" aria-label="Clear search" @click="query = ''"><X class="h-4 w-4" aria-hidden="true" /></Button>
        </form>
      </DialogHeader>

      <div class="min-h-0 flex-1 overflow-y-auto px-5 py-8 sm:px-10 lg:px-16 lg:py-12">
        <div v-if="!query" class="grid gap-12 lg:grid-cols-[minmax(0,1fr)_19rem]">
          <section>
            <div class="flex items-end justify-between gap-4">
              <div><h2 class="text-lg font-extrabold tracking-[-0.02em]">Featured products</h2><p class="mt-1 text-sm text-muted-foreground">A quick look at the store before you search.</p></div>
              <a :href="`${base}/shop`" class="hidden text-sm font-bold text-primary underline-offset-4 hover:underline sm:block">Shop all</a>
            </div>
            <div v-if="pending" class="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-3" aria-label="Loading recommendations" aria-busy="true">
              <div v-for="index in 3" :key="index" class="space-y-3"><Skeleton class="aspect-[4/5] w-full rounded-xl" /><Skeleton class="h-4 w-4/5" /><Skeleton class="h-3 w-2/5" /></div>
            </div>
            <div v-else-if="defaultProducts.length" class="mt-5 grid grid-cols-2 gap-x-4 gap-y-6 sm:grid-cols-3">
              <a v-for="product in defaultProducts.slice(0, 6)" :key="product.public_id" :href="`${base}/product/${product.slug}`" class="group min-w-0 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2" @click="$emit('update:open', false)">
                <div class="aspect-[4/5] overflow-hidden rounded-xl bg-secondary">
                  <img v-if="productImage(product)" :src="productImage(product).url" :alt="product.name" class="h-full w-full object-cover transition duration-500 ease-out group-hover:scale-[1.035] motion-reduce:transform-none" />
                  <div v-else class="flex h-full items-center justify-center text-muted-foreground"><Package class="h-7 w-7" aria-hidden="true" /></div>
                </div>
                <p class="mt-3 truncate text-sm font-extrabold group-hover:text-primary">{{ product.name }}</p>
                <p class="mt-1 text-xs font-semibold tabular-nums text-muted-foreground">{{ money(product.base_price) }}</p>
              </a>
            </div>
            <div v-else class="mt-5 rounded-xl bg-secondary px-5 py-8 text-center text-sm text-muted-foreground">Published products will appear here.</div>
          </section>

          <aside class="border-t pt-6 lg:border-l lg:border-t-0 lg:pl-7 lg:pt-0">
            <h2 class="text-sm font-extrabold">Browse categories</h2>
            <nav class="mt-3 grid grid-cols-2 gap-1 lg:grid-cols-1" aria-label="Search categories">
              <a v-for="category in categories" :key="category.slug" :href="`${base}/shop?category=${encodeURIComponent(category.slug)}`" class="flex min-h-10 items-center justify-between rounded-lg px-3 py-2 text-sm font-semibold text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" @click="$emit('update:open', false)">{{ category.name }}<ArrowRight class="h-4 w-4" aria-hidden="true" /></a>
            </nav>
          </aside>
        </div>

        <section v-else aria-live="polite">
          <div class="flex items-end justify-between gap-4">
            <div><h2 class="text-lg font-extrabold tracking-[-0.02em]">{{ searchPending ? 'Searching products' : `${visibleResults.length} suggestion${visibleResults.length === 1 ? '' : 's'}` }}</h2><p class="mt-1 text-sm text-muted-foreground">Matches for “{{ query }}”</p></div>
            <Button variant="outline" size="sm" type="button" @click="viewAll">View all results</Button>
          </div>
          <div v-if="searchPending" class="mt-5 grid gap-3 sm:grid-cols-2" aria-label="Searching products" aria-busy="true">
            <div v-for="index in 4" :key="index" class="flex gap-4 rounded-xl bg-secondary p-3"><Skeleton class="h-24 w-20 shrink-0 rounded-lg" /><div class="flex-1 space-y-3 py-2"><Skeleton class="h-4 w-4/5" /><Skeleton class="h-3 w-2/5" /><Skeleton class="h-3 w-1/3" /></div></div>
          </div>
          <div v-else-if="searchError" class="mt-5 rounded-xl bg-secondary px-5 py-8 text-center"><p class="font-bold">Suggestions could not be loaded.</p><p class="mt-2 text-sm text-muted-foreground">Press Enter to search the full catalog.</p></div>
          <div v-else-if="visibleResults.length" class="mt-5 grid gap-3 sm:grid-cols-2">
            <a v-for="product in visibleResults" :key="product.public_id" :href="`${base}/product/${product.slug}`" class="group flex min-w-0 gap-4 rounded-xl bg-secondary p-3 transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" @click="$emit('update:open', false)">
              <div class="h-24 w-20 shrink-0 overflow-hidden rounded-lg bg-background"><img v-if="productImage(product)" :src="productImage(product).url" :alt="product.name" class="h-full w-full object-cover transition duration-300 group-hover:scale-[1.04] motion-reduce:transform-none" /><div v-else class="flex h-full items-center justify-center text-muted-foreground"><Package class="h-5 w-5" aria-hidden="true" /></div></div>
              <div class="min-w-0 self-center"><p class="truncate font-extrabold group-hover:text-primary">{{ product.name }}</p><p class="mt-1 truncate text-xs text-muted-foreground">{{ product.category || product.product_profile?.brand || 'Product' }}</p><p class="mt-2 text-sm font-bold tabular-nums">{{ money(product.base_price) }}</p></div>
            </a>
          </div>
          <div v-else class="mt-5 rounded-xl bg-secondary px-5 py-10 text-center"><SearchX class="mx-auto h-7 w-7 text-muted-foreground" aria-hidden="true" /><p class="mt-4 font-extrabold">No close matches yet</p><p class="mx-auto mt-2 max-w-sm text-sm leading-6 text-muted-foreground">Try a shorter product name, a category, or browse the complete catalog.</p><Button variant="outline" class="mt-5" type="button" @click="viewAll">Search the full catalog</Button></div>
        </section>
      </div>
    </DialogContent>
  </Dialog>
</template>

<script setup>
import { ArrowRight, Package, Search, SearchX, X } from 'lucide-vue-next'
const props = defineProps({
  open: { type: Boolean, default: false },
  base: { type: String, required: true },
  slug: { type: String, required: true },
  currency: { type: String, default: 'PHP' },
  defaultProducts: { type: Array, default: () => [] },
  categories: { type: Array, default: () => [] },
  pending: { type: Boolean, default: false },
})
const emit = defineEmits(['update:open'])
const query = ref('')
const remoteResults = ref([])
const searchPending = ref(false)
const searchError = ref(false)
const config = useRuntimeConfig()
let searchTimer
let requestSequence = 0
const visibleResults = computed(() => remoteResults.value.slice(0, 8))

watch(() => props.open, (isOpen) => {
  if (!isOpen) { query.value = ''; remoteResults.value = []; searchError.value = false; searchPending.value = false }
})
watch(query, (value) => {
  clearTimeout(searchTimer)
  const normalized = value.trim()
  if (!normalized) { remoteResults.value = []; searchError.value = false; searchPending.value = false; return }
  searchPending.value = true
  searchTimer = setTimeout(() => loadSuggestions(normalized), 180)
})
onBeforeUnmount(() => clearTimeout(searchTimer))

async function loadSuggestions(value) {
  const sequence = ++requestSequence
  searchError.value = false
  try {
    const baseURL = import.meta.server ? config.apiInternalBaseUrl : config.public.apiBaseUrl
    const response = await $fetch(`public/${props.slug}/storefront/products/`, { baseURL, query: { search: value, page_size: 8 } })
    if (sequence === requestSequence) remoteResults.value = response.results || []
  } catch {
    if (sequence === requestSequence) { remoteResults.value = []; searchError.value = true }
  } finally {
    if (sequence === requestSequence) searchPending.value = false
  }
}
function productImage(product) { return product.ordered_media?.find((item) => item.role === 'cover') || product.media?.[0] || null }
function money(value) { return new Intl.NumberFormat('en-PH', { style: 'currency', currency: props.currency }).format(Number(value || 0)) }
function viewAll() { const value = query.value.trim(); emit('update:open', false); navigateTo(`${props.base}/shop${value ? `?search=${encodeURIComponent(value)}` : ''}`) }
</script>
