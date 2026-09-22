<template>
  <MarketplaceStorefrontFrame
    v-if="isMarketplace"
    :identity="identity"
    :navigation="navigation"
    :base="base"
    :full-bleed="fullBleed"
  >
    <slot />
  </MarketplaceStorefrontFrame>
  <div
    v-else
    data-business-theme
    :data-storefront-mode="storefrontMode"
    :style="pageStyle"
    class="min-h-screen overflow-x-clip bg-background text-foreground"
  >
    <StorefrontBanner :identity="identity" :base="base" />
    <StorefrontHeader :identity="identity" :navigation="navigation" :base="base" />
    <main :class="fullBleed ? 'w-full' : 'mx-auto max-w-[var(--content-max-width)] px-4 py-8 sm:px-6 lg:px-10 lg:py-12'"><slot /></main>
    <StorefrontCustomSection :identity="identity" />
    <StorefrontFooter :identity="identity" :base="base" />
    <StorefrontPopup :identity="identity" :base="base" />
    <CartDrawer :base="base" :currency="identity.currency" />
  </div>
</template>
<script setup>
import MarketplaceStorefrontFrame from '@/components/marketplace/MarketplaceStorefrontFrame.vue'
import StorefrontBanner from './StorefrontBanner.vue'
import StorefrontCustomSection from './StorefrontCustomSection.vue'
import StorefrontFooter from './StorefrontFooter.vue'
import StorefrontPopup from './StorefrontPopup.vue'
import { businessThemeStyle, storefrontBackgroundStyle } from '@/utils/businessTheme'

const props = defineProps({ identity: { type: Object, required: true }, navigation: { type: Array, default: () => [] }, base: { type: String, required: true }, fullBleed: { type: Boolean, default: false } })
const isMarketplace = computed(() => props.identity.branding?.storefront?.layout === 'marketplace')
const storefrontMode = computed(() => props.identity.branding?.storefront?.mode === 'luxury' ? 'luxury' : 'default')
const pageStyle = computed(() => ({
  ...businessThemeStyle(props.identity),
  ...storefrontBackgroundStyle(props.identity),
  fontSize: props.identity.branding?.typography?.base_font_size || '16px',
}))

useHead(computed(() => ({
  link: props.identity.favicon ? [{ rel: 'icon', href: props.identity.favicon }] : [],
  meta: [{ name: 'theme-color', content: props.identity.branding?.primary_color || '#165B4C' }],
})))
</script>
