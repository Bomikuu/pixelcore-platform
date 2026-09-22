<template>
  <MarketplaceHomePage
    v-if="isMarketplaceHome"
    :manifest="manifest"
    :offerings="offerings"
    :base="base"
  />
  <MarketplaceStorefrontFrame
    v-else-if="isMarketplace"
    :identity="manifest.identity"
    :navigation="manifest.site.navigation"
    :base="base"
  >
    <SiteBlockRenderer
      v-for="block in manifest.page.content?.blocks || []"
      :key="block.id"
      :block="block"
      :assets="assetMap"
      :offerings="offerings"
      :identity="manifest.identity"
      :site-base="base"
      :currency="manifest.identity.currency"
    />
  </MarketplaceStorefrontFrame>
  <div
    v-else
    data-business-theme
    :data-storefront-mode="storefrontMode"
    :style="pageStyle"
    class="min-h-screen overflow-x-clip bg-background text-foreground"
  >
    <StorefrontBanner :identity="manifest.identity" :base="base" />
    <StorefrontHeader :identity="manifest.identity" :navigation="manifest.site.navigation" :base="base" />
    <StorefrontHero v-if="showGlobalHero" :identity="manifest.identity" :base="base" />
    <main class="mx-auto max-w-[var(--content-max-width)] px-4 sm:px-6 lg:px-10">
      <SiteBlockRenderer v-for="block in visibleBlocks" :key="block.id" :block="block" :assets="assetMap" :offerings="offerings" :identity="manifest.identity" :site-base="base" :currency="manifest.identity.currency" />
    </main>
    <StorefrontHomeClosing v-if="manifest.page.page_type === 'home' && manifest.identity.enabled_modules?.includes('sell')" :identity="manifest.identity" :offerings="offerings" :base="base" :show-categories="!visibleBlocks.some((block) => block.type === 'category_tiles' && block.settings?.items?.length)" />
    <StorefrontCustomSection :identity="manifest.identity" />
    <StorefrontFooter :identity="manifest.identity" :base="base" />
    <StorefrontPopup :identity="manifest.identity" :base="base" />
    <CartDrawer :base="base" :currency="manifest.identity.currency" />
  </div>
</template>

<script setup>
import MarketplaceHomePage from '@/components/marketplace/MarketplaceHomePage.vue'
import MarketplaceStorefrontFrame from '@/components/marketplace/MarketplaceStorefrontFrame.vue'
import StorefrontBanner from './StorefrontBanner.vue'
import StorefrontCustomSection from './StorefrontCustomSection.vue'
import StorefrontFooter from './StorefrontFooter.vue'
import StorefrontHero from './StorefrontHero.vue'
import StorefrontHomeClosing from './StorefrontHomeClosing.vue'
import StorefrontPopup from './StorefrontPopup.vue'
import { businessThemeStyle, storefrontBackgroundStyle } from '@/utils/businessTheme'

const props = defineProps({ manifest: { type: Object, required: true }, offerings: { type: Array, default: () => [] }, base: { type: String, required: true } })
const assetMap = computed(() => Object.fromEntries((props.manifest.assets || []).map((asset) => [asset.public_id, asset])))
const branding = computed(() => props.manifest.identity.branding || {})
const isMarketplace = computed(() => branding.value.storefront?.layout === 'marketplace')
const isMarketplaceHome = computed(() =>
  isMarketplace.value && props.manifest.page.page_type === 'home',
)
const storefrontMode = computed(() => branding.value.storefront?.mode === 'luxury' ? 'luxury' : 'default')
const showGlobalHero = computed(() => props.manifest.page.page_type === 'home' && branding.value.storefront?.hero?.enabled)
const visibleBlocks = computed(() => {
  const blocks = props.manifest.page.content?.blocks || []
  return showGlobalHero.value ? blocks.filter((block) => !['hero', 'commerce_hero'].includes(block.type)) : blocks
})
const pageStyle = computed(() => ({
  ...businessThemeStyle(props.manifest.identity),
  ...storefrontBackgroundStyle(props.manifest.identity),
  fontSize: branding.value.typography?.base_font_size || '16px',
}))

useHead(computed(() => ({
  link: props.manifest.identity.favicon ? [{ rel: 'icon', href: props.manifest.identity.favicon }] : [],
  meta: [{ name: 'theme-color', content: branding.value.primary_color || '#165B4C' }],
})))
</script>
