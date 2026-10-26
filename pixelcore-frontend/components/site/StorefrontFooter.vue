<template>
  <footer :data-builder-variant="builderFooter?.props?.variant" :style="{ backgroundColor: builderFooter?.style?.backgroundColor || footer.background_color, color: builderFooter?.style?.color || footer.text_color }">
    <div class="mx-auto max-w-[var(--content-max-width)] px-4 pb-6 pt-12 sm:px-6 lg:px-10 lg:pt-16">
      <div class="grid gap-x-10 gap-y-10 pb-12 sm:grid-cols-2 lg:grid-cols-[minmax(0,1.5fr)_1fr_1fr_1fr]">
        <div class="max-w-md sm:col-span-2 lg:col-span-1">
          <a :href="base || '/'" class="inline-flex min-h-11 items-center gap-3 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4" :aria-label="`${identity.display_name} home`">
            <img v-if="logo" :src="logo" alt="" class="h-12 max-w-32 object-contain object-left" />
            <span class="display-face text-xl font-semibold">{{ identity.display_name }}</span>
          </a>
          <p v-if="footer.description || identity.tagline || identity.description" class="mt-5 max-w-sm text-sm leading-7">{{ footer.description || identity.tagline || identity.description }}</p>
          <SandboxedCustomization v-if="footer.custom_html" :html="footer.custom_html" :css="footer.custom_css" title="Custom footer content" height-class="mt-4 h-32" />
        </div>
        <nav v-if="canShop" aria-label="Footer shop">
          <h2 class="text-sm font-bold">Explore</h2>
          <ul class="mt-4 space-y-1">
            <li v-for="link in shopLinks" :key="link.path"><a :href="resolveLink(link.path)" class="inline-flex min-h-10 items-center text-sm underline-offset-4 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4">{{ link.label }}</a></li>
          </ul>
        </nav>
        <nav v-if="footer.links?.length" aria-label="Policies and information">
          <h2 class="text-sm font-bold">Information & policies</h2>
          <ul class="mt-4 space-y-1">
            <li v-for="link in footer.links" :key="`${link.label}-${link.url}`"><a :href="resolveLink(link.url)" class="inline-flex min-h-10 items-center text-sm underline-offset-4 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4" :style="{ color: footer.link_color }">{{ link.label }}</a></li>
          </ul>
        </nav>
        <div v-if="identity.contact_email || identity.contact_phone || socials.length">
          <h2 class="text-sm font-bold">Get in touch</h2>
          <address class="mt-4 space-y-1 text-sm not-italic">
            <a v-if="identity.contact_email" :href="`mailto:${identity.contact_email}`" class="flex min-h-10 items-center gap-2 break-all underline-offset-4 hover:underline"><Mail class="h-4 w-4 shrink-0" aria-hidden="true" />{{ identity.contact_email }}</a>
            <a v-if="identity.contact_phone" :href="`tel:${identity.contact_phone}`" class="flex min-h-10 items-center gap-2 underline-offset-4 hover:underline"><Phone class="h-4 w-4 shrink-0" aria-hidden="true" />{{ identity.contact_phone }}</a>
          </address>
          <nav v-if="socials.length" class="mt-5 flex flex-wrap gap-2" aria-label="Social media">
            <a
              v-for="social in socials"
              :key="social.platform"
              :href="social.url"
              target="_blank"
              rel="noopener noreferrer"
              class="group inline-flex h-10 w-10 items-center justify-center rounded-full border border-current/25 transition-colors hover:bg-current focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 motion-reduce:transition-none"
              :style="{ '--social-hover-color': footer.background_color }"
              :aria-label="`${platformLabel(social.platform)} (opens in a new tab)`"
              :title="platformLabel(social.platform)"
            >
              <SocialPlatformIcon :platform="social.platform" class="h-[1.125rem] w-[1.125rem] group-hover:text-[var(--social-hover-color)]" />
            </a>
          </nav>
        </div>
      </div>
      <div class="flex flex-wrap items-center justify-between gap-x-8 gap-y-3 border-t border-current/20 py-6 text-xs">
        <p>{{ footer.copyright_text || `© ${new Date().getFullYear()} ${identity.display_name}` }}</p>
        <div class="flex items-center gap-5"><span v-if="identity.currency">{{ identity.currency }}</span><span>Powered by PixelCore</span></div>
      </div>
    </div>
  </footer>
</template>
<script setup>
import { Mail, Phone } from 'lucide-vue-next'
import SandboxedCustomization from '@/components/business/SandboxedCustomization.vue'
import SocialPlatformIcon from './SocialPlatformIcon.vue'
const props = defineProps({ identity: { type: Object, required: true }, base: { type: String, required: true }, builderLayout: {type:Object,default:()=>({})} })
const builderFooter = computed(() => props.builderLayout?.revisionId ? props.builderLayout.regions?.find(n => n.type === 'footer') : undefined)
const footer = computed(() => props.identity.branding?.storefront?.footer || {})
const socials = computed(() => props.identity.branding?.socials || [])
const assets = computed(() => props.identity.branding_assets || {})
const logo = computed(() => assets.value[footer.value.logo_asset_id]?.url || props.identity.logo)
const canShop = computed(() => props.identity.enabled_modules?.includes('sell'))
const shopLinks = [{ label: 'All products', path: '/shop' }, { label: 'Saved items', path: '/account?tab=wishlist' }, { label: 'Your account', path: '/account' }, { label: 'Shopping bag', path: '/cart' }]
function resolveLink(value) { return value?.startsWith('/') ? `${props.base}${value === '/' ? '' : value}` : value }
function platformLabel(platform) {
  return ({ facebook: 'Facebook', instagram: 'Instagram', tiktok: 'TikTok', x: 'X', twitter: 'X', youtube: 'YouTube', linkedin: 'LinkedIn' })[platform] || platform
}
</script>

<style scoped>
[data-builder-variant="compact"] > div > div:first-child { padding-top:2rem;padding-bottom:2rem; }
[data-builder-variant="wedding"] { text-align:center; }
[data-builder-variant="wedding"] nav { display:none; }
</style>
