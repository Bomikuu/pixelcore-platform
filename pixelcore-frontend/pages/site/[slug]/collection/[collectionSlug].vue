<template>
  <StatePanel v-if="pending" kind="loading" title="Loading collection" message="Retrieving published products." />
  <StatePanel v-else-if="error || !identity || !collection" kind="error" title="Collection unavailable" message="This collection is not published." />
  <StorefrontFrame v-else :identity="identity" :navigation="navigation" :base="base" full-bleed>
    <MarketplaceCollection
      v-if="isMarketplace"
      :collection="collection"
      :products="products"
      :identity="identity"
      :base="base"
      :slug="String(route.params.slug)"
    />
    <template v-else>
      <CollectionHero
        v-if="collection.hero_settings?.enabled !== false"
        :collection="collection"
        :products="products"
        :base="base"
        :mode="isLuxury ? 'luxury' : 'default'"
      />
      <section v-else class="border-b px-5 py-16 sm:px-10 lg:px-[clamp(3rem,6vw,7rem)] lg:py-24">
        <h1 class="display-face mt-4 max-w-5xl text-5xl font-medium leading-[0.98] tracking-[-0.035em] sm:text-6xl lg:text-8xl">{{ collection.name }}</h1>
        <p class="mt-6 max-w-2xl leading-7 text-muted-foreground">{{ collection.description }}</p>
      </section>
    <section id="collection-products" class="scroll-mt-20" aria-label="Collection products">
      <div class="flex flex-wrap items-center justify-between gap-3 border-b px-5 py-5 sm:px-10"><p class="text-sm text-muted-foreground">{{ products.length }} products in {{ collection.name }}</p><a :href="`${base}/shop`" class="text-sm underline underline-offset-4">Explore all products</a></div>
      <LuxuryProductGrid v-if="isLuxury" :products="products" :base="base" :slug="String(route.params.slug)" :currency="identity.currency" />
      <div v-else-if="products.length" class="mx-auto grid max-w-[var(--content-max-width)] gap-x-5 gap-y-12 px-5 py-10 sm:grid-cols-2 sm:px-10 lg:grid-cols-3 xl:grid-cols-4">
        <ProductCard v-for="product in products" :key="product.public_id" :product="product" :base="base" :slug="route.params.slug" :currency="identity.currency" />
      </div>
      <StatePanel v-else class="mt-10" title="No products in this collection" message="Published products will appear here when assigned." />
    </section>
    </template>
  </StorefrontFrame>
</template>

<script setup>
import CollectionHero from '~/components/storefront/LuxuryCollectionHero.vue'
import LuxuryProductGrid from '~/components/storefront/LuxuryProductGrid.vue'
import MarketplaceCollection from '@/components/marketplace/MarketplaceCollection.vue'
definePageMeta({ layout: 'storefront' })
const route = useRoute()
const { identity, navigation, pending: identityPending, error: identityError, baseURL, siteBase: base } = useStorefrontContext(route.params.slug)
const { data: collection, pending: collectionPending, error: collectionError } = useAsyncData(
  `collection:${route.params.slug}:${route.params.collectionSlug}`,
  () => $fetch(`public/${route.params.slug}/storefront/collections/${route.params.collectionSlug}/`, { baseURL }),
)
const { data: catalog, pending: catalogPending, error: catalogError } = useAsyncData(
  `collection-products:${route.params.slug}:${route.params.collectionSlug}`,
  () => $fetch(`public/${route.params.slug}/storefront/products/?collection=${encodeURIComponent(route.params.collectionSlug)}&page_size=60`, { baseURL }),
)
const pending = computed(() => identityPending.value || collectionPending.value || catalogPending.value)
const error = computed(() => identityError.value || collectionError.value || catalogError.value)
const products = computed(() => catalog.value?.results || [])
const isLuxury = computed(() => identity.value?.branding?.storefront?.mode === 'luxury')
const isMarketplace = computed(() => identity.value?.branding?.storefront?.layout === 'marketplace')

useHead(() => collection.value && identity.value ? {
  title: `${collection.value.name} | ${identity.value.display_name}`,
  meta: [{ name: 'description', content: collection.value.description || `Shop ${collection.value.name}.` }],
} : {})
</script>
