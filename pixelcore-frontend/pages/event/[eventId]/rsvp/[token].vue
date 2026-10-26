<template>
  <div class="min-h-screen bg-black text-white">
    <div v-if="pending" class="grid min-h-screen place-items-center text-center">
      <div>
        <Loader2 class="mx-auto h-8 w-8 animate-spin" aria-hidden="true" />
        <p class="mt-4 text-sm text-white/60">Opening your invitation…</p>
      </div>
    </div>
    <div v-else-if="loadError || !payload" class="grid min-h-screen place-items-center px-5">
      <StatePanel
        class="max-w-xl border-white/15 bg-white/5 text-white"
        kind="error"
        title="Invitation unavailable"
        message="This private invitation link is invalid or has been replaced. Ask the organizer for a new link."
      />
    </div>
    <BuilderEventWebsite v-else-if="payload.event?.builder" :payload="payload" :endpoint="endpoint" @updated="payload = $event" />
    <EventRsvpResponsePage
      v-else
      :payload="payload"
      :endpoint="endpoint"
      @updated="payload = $event"
    />
  </div>
</template>

<script setup>
import { Loader2 } from 'lucide-vue-next'
import BuilderEventWebsite from '@/components/event/BuilderEventWebsite.vue'
import EventRsvpResponsePage from '@/components/event/EventRsvpResponsePage.vue'
import { normalizePublicAssetUrls } from '@/utils/publicAssetUrls'

definePageMeta({ layout: false })
useHead({meta:[{name:'robots',content:'noindex,nofollow'},{name:'referrer',content:'no-referrer'}]})
if (import.meta.server) { useResponseHeader('Cache-Control').value = 'no-store, private'; useResponseHeader('X-Robots-Tag').value = 'noindex, nofollow'; useResponseHeader('Referrer-Policy').value = 'no-referrer' }

const route = useRoute()
const config = useRuntimeConfig()
const apiBase = import.meta.server ? config.apiInternalBaseUrl : config.public.apiBaseUrl
const publicOrigin = import.meta.server ? useRequestURL().origin : ''
const endpoint = `public/events/${route.params.eventId}/rsvp/${route.params.token}/`

const { data: payload, pending, error: loadError, refresh } = await useAsyncData(
  `event-rsvp:${route.params.eventId}:${route.params.token}`,
  async () => {
    const response = await $fetch(endpoint, { baseURL: apiBase })
    if (!import.meta.server) return response
    return normalizePublicAssetUrls(response, {
      publicOrigin,
      internalApiBaseUrl: config.apiInternalBaseUrl,
    })
  },
)
</script>
