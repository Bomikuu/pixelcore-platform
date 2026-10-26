<template>
  <header :data-builder-variant="builderHeader?.props?.variant" :style="builderStyle" class="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/85" :class="isLuxury ? 'border-foreground/15' : ''" @pointerleave="scheduleCatalogClose">
    <div class="grid min-h-[4.5rem] w-full grid-cols-[auto_1fr_auto] items-center gap-4 px-4 sm:px-7 lg:px-10">
      <a :href="base || '/'" class="group flex min-w-0 items-center gap-3 rounded-[var(--button-radius)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2" :aria-label="`${identity.display_name} home`">
        <img v-if="identity.logo" :src="identity.logo" alt="" class="h-9 w-9 rounded-[var(--button-radius)] object-contain" />
        <span v-else class="grid h-9 w-9 shrink-0 place-items-center rounded-[var(--button-radius)] bg-[var(--brand-secondary)] text-sm font-black text-white" aria-hidden="true">{{ monogram }}</span>
        <span class="brand-name truncate text-base font-black tracking-[-0.025em] transition-colors group-hover:text-primary sm:text-lg">{{ identity.display_name }}</span>
      </a>

      <nav class="hidden h-full items-center justify-center gap-1 lg:flex" aria-label="Storefront navigation">
        <Button
          variant="ghost"
          class="h-10 px-4 font-bold"
          aria-haspopup="true"
          :aria-expanded="catalogOpen"
          aria-controls="storefront-catalog-menu"
          @click="catalogOpen = !catalogOpen"
          @focus="openCatalog"
          @pointerenter="openCatalog"
          @keydown.esc="catalogOpen = false"
        >Shop</Button>

        <a v-for="item in secondaryNavigation" :key="item.id || item.path" :href="path(item.path)" class="relative flex h-10 items-center rounded-lg px-4 text-sm font-bold text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">{{ item.label }}</a>
      </nav>

      <div class="flex items-center justify-end gap-0.5 sm:gap-1">
        <Button variant="ghost" size="icon" class="rounded-full" aria-label="Search products" @click="searchOpen = true"><Search class="h-5 w-5" /></Button>
        <ButtonAnchor variant="ghost" size="icon" class="hidden rounded-full sm:inline-flex" :href="`${base}/account?tab=wishlist`" aria-label="Wishlist"><Heart class="h-5 w-5" /><span v-if="wishlist.count" class="sr-only">{{ wishlist.count }} saved</span></ButtonAnchor>
        <ButtonAnchor variant="ghost" size="icon" class="hidden rounded-full sm:inline-flex" :href="`${base}/account`" aria-label="Account"><UserRound class="h-5 w-5" /></ButtonAnchor>
        <Button variant="ghost" class="relative rounded-full" size="icon" aria-label="Open shopping bag" @click="cart.drawerOpen = true"><ShoppingBag class="h-5 w-5" /><span v-if="cart.itemCount" class="absolute right-0 top-0 min-w-4 rounded-full bg-primary px-1 text-[10px] font-bold leading-4 text-primary-foreground">{{ cart.itemCount }}</span></Button>

        <Sheet v-model:open="menuOpen">
          <SheetTrigger as-child><Button variant="ghost" size="icon" class="rounded-full lg:hidden" aria-label="Open menu"><Menu class="h-5 w-5" /></Button></SheetTrigger>
          <SheetContent side="right" class="w-[min(24rem,90vw)] overflow-y-auto px-0">
            <SheetHeader class="border-b px-6 pb-5 text-left"><SheetTitle class="text-xl font-extrabold">{{ identity.display_name }}</SheetTitle><SheetDescription>Browse products, saved items, and your account.</SheetDescription></SheetHeader>
            <nav class="px-3 py-5" aria-label="Mobile storefront navigation">
              <a :href="`${base}/shop`" class="flex min-h-12 items-center justify-between rounded-lg px-3 text-lg font-extrabold hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Shop all <ArrowUpRight class="h-5 w-5" /></a>
              <a v-for="item in secondaryNavigation" :key="item.id || item.path" :href="path(item.path)" class="flex min-h-12 items-center rounded-lg px-3 text-base font-bold text-muted-foreground hover:bg-secondary hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">{{ item.label }}</a>

              <div v-if="categories.length" class="mt-6 border-t px-3 pt-6">
                <h2 class="text-sm font-extrabold">Shop by category</h2>
                <div class="mt-4 grid grid-cols-2 gap-3">
                  <a v-for="category in categories.slice(0, 4)" :key="category.slug" :href="`${base}/shop?category=${encodeURIComponent(category.slug)}`" class="group min-w-0 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                    <div class="aspect-square overflow-hidden rounded-lg bg-secondary"><img v-if="category.image" :src="category.image.url" :alt="category.name" class="h-full w-full object-cover transition duration-300 group-hover:scale-[1.03] motion-reduce:transform-none" /></div>
                    <p class="mt-2 truncate text-sm font-bold">{{ category.name }}</p>
                  </a>
                </div>
              </div>

              <div class="mt-6 grid gap-1 border-t px-3 pt-5">
                <a :href="`${base}/account?tab=wishlist`" class="flex min-h-11 items-center gap-3 rounded-lg px-3 text-sm font-bold hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"><Heart class="h-4 w-4" /> Wishlist</a>
                <a :href="`${base}/account`" class="flex min-h-11 items-center gap-3 rounded-lg px-3 text-sm font-bold hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"><UserRound class="h-4 w-4" /> Account</a>
              </div>
            </nav>
          </SheetContent>
        </Sheet>
      </div>
    </div>

    <Transition name="catalog-panel">
      <div v-if="catalogOpen" id="storefront-catalog-menu" class="absolute inset-x-0 top-full w-full border-y bg-background shadow-[0_26px_60px_rgba(15,24,20,0.14)]" @pointerenter="cancelCatalogClose" @pointerleave="scheduleCatalogClose">
        <StorefrontMegaMenu :base="base" :categories="headerCategories" :collections="collections" :layout="headerLayout" :pending="discoveryPending" :error="Boolean(discoveryError)" />
      </div>
    </Transition>

    <StorefrontSearchDialog v-model:open="searchOpen" :base="base" :slug="identity.slug" :currency="identity.currency" :default-products="products" :categories="categories" :pending="discoveryPending" />
  </header>
