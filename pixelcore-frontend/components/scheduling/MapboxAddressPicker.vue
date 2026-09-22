<template>
  <div class="space-y-3">
    <Popover v-model:open="open">
      <PopoverAnchor as-child>
        <div class="relative">
          <Search class="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" aria-hidden="true" />
          <Input
            :id="id"
            v-model="query"
            class="pl-9 pr-10"
            autocomplete="off"
            placeholder="Search an address or venue"
            role="combobox"
            :aria-expanded="open"
            :aria-controls="`${id}-suggestions`"
            @focus="openSuggestions"
            @input="queueSearch"
          />
          <Loader2 v-if="loading" class="pointer-events-none absolute right-3 top-3 h-4 w-4 animate-spin text-muted-foreground" aria-hidden="true" />
        </div>
      </PopoverAnchor>
      <PopoverContent
        :id="`${id}-suggestions`"
        align="start"
        class="w-[var(--radix-popover-trigger-width)] p-1"
        :side-offset="6"
        @open-auto-focus.prevent
      >
        <div v-if="suggestions.length" class="max-h-72 overflow-y-auto" role="listbox">
          <Button
            v-for="suggestion in suggestions"
            :key="suggestion.id"
            type="button"
            variant="ghost"
            class="h-auto w-full justify-start rounded-lg px-3 py-3 text-left"
            role="option"
            @click="selectSuggestion(suggestion)"
          >
            <MapPin class="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
            <span class="min-w-0">
              <span class="block truncate text-sm font-semibold">{{ suggestion.name }}</span>
              <span class="mt-0.5 block whitespace-normal text-xs leading-5 text-muted-foreground">{{ suggestion.address }}</span>
            </span>
          </Button>
        </div>
        <div v-else class="p-3 text-sm leading-6 text-muted-foreground">
          {{ searchMessage }}
        </div>
      </PopoverContent>
    </Popover>

    <div class="relative aspect-[16/6] min-h-44 overflow-hidden rounded-xl border bg-muted/30">
      <img
        v-if="mapPreviewUrl"
        :src="mapPreviewUrl"
        :alt="`Map pin for ${venueName || query || 'the selected venue'}`"
        class="h-full w-full object-cover"
      >
      <div v-else class="absolute inset-0 grid place-items-center p-6 text-center">
        <div>
          <MapPinned class="mx-auto h-8 w-8 text-muted-foreground/50" aria-hidden="true" />
          <p class="mt-3 text-sm font-semibold">Choose a Mapbox suggestion</p>
          <p class="mt-1 text-xs leading-5 text-muted-foreground">The selected place will add the map pin automatically.</p>
        </div>
      </div>
      <div v-if="mapPreviewUrl" class="pointer-events-none absolute bottom-3 left-3 flex items-center gap-2 rounded-lg bg-background/90 px-3 py-2 text-xs font-medium shadow-sm">
        <MapPin class="h-4 w-4 text-primary" aria-hidden="true" />
        Pin saved for this schedule item
      </div>
    </div>

    <p v-if="!token" class="text-xs leading-5 text-destructive">
      Add NUXT_PUBLIC_MAPBOX_ACCESS_TOKEN to enable address suggestions and map pins.
    </p>
  </div>
</template>

<script setup>
import { Loader2, MapPin, MapPinned, Search } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Popover, PopoverAnchor, PopoverContent } from '@/components/ui/popover'

const props = defineProps({
  id: { type: String, required: true },
  modelValue: { type: String, default: '' },
  latitude: { type: [String, Number], default: null },
  longitude: { type: [String, Number], default: null },
  venueName: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'selected'])
const config = useRuntimeConfig()
const query = ref(props.modelValue || '')
const open = ref(false)
const loading = ref(false)
const suggestions = ref([])
const searchError = ref('')
let searchTimer
let requestSequence = 0

const token = computed(() => String(config.public.mapboxAccessToken || ''))
const coordinates = computed(() => {
  if (
    props.latitude === null
    || props.latitude === undefined
    || props.latitude === ''
    || props.longitude === null
    || props.longitude === undefined
    || props.longitude === ''
  ) return null
  const latitude = Number(props.latitude)
  const longitude = Number(props.longitude)
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return null
  return [longitude, latitude]
})
const mapPreviewUrl = computed(() => {
  if (!token.value || !coordinates.value) return ''
  const [longitude, latitude] = coordinates.value
  const marker = `pin-s+0d2f2a(${longitude},${latitude})`
  return `https://api.mapbox.com/styles/v1/mapbox/streets-v12/static/${marker}/${longitude},${latitude},15,0/1200x450@2x?access_token=${encodeURIComponent(token.value)}`
})
const searchMessage = computed(() => {
  if (!token.value) return 'Mapbox is not configured for this workspace.'
  if (searchError.value) return searchError.value
  if (query.value.trim().length < 3) return 'Type at least three characters to find an address or venue.'
  if (loading.value) return 'Searching Mapbox…'
  return 'No matching locations found. Try adding a city or region.'
})

watch(() => props.modelValue, value => {
  if (value !== query.value) query.value = value || ''
})

onBeforeUnmount(() => window.clearTimeout(searchTimer))

function openSuggestions() {
  if (suggestions.value.length || query.value.trim().length >= 3) open.value = true
}

function queueSearch() {
  emit('update:modelValue', query.value)
  emit('selected', {
    address: query.value,
    latitude: null,
    longitude: null,
    mapUrl: '',
  })
  searchError.value = ''
  suggestions.value = []
  window.clearTimeout(searchTimer)
  if (!token.value || query.value.trim().length < 3) {
    open.value = query.value.trim().length > 0
    return
  }
  open.value = true
  searchTimer = window.setTimeout(searchAddresses, 350)
}

async function searchAddresses() {
  const sequence = ++requestSequence
  loading.value = true
  try {
    const response = await $fetch('https://api.mapbox.com/search/geocode/v6/forward', {
      query: {
        q: query.value.trim(),
        access_token: token.value,
        autocomplete: true,
        permanent: true,
        limit: 5,
      },
    })
    if (sequence !== requestSequence) return
    suggestions.value = (response?.features || []).map(feature => {
      const properties = feature.properties || {}
      const name = properties.name_preferred || properties.name || 'Selected location'
      const address = properties.full_address || [name, properties.place_formatted].filter(Boolean).join(', ')
      return {
        id: properties.mapbox_id || feature.id,
        name,
        address,
        coordinates: feature.geometry?.coordinates || [],
      }
    }).filter(item => item.address && item.coordinates.length >= 2)
  } catch {
    if (sequence === requestSequence) {
      suggestions.value = []
      searchError.value = 'Mapbox could not load suggestions. Check the token and try again.'
    }
  } finally {
    if (sequence === requestSequence) loading.value = false
  }
}

function selectSuggestion(suggestion) {
  const [longitude, latitude] = suggestion.coordinates
  query.value = suggestion.address
  emit('update:modelValue', suggestion.address)
  emit('selected', {
    address: suggestion.address,
    latitude,
    longitude,
    mapUrl: `https://www.google.com/maps/search/?api=1&query=${latitude},${longitude}`,
  })
  suggestions.value = []
  open.value = false
}
</script>
