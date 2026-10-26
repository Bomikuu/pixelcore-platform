<template>
  <div class="min-h-screen bg-black text-white">
    <div v-if="pending" class="grid min-h-screen place-items-center text-center">
      <div>
        <Loader2 class="mx-auto h-8 w-8 animate-spin" aria-hidden="true" />
        <p class="mt-4 text-sm text-white/60">Opening event website…</p>
      </div>
    </div>
    <div v-else-if="loadError || !payload" class="grid min-h-screen place-items-center px-5">
      <StatePanel
        class="max-w-xl border-white/15 bg-white/5 text-white"
        kind="error"
        title="Event website unavailable"
        message="This event website has not been published or is no longer available."
      />
    </div>
    <WebsitePage v-else-if="payload.event?.builder" :document="payload.event.builder.document" :data="payload.event.builder.data" :base-url="payload.event.builder.baseUrl" />
    <WeddingInvitationPage v-else :payload="payload" @refresh="refresh" />
  </div>
</template>

<script setup>
import { pageHead } from '@sitebuilder/core'
import { WebsitePage } from '@sitebuilder/vue'
import { Loader2 } from 'lucide-vue-next'
import WeddingInvitationPage from '@/components/event/WeddingInvitationPage.vue'
import { normalizePublicAssetUrls } from '@/utils/publicAssetUrls'

definePageMeta({ layout: false })

const route = useRoute()
const config = useRuntimeConfig()
const apiBase = import.meta.server ? config.apiInternalBaseUrl : config.public.apiBaseUrl
const publicOrigin = import.meta.server ? useRequestURL().origin : ''
const endpoint = `public/events/${route.params.eventId}/website/`

const { data: payload, pending, error: loadError, refresh } = await useAsyncData(
  `event-website:${route.params.eventId}`,
  async () => {
    const response = await $fetch(endpoint, { baseURL: apiBase })
    if (!import.meta.server) return response
    return normalizePublicAssetUrls(response, {
      publicOrigin,
      internalApiBaseUrl: config.apiInternalBaseUrl,
    })
  },
)
useHead(() => payload.value?.event?.builder ? pageHead(payload.value.event.builder.document,payload.value.event.builder.data) : {})
</script>
