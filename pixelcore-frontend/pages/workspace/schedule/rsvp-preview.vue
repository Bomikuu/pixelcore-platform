<template>
  <div class="min-h-screen bg-background">
    <div v-if="loading" class="grid min-h-screen place-items-center px-5">
      <div class="text-center text-muted-foreground" aria-live="polite">
        <Loader2 class="mx-auto h-8 w-8 animate-spin" aria-hidden="true" />
        <p class="mt-4 text-sm">Preparing the RSVP preview…</p>
      </div>
    </div>

    <div v-else-if="loadError || !payload" class="grid min-h-screen place-items-center px-5">
      <StatePanel
        class="w-full max-w-xl"
        kind="error"
        title="RSVP preview unavailable"
        :message="loadError || 'The preview data could not be loaded.'"
      >
        <ButtonLink :to="eventWorkspaceUrl" variant="outline">
          <ArrowLeft class="h-4 w-4" aria-hidden="true" />
          Return to event workspace
        </ButtonLink>
      </StatePanel>
    </div>

    <EventRsvpResponsePage
      v-else
      :payload="payload"
      preview-mode
    />
  </div>
</template>

<script setup>
import { ArrowLeft, Loader2 } from 'lucide-vue-next'
import EventRsvpResponsePage from '@/components/event/EventRsvpResponsePage.vue'
import { ButtonLink } from '@/components/ui/button-link'
import StatePanel from '@/components/workspace/StatePanel.vue'
import { createRsvpPreviewPayload } from '@/utils/eventRsvpConfig'

definePageMeta({
  layout: false,
  path: '/workspace/schedule/events/:eventId/rsvp-preview',
})

useHead({
  title: 'RSVP preview | PixelCore',
  meta: [{ name: 'robots', content: 'noindex,nofollow' }],
})

const route = useRoute()
const business = useBusinessStore()
const { apiFetch } = useApiClient()
const loading = ref(true)
const loadError = ref('')
const payload = ref(null)

const eventId = computed(() => String(route.params.eventId || ''))
const eventWorkspaceUrl = computed(() => `/workspace/schedule/events/${eventId.value}?tab=rsvp`)

onMounted(loadPreview)

async function loadPreview() {
  loading.value = true
  loadError.value = ''
  try {
    const requestedBusinessId = Array.isArray(route.query.business)
      ? route.query.business[0]
      : String(route.query.business || '')

    if (!business.activeBusiness) await business.loadBusinesses()
    const businessId = requestedBusinessId || business.activeBusiness?.public_id
    if (!businessId) throw new Error('Choose a business before opening the RSVP preview.')

    const [event, website] = await Promise.all([
      apiFetch(`businesses/${businessId}/venue-events/${eventId.value}/`),
      apiFetch(`businesses/${businessId}/venue-events/${eventId.value}/website/`),
    ])
    payload.value = createRsvpPreviewPayload({ event, website })
  } catch (error) {
    loadError.value = error?.data?.error?.message
      || error?.data?.detail
      || error?.message
      || 'Reload the event workspace and try again.'
  } finally {
    loading.value = false
  }
}
</script>
