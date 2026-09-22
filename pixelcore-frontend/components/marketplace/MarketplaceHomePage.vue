<template>
  <MarketplaceStorefrontFrame
    :identity="manifest.identity"
    :navigation="manifest.site.navigation"
    :base="base"
    full-bleed
  >
    <MarketplaceHomeCarousel
      v-if="heroLayout !== 'search'"
      :identity="manifest.identity"
      :products="[...products, ...offerings]"
      :hero-block="heroBlock"
      :assets="assetMap"
      :categories="categories"
      :show-search="heroLayout === 'both'"
      :base="base"
    />
    <MarketplaceSearchHero
      v-if="heroLayout === 'search'"
      primary
      :identity="manifest.identity"
      :categories="categories"
      :base="base"
    />
    <div class="mx-auto max-w-screen-2xl px-4 py-5 sm:px-6 lg:px-8">
      <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
        <h2 class="text-xl font-semibold">Discover {{ manifest.identity.display_name }}</h2>
        <a :href="`${base}/shop`" class="text-sm underline underline-offset-4">Explore the catalog</a>
      </div>
      <div class="grid gap-4" :class="heroLayout === 'search' ? 'lg:grid-cols-[13rem_minmax(0,1fr)_minmax(0,1.2fr)]' : 'lg:grid-cols-[16rem_minmax(0,1fr)]'">
        <aside class="hidden border bg-background lg:block" aria-label="Shop categories">
          <div class="flex items-center gap-2 border-b px-4 py-3">
            <LayoutGrid class="h-4 w-4 text-primary" aria-hidden="true" />
            <h2 class="text-sm font-extrabold">Shop by category</h2>
          </div>
          <nav class="p-2">
            <a
              v-for="category in categories.slice(0, 10)"
              :key="category.slug"
              :href="`${base}/shop?category=${encodeURIComponent(category.slug)}`"
              class="flex min-h-10 items-center justify-between gap-3 rounded-md px-3 text-sm font-semibold transition hover:bg-secondary hover:text-primary"
            >
              <span class="truncate">{{ category.name }}</span>
              <ChevronRight class="h-4 w-4 shrink-0" aria-hidden="true" />
            </a>
            <a :href="`${base}/shop`" class="mt-1 flex min-h-10 items-center rounded-md px-3 text-sm font-extrabold text-primary hover:bg-secondary">
              View all products
            </a>
          </nav>
        </aside>

        <div class="grid min-w-0 grid-cols-2 gap-3">
          <a
            v-for="product in products.slice(0, 2)"
            :key="product.public_id"
            :href="`${base}/product/${product.slug}`"
            class="group flex min-w-0 flex-col rounded-xl bg-secondary/40 p-4"
          >
            <h3 class="line-clamp-2 text-base font-semibold">{{ product.name }}</h3>
            <p class="mt-1 text-xs text-muted-foreground">{{ product.category }}</p>
            <img
              v-if="productImages(product)[0]"
              :src="productImages(product)[0].url"
              :alt="productImages(product)[0].alt_text || ''"
              class="mt-5 aspect-[3/4] w-full rounded-lg object-cover motion-safe:transition-transform motion-safe:group-hover:scale-[1.02]"
            />
            <span class="mt-auto flex items-center gap-2 pt-4 text-sm font-medium">
              View product <ArrowRight class="h-4 w-4" aria-hidden="true" />
            </span>
          </a>
        </div>
        <div v-if="heroLayout === 'search'" class="marketplace-campaign min-w-0 overflow-hidden rounded-xl">
          <SiteBlockRenderer
            v-if="heroBlock && !manifest.identity.branding?.storefront?.hero?.enabled"
            :block="heroBlock"
            :assets="assetMap"
            :offerings="offerings"
            :identity="manifest.identity"
            :site-base="base"
            :currency="manifest.identity.currency"
          />
          <MarketplaceHero
            v-else
            :identity="manifest.identity"
            :featured-product="highlightedProduct"
            :base="base"
          />
        </div>
      </div>

      <div v-if="promoBlocks.length" class="mt-4">
        <SiteBlockRenderer
          v-for="block in promoBlocks"
          :key="block.id"
          :block="block"
          :assets="assetMap"
          :offerings="offerings"
          :identity="manifest.identity"
          :site-base="base"
          :currency="manifest.identity.currency"
        />
      </div>

      <section v-if="categoryTiles.length" class="mt-6 border bg-background p-4 sm:p-6" aria-labelledby="marketplace-categories-heading">
        <div class="flex items-end justify-between gap-4">
          <div>
            <p class="text-xs font-bold uppercase tracking-[0.12em] text-primary">Explore departments</p>
            <h2 id="marketplace-categories-heading" class="mt-1 text-2xl font-black tracking-tight">Browse categories</h2>
          </div>
          <ButtonAnchor :href="`${base}/shop`" variant="ghost" size="sm">
            View all
            <ArrowRight class="h-4 w-4" aria-hidden="true" />
          </ButtonAnchor>
        </div>
        <div class="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <a
            v-for="category in categoryTiles"
            :key="category.slug"
            :href="`${base}/shop?category=${encodeURIComponent(category.slug)}`"
            class="group overflow-hidden border bg-background transition hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-md"
          >
            <div class="aspect-[4/3] overflow-hidden bg-secondary/50">
              <img
                v-if="category.image"
                :src="category.image.url"
                :alt="category.image.alt_text || ''"
                class="h-full w-full object-cover transition duration-300 group-hover:scale-105"
              />
              <div v-else class="grid h-full place-items-center text-muted-foreground">
                <PackageOpen class="h-7 w-7" aria-hidden="true" />
              </div>
            </div>
            <p class="truncate px-3 py-3 text-sm font-extrabold">{{ category.name }}</p>
          </a>
        </div>
      </section>

      <MarketplaceProductShelf
        v-if="featuredProducts.length"
        class="mt-6"
        eyebrow="Featured picks"
        title="Products selected by the store"
        :products="featuredProducts"
        :identity="manifest.identity"
        :base="base"
      />

      <div v-if="visibleBlocks.length" class="mt-8 border bg-background px-4 sm:px-6 lg:px-8">
        <SiteBlockRenderer
          v-for="block in visibleBlocks"
          :key="block.id"
          :block="block"
          :assets="assetMap"
          :offerings="offerings"
          :identity="manifest.identity"
          :site-base="base"
          :currency="manifest.identity.currency"
        />
      </div>

      <MarketplaceProductShelf
        v-if="moreProducts.length"
        class="mt-6"
        eyebrow="More to discover"
        title="Continue browsing"
        :products="moreProducts"
        :identity="manifest.identity"
        :base="base"
      />
    </div>
  </MarketplaceStorefrontFrame>
