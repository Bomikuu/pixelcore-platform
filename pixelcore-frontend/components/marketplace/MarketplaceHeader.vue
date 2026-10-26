<template>
  <header :style="builderStyle" class="sticky top-0 z-40 border-b bg-background shadow-sm">
    <div class="border-b" :style="utilityStyle">
      <div class="mx-auto flex min-h-9 max-w-screen-2xl items-center justify-between gap-4 px-4 text-xs sm:px-6 lg:px-8">
        <p class="truncate font-medium">
          {{ identity.tagline || `Shop directly from ${identity.display_name}` }}
        </p>
        <nav class="hidden items-center gap-5 sm:flex" aria-label="Store utilities">
          <a :href="`${base}/account`" class="font-semibold hover:underline">Track orders</a>
          <a v-if="identity.contact_email" :href="`mailto:${identity.contact_email}`" class="font-semibold hover:underline">Help</a>
        </nav>
      </div>
    </div>

    <div class="mx-auto grid min-h-20 max-w-screen-2xl grid-cols-[auto_1fr_auto] items-center gap-3 px-4 sm:gap-5 sm:px-6 lg:px-8">
      <a :href="base || '/'" class="flex min-w-0 items-center gap-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
        <img v-if="identity.logo" :src="identity.logo" alt="" class="h-10 w-10 shrink-0 object-contain" />
        <span v-else class="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-primary text-sm font-black text-primary-foreground">
          {{ monogram }}
        </span>
        <span class="hidden max-w-44 truncate text-base font-black tracking-tight md:block">
          {{ identity.display_name }}
        </span>
      </a>

      <form
        class="relative min-w-0"
        role="search"
        @submit.prevent="search"
        @focusin="searchOpen = true"
        @focusout="closeSearchSuggestions"
      >
        <Label class="sr-only" for="marketplace-search">Search products</Label>
        <Input
          id="marketplace-search"
          v-model.trim="searchTerm"
          class="h-12 w-full rounded-lg border-2 border-primary bg-background pl-4 pr-12 shadow-none"
          type="search"
          placeholder="Search products, brands, and categories"
          autocomplete="off"
        />
        <Button class="absolute right-1 top-1 h-10 w-10 rounded-md" size="icon" type="submit" aria-label="Search catalog">
          <Search class="h-5 w-5" aria-hidden="true" />
        </Button>
        <div
          v-if="searchOpen && suggestions.length"
          class="absolute left-0 right-0 top-[calc(100%+0.5rem)] z-50 overflow-hidden border bg-popover text-popover-foreground shadow-xl"
        >
          <div class="flex items-center justify-between border-b px-4 py-2.5">
            <p class="text-xs font-extrabold uppercase tracking-[0.1em] text-muted-foreground">
              {{ searchTerm ? 'Matching products' : 'Suggested products' }}
            </p>
            <a :href="`${base}/shop`" class="text-xs font-bold text-primary hover:underline">View catalog</a>
          </div>
          <a
            v-for="product in suggestions"
            :key="product.public_id"
            :href="`${base}/product/${product.slug}`"
            class="grid grid-cols-[3rem_1fr_auto] items-center gap-3 border-b px-3 py-2.5 last:border-b-0 hover:bg-secondary"
          >
            <div class="h-12 w-12 overflow-hidden bg-secondary">
              <img v-if="productImage(product)" :src="productImage(product).url" :alt="productImage(product).alt_text || ''" class="h-full w-full object-cover" />
            </div>
            <div class="min-w-0">
              <p class="truncate text-sm font-extrabold">{{ product.name }}</p>
              <p class="truncate text-xs text-muted-foreground">{{ product.category || product.product_profile?.brand || 'Product' }}</p>
            </div>
            <span class="text-sm font-bold">{{ money(product.base_price) }}</span>
          </a>
        </div>
      </form>

      <div class="flex items-center justify-end gap-1">
        <ButtonAnchor variant="ghost" size="icon" :href="`${base}/account`" aria-label="Account and orders">
          <UserRound class="h-5 w-5" aria-hidden="true" />
        </ButtonAnchor>
        <ButtonAnchor class="hidden sm:inline-flex" variant="ghost" size="icon" :href="`${base}/account?tab=wishlist`" aria-label="Saved products">
          <Heart class="h-5 w-5" aria-hidden="true" />
        </ButtonAnchor>
        <Button variant="ghost" size="icon" class="relative" type="button" aria-label="Open cart" @click="cart.drawerOpen = true">
          <ShoppingCart class="h-5 w-5" aria-hidden="true" />
          <span v-if="cart.itemCount" class="absolute -right-0.5 top-0 min-w-4 rounded-full bg-accent px-1 text-[10px] font-black leading-4 text-accent-foreground">
            {{ cart.itemCount }}
          </span>
        </Button>
        <Sheet v-model:open="menuOpen">
          <SheetTrigger as-child>
            <Button variant="ghost" size="icon" class="lg:hidden" aria-label="Open categories">
              <Menu class="h-5 w-5" aria-hidden="true" />
            </Button>
          </SheetTrigger>
          <SheetContent side="right" class="w-[min(24rem,92vw)] overflow-y-auto">
            <SheetHeader class="text-left">
              <SheetTitle>Browse {{ identity.display_name }}</SheetTitle>
              <SheetDescription>Products, categories, and account links.</SheetDescription>
            </SheetHeader>
            <nav class="mt-6 space-y-1" aria-label="Mobile marketplace navigation">
              <a :href="`${base}/shop`" class="flex min-h-11 items-center rounded-md px-3 font-bold hover:bg-secondary">All products</a>
              <a v-for="category in categories" :key="category.slug" :href="`${base}/shop?category=${encodeURIComponent(category.slug)}`" class="flex min-h-11 items-center rounded-md px-3 text-sm font-semibold hover:bg-secondary">
                {{ category.name }}
              </a>
              <a v-for="item in secondaryNavigation" :key="item.id || item.path" :href="resolvePath(item.path)" class="flex min-h-11 items-center rounded-md px-3 text-sm font-semibold hover:bg-secondary">
                {{ item.label }}
              </a>
            </nav>
          </SheetContent>
        </Sheet>
      </div>
    </div>

    <MarketplaceCategoryMenu
      :identity="identity"
      :categories="headerCategories"
      :navigation="secondaryNavigation"
      :base="base"
    />
  </header>
