<template>
  <section class="workspace-page space-y-5">
    <StatePanel
      v-if="loading"
      kind="loading"
      title="Loading event workspace"
      message="Retrieving the event, venue plan, and guest access settings."
    />
    <StatePanel
      v-else-if="error"
      kind="error"
      title="Event workspace unavailable"
      :message="error"
    >
      <Button variant="outline" type="button" @click="load">Try again</Button>
    </StatePanel>
    <EventRsvpWorkspace
      v-else
      mode="detail"
      :event-id="eventId"
      :business-id="business.activeBusiness.public_id"
      :locations="locations"
      :layouts="layouts"
      :resources="resources"
      :resource-types="resourceTypes"
      :staff="staff"
      :products="products"
    />
  </section>
</template>

<script setup>
import { Button } from '@/components/ui/button'
import EventRsvpWorkspace from '@/components/scheduling/EventRsvpWorkspace.vue'

useHead({ title: 'Event details | PixelCore' })

const route = useRoute()
const business = useBusinessStore()
const { apiFetch } = useApiClient()
const locations = ref([])
const layouts = ref([])
const resources = ref([])
const resourceTypes = ref([])
const staff = ref([])
const products = ref([])
const loading = ref(true)
const error = ref('')

const eventId = computed(() => String(route.params.eventId || ''))

onMounted(load)

async function load() {
  loading.value = true
  error.value = ''
  try {
    if (!business.activeBusiness) await business.loadBusinesses()
    const businessId = business.activeBusiness?.public_id
    if (!businessId) throw new Error('Choose a business before opening an event.')

    const [locationResponse, layoutResponse, resourceResponse, resourceTypeResponse, staffResponse, productResponse] = await Promise.all([
      apiFetch(`businesses/${businessId}/locations/?page_size=100`),
      apiFetch(`businesses/${businessId}/resource-layouts/?page_size=100`),
      apiFetch(`businesses/${businessId}/resources/?page_size=100`),
      apiFetch(`businesses/${businessId}/resource-types/?page_size=100`),
      apiFetch(`businesses/${businessId}/staff/?page_size=100`),
      apiFetch(`businesses/${businessId}/offerings/?page_size=100`),
    ])
    locations.value = normalizeList(locationResponse)
    layouts.value = normalizeList(layoutResponse)
    resources.value = normalizeList(resourceResponse)
    resourceTypes.value = normalizeList(resourceTypeResponse)
    staff.value = normalizeList(staffResponse)
    products.value = normalizeList(productResponse)
  } catch (requestError) {
    error.value = requestError?.data?.error?.message
      || requestError?.data?.detail
      || requestError?.message
      || 'This event could not be loaded.'
  } finally {
    loading.value = false
  }
}

function normalizeList(response) {
  return Array.isArray(response) ? response : response?.results || []
}
</script>
