<template>
  <footer class="mt-12 border-t" :style="footerStyle">
    <div class="mx-auto max-w-screen-2xl px-4 py-10 sm:px-6 lg:px-8 lg:py-14">
      <div class="grid gap-10 sm:grid-cols-2 lg:grid-cols-[1.4fr_1fr_1fr_1fr]">
        <div>
          <a :href="base || '/'" class="flex items-center gap-3 font-black focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
            <img v-if="identity.logo" :src="identity.logo" alt="" class="h-11 w-11 object-contain" />
            <span>{{ identity.display_name }}</span>
          </a>
          <p class="mt-4 max-w-sm text-sm leading-6 opacity-70">
            {{ footer.description || identity.tagline || identity.description }}
          </p>
        </div>

        <nav aria-label="Shopping links">
          <h2 class="text-sm font-black">Shop</h2>
          <ul class="mt-4 space-y-3 text-sm">
            <li><a :href="`${base}/shop`" class="hover:underline">All products</a></li>
            <li><a :href="`${base}/account?tab=wishlist`" class="hover:underline">Saved products</a></li>
            <li><a :href="`${base}/cart`" class="hover:underline">Cart</a></li>
          </ul>
        </nav>

        <nav aria-label="Customer links">
          <h2 class="text-sm font-black">Your account</h2>
          <ul class="mt-4 space-y-3 text-sm">
            <li><a :href="`${base}/account`" class="hover:underline">Orders and profile</a></li>
            <li v-if="identity.contact_email"><a :href="`mailto:${identity.contact_email}`" class="hover:underline">Customer support</a></li>
            <li v-if="identity.contact_phone"><a :href="`tel:${identity.contact_phone}`" class="hover:underline">{{ identity.contact_phone }}</a></li>
          </ul>
        </nav>

        <nav v-if="footer.links?.length" aria-label="Policies">
          <h2 class="text-sm font-black">Information</h2>
          <ul class="mt-4 space-y-3 text-sm">
            <li v-for="link in footer.links" :key="`${link.label}-${link.url}`">
              <a :href="resolveLink(link.url)" class="hover:underline">{{ link.label }}</a>
            </li>
          </ul>
        </nav>
      </div>

      <div class="mt-10 flex flex-wrap items-center justify-between gap-3 border-t border-current/15 pt-6 text-xs opacity-70">
        <p>{{ footer.copyright_text || `© ${new Date().getFullYear()} ${identity.display_name}` }}</p>
        <p>{{ identity.currency }} · Powered by PixelCore</p>
      </div>
    </div>
  </footer>
</template>

<script setup>
const props = defineProps({
  identity: { type: Object, required: true },
  base: { type: String, required: true },
  builderLayout: {type:Object,default:()=>({})},
});

const builderFooter = computed(() => (props.builderLayout?.revisionId ? props.builderLayout.regions?.find(n=>n.type==='footer') : undefined))
const footer = computed(() => props.identity.branding?.storefront?.footer || {});
const footerStyle = computed(() => ({
  backgroundColor: builderFooter.value?.style?.backgroundColor || footer.value.background_color || props.identity.branding?.secondary_color,
  color: builderFooter.value?.style?.color || footer.value.text_color || props.identity.branding?.text_color,
}))

function resolveLink(value) {
  return value?.startsWith("/")
    ? `${props.base}${value === "/" ? "" : value}`
    : value;
}
</script>
