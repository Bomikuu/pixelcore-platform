<template>
  <main class="min-h-screen" :style="screenStyle">
    <StatePanel v-if="pending" class="mx-auto max-w-xl pt-24" kind="loading" title="Loading display" message="Retrieving the latest published layout." />
    <StatePanel v-else-if="error" class="mx-auto max-w-xl pt-24" kind="error" title="Display unavailable" message="This display may be unpublished, offline, or no longer active." />
    <section v-else-if="hasInteractiveLayout" class="h-screen w-screen overflow-hidden">
      <InteractiveDisplayCanvas
        :settings="publication.settings"
        :offerings="publication.offerings"
        :assets="publication.assets"
        :business-name="publication.business_identity?.display_name"
        :background-url="publication.background_asset_url || ''"
        :currency="publication.business_identity?.currency || 'PHP'"
      />
    </section>
    <section v-else class="relative flex min-h-screen flex-col overflow-hidden p-7 sm:p-12 lg:p-16">
      <img v-if="publication.background_asset_url" :src="publication.background_asset_url" alt="" class="absolute inset-0 h-full w-full object-cover opacity-25" />
      <header class="relative flex items-start justify-between gap-6 border-b border-current/20 pb-6"><div><p class="text-xs font-extrabold uppercase tracking-[.16em] opacity-65">{{ publication.kind.replaceAll('_', ' ') }}</p><h1 class="display-face mt-3 text-5xl font-semibold leading-none sm:text-7xl">{{ publication.settings?.heading || publication.name }}</h1></div><PixelCoreMark class="opacity-60" /></header>
      <p v-if="publication.settings?.message" class="relative mt-6 max-w-2xl text-lg leading-8 opacity-75">{{ publication.settings.message }}</p>
      <div class="relative mt-auto grid gap-x-8 gap-y-5 pt-12 sm:grid-cols-2 lg:grid-cols-3">
        <article v-for="offering in publication.offerings" :key="offering.public_id" class="border-t border-current/25 py-5"><div class="flex items-start justify-between gap-5"><h2 class="text-xl font-extrabold">{{ offering.name }}</h2><strong class="shrink-0">{{ money(offering.base_price) }}</strong></div><p class="mt-2 text-sm leading-6 opacity-70">{{ offering.summary }}</p></article>
      </div>
      <footer class="relative mt-8 flex justify-between border-t border-current/20 pt-4 text-xs opacity-60"><span>{{ publication.template.replaceAll('_', ' ') }}</span><span>Updated {{ formatDate(publication.updated_at) }}</span></footer>
    </section>
  </main>
</template>

<script setup>
import InteractiveDisplayCanvas from '@/components/display/InteractiveDisplayCanvas.vue'

definePageMeta({ layout: 'storefront' })
const route = useRoute(); const config = useRuntimeConfig(); const baseURL = import.meta.server ? config.apiInternalBaseUrl : config.public.apiBaseUrl
const { data: publication, pending, error } = await useFetch(`public/displays/${route.params.shareKey}/`, { baseURL })
const hasInteractiveLayout = computed(() => Boolean(publication.value?.settings?.builder?.slides?.[0]?.elements?.length))
const screenStyle = computed(() => ({ backgroundColor: publication.value?.settings?.background || '#102a2a', color: publication.value?.settings?.foreground || '#f7f3ea' }))
const money = (value) => new Intl.NumberFormat('en-PH', { style: 'currency', currency: publication.value?.business_identity?.currency || 'PHP' }).format(Number(value || 0))
const formatDate = (value) => new Intl.DateTimeFormat('en-PH', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
</script>
