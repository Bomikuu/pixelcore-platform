<template>
  <div
    data-business-theme
    data-storefront-layout="marketplace"
    :style="pageStyle"
    class="min-h-screen overflow-x-clip bg-background text-foreground"
  >
    <StorefrontBanner :identity="identity" :base="base" />
    <MarketplaceHeader :identity="identity" :navigation="navigation" :base="base" :builder-layout="builderLayout" />
    <main :class="fullBleed ? 'w-full' : 'mx-auto w-full max-w-screen-2xl px-4 py-6 sm:px-6 lg:px-8'">
      <slot />
    </main>
    <StorefrontCustomSection :identity="identity" />
    <MarketplaceFooter :identity="identity" :base="base" :builder-layout="builderLayout" />
    <StorefrontPopup :identity="identity" :base="base" />
    <CartDrawer :base="base" :currency="identity.currency" />
  </div>
</template>

<script setup>
import MarketplaceFooter from "./MarketplaceFooter.vue";
import MarketplaceHeader from "./MarketplaceHeader.vue";
import StorefrontBanner from "@/components/site/StorefrontBanner.vue";
import StorefrontCustomSection from "@/components/site/StorefrontCustomSection.vue";
import StorefrontPopup from "@/components/site/StorefrontPopup.vue";
import { businessThemeStyle, storefrontBackgroundStyle } from "@/utils/businessTheme";

const props = defineProps({
  identity: { type: Object, required: true },
  navigation: { type: Array, default: () => [] },
  base: { type: String, required: true },
  builderLayout: {type:Object,default:()=>({})},
  fullBleed: { type: Boolean, default: false },
});

const pageStyle = computed(() => ({
  ...businessThemeStyle(props.identity),
  ...storefrontBackgroundStyle(props.identity),
  fontSize: props.identity.branding?.typography?.base_font_size || "16px",
}));

useHead(
  computed(() => ({
    link: props.identity.favicon ? [{ rel: "icon", href: props.identity.favicon }] : [],
    meta: [
      {
        name: "theme-color",
        content: props.identity.branding?.primary_color || "#0F766E",
      },
    ],
  })),
);
</script>