</template>

<script setup>
import {
  ArrowRight,
  ChevronRight,
  LayoutGrid,
  PackageOpen,
} from 'lucide-vue-next'
import { productImages } from '@/utils/productImages'
import MarketplaceHero from './MarketplaceHero.vue'
import MarketplaceHomeCarousel from './MarketplaceHomeCarousel.vue'
import MarketplaceSearchHero from './MarketplaceSearchHero.vue'
import MarketplaceProductShelf from './MarketplaceProductShelf.vue'
import MarketplaceStorefrontFrame from './MarketplaceStorefrontFrame.vue'

const props = defineProps({
  manifest: { type: Object, required: true },
  offerings: { type: Array, default: () => [] },
  base: { type: String, required: true },
})

const config = useRuntimeConfig()
const heroLayout = computed(() => props.manifest.identity.branding?.storefront?.marketplace?.hero_layout || 'both')
const baseURL = import.meta.server ? config.apiInternalBaseUrl : config.public.apiBaseUrl
const slug = computed(() => props.manifest.identity.slug)
const assetMap = computed(() =>
  Object.fromEntries((props.manifest.assets || []).map((asset) => [asset.public_id, asset])),
)

const { data: discovery } = useAsyncData(
  `marketplace-home:${slug.value}`,
  () => $fetch(`public/${slug.value}/storefront/products/`, {
    baseURL,
    query: { page_size: 24 },
  }),
)

const products = computed(() => discovery.value?.results || props.offerings || [])
const categories = computed(() => discovery.value?.facets?.categories || [])
const highlightedProduct = computed(() => discovery.value?.highlighted || products.value[0] || null)
const heroBlock = computed(() =>
  (props.manifest.page.content?.blocks || []).find(
    (block) => ['commerce_hero', 'hero'].includes(block.type),
  ) || null,
)
const promoBlocks = computed(() =>
  (props.manifest.page.content?.blocks || []).filter((block) => block.type === 'promo_strip'),
)
const featuredProducts = computed(() => products.value.slice(0, 10))
const moreProducts = computed(() => products.value.slice(10, 20))
const visibleBlocks = computed(() =>
  (props.manifest.page.content?.blocks || []).filter(
    (block) => ![
      'hero',
      'commerce_hero',
      'promo_strip',
      'category_tiles',
      'product_grid',
      'product_rail',
      'featured_products',
    ].includes(block.type),
  ),
)
const categoryTiles = computed(() =>
  categories.value.slice(0, 6).map((category) => {
    const matchingProduct = products.value.find((product) => {
      const categoryValue = product.category
      return categoryValue === category.name || categoryValue === category.slug
    })
    return {
      ...category,
      image: category.image ? { url: category.image, alt_text: category.name } : productImages(matchingProduct)[0] || null,
    }
  }),
)
</script>

<style scoped>
.marketplace-campaign :deep([data-block-type]) {
  left: 0;
  width: 100%;
  transform: none;
}
.marketplace-campaign :deep(section),
.marketplace-campaign :deep([class*="min-h-"]) {
  min-height: 24rem;
}
.marketplace-campaign :deep(h1) {
  font-size: clamp(1.75rem, 2.5vw, 2.75rem);
  line-height: 1.08;
}
.marketplace-campaign :deep(section > div > div[class*="px-"]) {
  padding-inline: 1.5rem;
}
.marketplace-campaign :deep(section > div > div[class*="pb-"]) {
  padding-bottom: 5rem;
}
.marketplace-campaign :deep(section > div > div[class*="pt-"]) {
  padding-top: 2rem;
}
</style>