</template>

<script setup>
import {
  Heart,
  Menu,
  Search,
  ShoppingCart,
  UserRound,
} from "lucide-vue-next";
import { productImages } from '@/utils/productImages'
import { readableForeground } from '@/utils/businessTheme'
import MarketplaceCategoryMenu from './MarketplaceCategoryMenu.vue'

const props = defineProps({
  identity: { type: Object, required: true },
  navigation: { type: Array, default: () => [] },
  base: { type: String, required: true },
  builderLayout: {type:Object,default:()=>({})},
});

const builderStyle = computed(() => {const style=(props.builderLayout?.revisionId ? props.builderLayout.regions?.find(n=>n.type==='header') : undefined)?.style || {};return {backgroundColor:style.backgroundColor,color:style.color,padding:style.padding!==undefined?`${style.padding}px`:undefined}})
const cart = useCartStore();
const wishlist = useWishlistStore();
const menuOpen = ref(false);
const searchTerm = ref("");
const searchOpen = ref(false)
const config = useRuntimeConfig();
const baseURL = import.meta.server ? config.apiInternalBaseUrl : config.public.apiBaseUrl;

const { data: discovery } = useAsyncData(
  `marketplace-navigation:${props.identity.slug}`,
  () => $fetch(`public/${props.identity.slug}/storefront/products/`, {
    baseURL,
    query: { page_size: 12 },
  }),
);

const categories = computed(() => discovery.value?.facets?.categories || []);
const headerCategories = computed(() => categories.value.filter((item) => item.show_in_header !== false))
const utilityStyle = computed(() => ({
  backgroundColor: props.identity.branding?.secondary_color,
  color: readableForeground(props.identity.branding?.secondary_color || '#e7f3f1'),
}))
const suggestions = computed(() => {
  const products = discovery.value?.results || []
  const query = searchTerm.value.trim().toLowerCase()
  if (!query) return products.slice(0, 5)
  return products.filter((product) =>
    [product.name, product.category, product.product_profile?.brand]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(query)),
  ).slice(0, 5)
})
const secondaryNavigation = computed(() =>
  props.navigation.filter((item) => !["/shop", "/wishlist", "/account"].includes(item.path)),
);
const monogram = computed(() =>
  props.identity.display_name
    ?.split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase() || "PC",
);

onMounted(async () => {
  wishlist.hydrate(props.identity.slug);
  await Promise.all([
    cart.load(props.identity.slug),
    wishlist.mergeIfSignedIn(props.identity.slug),
  ]);
});

function resolvePath(value) {
  return `${props.base}${value === "/" ? "" : value}` || "/";
}

function search() {
  const query = searchTerm.value ? `?search=${encodeURIComponent(searchTerm.value)}` : "";
  navigateTo(`${props.base}/shop${query}`);
}

function closeSearchSuggestions() {
  window.setTimeout(() => {
    searchOpen.value = false
  }, 150)
}

function productImage(product) {
  return productImages(product)[0] || null
}

function money(value) {
  return new Intl.NumberFormat('en-PH', {
    style: 'currency',
    currency: props.identity.currency || 'PHP',
  }).format(Number(value || 0))
}
</script>
