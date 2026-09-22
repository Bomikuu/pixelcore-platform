<template>
  <section class="overflow-hidden rounded-xl border bg-background">
    <div class="flex items-start gap-3 p-3">
      <span class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
        <MapPin class="h-5 w-5" aria-hidden="true" />
      </span>
      <div class="min-w-0">
        <p class="truncate text-sm font-bold">{{ location?.name || 'Venue location' }}</p>
        <p class="mt-1 line-clamp-2 text-xs leading-5 text-muted-foreground">{{ addressLabel }}</p>
      </div>
    </div>

    <div class="relative aspect-[16/9] border-t bg-muted/40">
      <Skeleton v-if="loading" class="absolute inset-0 h-full w-full rounded-none" />
      <img
        v-else-if="mapUrl"
        :src="mapUrl"
        :alt="`Map showing ${location?.name || 'the venue location'}`"
        class="h-full w-full object-cover"
      >
      <div v-else class="absolute inset-0 grid place-items-center p-4 text-center">
        <div>
          <Map class="mx-auto h-7 w-7 text-muted-foreground/45" aria-hidden="true" />
          <p class="mt-2 text-xs font-semibold">Map preview unavailable</p>
          <p class="mt-1 text-[11px] leading-4 text-muted-foreground">
            {{ mapError || 'Add a complete venue address to show its Mapbox preview.' }}
          </p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { Map, MapPin } from 'lucide-vue-next'
import { Skeleton } from '@/components/ui/skeleton'

const props = defineProps({
  location: {
    type: Object,
    default: null,
  },
})

const config = useRuntimeConfig()
const loading = ref(false)
const mapError = ref('')
const coordinates = ref(null)

const token = computed(() => String(config.public.mapboxAccessToken || ''))
const addressLabel = computed(() => {
  if (!props.location) return 'Choose a saved business location.'
  return [
    props.location.address,
    props.location.city,
    props.location.region,
    props.location.postal_code,
    props.location.country,
  ].filter(Boolean).join(', ') || 'No address saved for this location.'
})

const mapUrl = computed(() => {
  if (!token.value || !coordinates.value) return ''
  const [longitude, latitude] = coordinates.value
  const marker = `pin-s+0d2f2a(${longitude},${latitude})`
  return `https://api.mapbox.com/styles/v1/mapbox/streets-v12/static/${marker}/${longitude},${latitude},14,0/900x506@2x?access_token=${encodeURIComponent(token.value)}`
})

watch(
  () => props.location,
  resolveCoordinates,
  { immediate: true, deep: true },
)

async function resolveCoordinates(location) {
  coordinates.value = null
  mapError.value = ''
  if (!location) return

  if (location.longitude !== null && location.longitude !== undefined && location.latitude !== null && location.latitude !== undefined) {
    coordinates.value = [Number(location.longitude), Number(location.latitude)]
    return
  }
  if (!token.value) {
    mapError.value = 'Add NUXT_PUBLIC_MAPBOX_ACCESS_TOKEN to enable venue maps.'
    return
  }
  if (!addressLabel.value || addressLabel.value.startsWith('No address')) return

  loading.value = true
  try {
    const response = await $fetch('https://api.mapbox.com/search/geocode/v6/forward', {
      query: {
        q: addressLabel.value,
        access_token: token.value,
        limit: 1,
      },
    })
    const found = response?.features?.[0]?.geometry?.coordinates
    if (Array.isArray(found) && found.length >= 2) {
      coordinates.value = [Number(found[0]), Number(found[1])]
    } else {
      mapError.value = 'Mapbox could not locate this saved address.'
    }
  } catch {
    mapError.value = 'Mapbox could not load this venue preview.'
  } finally {
    loading.value = false
  }
}
</script>
