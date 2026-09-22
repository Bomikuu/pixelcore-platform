<template>
  <aside v-if="banner.enabled && visible" class="relative z-50 flex min-h-10 w-full items-center justify-center gap-x-3 gap-y-1 px-12 py-2 text-center text-xs font-bold sm:text-sm" :style="{ backgroundColor: banner.background_color, color: banner.text_color }" role="status" aria-label="Store announcement">
    <Megaphone class="hidden h-4 w-4 shrink-0 sm:block" aria-hidden="true" />
    <span>{{ banner.text }}</span><a v-if="banner.link_label && banner.link_url" :href="link" class="font-extrabold underline decoration-current/40 underline-offset-4 transition-opacity hover:opacity-75">{{ banner.link_label }}</a>
    <Button v-if="banner.dismissible !== false" type="button" variant="ghost" size="icon" class="absolute right-2 h-8 w-8 text-current hover:bg-white/10 hover:text-current" aria-label="Dismiss announcement" @click="dismiss"><X class="h-4 w-4" /></Button>
  </aside>
</template>
<script setup>
import { Megaphone, X } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
const props = defineProps({ identity: { type: Object, required: true }, base: { type: String, required: true } })
const banner = computed(() => props.identity.branding?.storefront?.banner || {})
const link = computed(() => banner.value.link_url?.startsWith('/') ? `${props.base}${banner.value.link_url === '/' ? '' : banner.value.link_url}` : banner.value.link_url)
function fingerprint(value) { let hash = 5381; for (let index = 0; index < value.length; index += 1) hash = ((hash << 5) + hash) ^ value.charCodeAt(index); return (hash >>> 0).toString(36) }
const bannerFingerprint = fingerprint(`${banner.value.text || ''}|${banner.value.link_label || ''}|${banner.value.link_url || ''}`)
const cookieSlug = String(props.identity.slug || 'store').replace(/[^a-z0-9_-]/gi, '')
const dismissal = useCookie(`pixelcore_banner_${cookieSlug}_${bannerFingerprint}`, { default: () => '', path: '/', sameSite: 'lax' })
const visible = computed(() => dismissal.value !== 'dismissed')
function dismiss() { dismissal.value = 'dismissed' }
</script>