</template>

<script setup>
import { ArrowUpRight, Heart, Menu, Search, ShoppingBag, UserRound } from 'lucide-vue-next'
import StorefrontMegaMenu from './StorefrontMegaMenu.vue'
import StorefrontSearchDialog from './StorefrontSearchDialog.vue'

const props = defineProps({
  identity: { type: Object, required: true },
  navigation: { type: Array, default: () => [] },
  base: { type: String, required: true },
  builderLayout: {type:Object,default:()=>({})},
})
const builderHeader = computed(() => props.builderLayout?.revisionId ? props.builderLayout.regions?.find(n => n.type === 'header') : undefined)
const builderStyle = computed(() => { const style = builderHeader.value?.style || {}; return {backgroundColor:style.backgroundColor,color:style.color,padding:style.padding !== undefined ? `${style.padding}px` : undefined} })
const cart = useCartStore()
const wishlist = useWishlistStore()
const menuOpen = ref(false)
const searchOpen = ref(false)
const catalogOpen = ref(false)
const config = useRuntimeConfig()
let catalogCloseTimer

const baseURL = import.meta.server ? config.apiInternalBaseUrl : config.public.apiBaseUrl
const { data: discovery, pending: discoveryPending, error: discoveryError } = useAsyncData(
  `storefront-discovery:${props.identity.slug}`,
  () => $fetch(`public/${props.identity.slug}/storefront/products/`, { baseURL, query: { page_size: 12 } }),
)
const products = computed(() => discovery.value?.results || [])
const collections = computed(() => discovery.value?.facets?.collections || [])
const categories = computed(() => (discovery.value?.facets?.categories || []).map((category) => ({
  ...category,
  image: category.image ? { url: category.image, alt_text: category.name } : productImage(products.value.find((product) => product.category === category.name)),
})))
const headerCategories = computed(() => {
  const curated = categories.value.filter((category) => category.show_in_header !== false)
  return (curated.length ? curated : categories.value).sort((a, b) => Number(a.header_order || 0) - Number(b.header_order || 0))
})
const headerLayout = computed(() => props.identity.branding?.storefront?.header?.category_layout || 'grid')
const isLuxury = computed(() => props.identity.branding?.storefront?.mode === 'luxury')
const secondaryNavigation = computed(() => props.navigation.filter((item) => !['/shop', '/wishlist', '/account'].includes(item.path)).slice(0, 5))
const monogram = computed(() => props.identity.display_name?.split(/\s+/).slice(0, 2).map((word) => word[0]).join('').toUpperCase() || 'PC')
const path = (value) => `${props.base}${value === '/' ? '' : value}` || '/'

onMounted(async () => {
  wishlist.hydrate(props.identity.slug)
  await Promise.all([cart.load(props.identity.slug), wishlist.mergeIfSignedIn(props.identity.slug)])
})
onBeforeUnmount(() => clearTimeout(catalogCloseTimer))

function productImage(product) {
  if (!product) return null
  return product.ordered_media?.find((item) => item.role === 'cover') || product.media?.[0] || null
}
function openCatalog() { clearTimeout(catalogCloseTimer); catalogOpen.value = true }
function cancelCatalogClose() { clearTimeout(catalogCloseTimer) }
function scheduleCatalogClose() { clearTimeout(catalogCloseTimer); catalogCloseTimer = setTimeout(() => { catalogOpen.value = false }, 180) }
</script>

<style scoped>
[data-builder-variant="center"] > div:first-child { grid-template-columns: 1fr auto 1fr; }
[data-builder-variant="center"] .brand-name { text-align: center; }
[data-builder-variant="center"] > div:first-child > a { grid-column: 2; }
[data-builder-variant="center"] > div:first-child > nav { grid-row: 2; grid-column: 1 / -1; }
[data-builder-variant="center"] > div:first-child > div { grid-column: 3; grid-row: 1; }

.catalog-panel-enter-active,
.catalog-panel-leave-active { transition: opacity 180ms ease, transform 180ms ease; }
.catalog-panel-enter-from,
.catalog-panel-leave-to { opacity: 0; transform: translateY(-0.4rem); }
@media (prefers-reduced-motion: reduce) {
  .catalog-panel-enter-active,
  .catalog-panel-leave-active { transition: none; }
}
@media (max-width: 429px) {
  .brand-name { display: none; }
}
</style>
