<template>
  <form class="overflow-hidden rounded-xl border bg-card" @submit.prevent="saveDetails">
    <div class="flex flex-col justify-between gap-3 border-b px-5 py-4 sm:flex-row sm:items-center sm:px-6">
      <div>
        <h2 class="text-lg font-semibold">Event details</h2>
        <p class="mt-1 text-sm text-muted-foreground">Update the shared event record used by guests, staff, and the public invitation.</p>
      </div>
      <Button type="submit" :disabled="saving || !canSave">
        <Loader2 v-if="saving" class="h-4 w-4 animate-spin" aria-hidden="true" />
        <Save v-else class="h-4 w-4" aria-hidden="true" />
        Save details
      </Button>
    </div>

    <div class="grid gap-6 p-5 sm:p-6 xl:grid-cols-[minmax(0,1fr)_20rem]">
      <div class="grid gap-5 sm:grid-cols-2">
        <div class="grid gap-2 sm:col-span-2">
          <Label for="details-event-title">Event title</Label>
          <Input id="details-event-title" v-model.trim="form.title" placeholder="Jordan and Riley's wedding" />
        </div>

        <div class="grid gap-2">
          <Label>Event type</Label>
          <Select v-model="form.event_type">
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="wedding">Wedding</SelectItem>
              <SelectItem value="birthday">Birthday</SelectItem>
              <SelectItem value="general">General event</SelectItem>
              <SelectItem value="private_event">Private event</SelectItem>
              <SelectItem value="corporate">Corporate event</SelectItem>
              <SelectItem value="community">Community event</SelectItem>
              <SelectItem value="other">Other event</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div class="grid gap-2">
          <Label>RSVP status</Label>
          <Select v-model="form.status">
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="planning">Planning</SelectItem>
              <SelectItem value="open">Open for RSVP</SelectItem>
              <SelectItem value="closed">RSVP closed</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="cancelled">Cancelled</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div class="grid gap-2">
          <Label for="details-event-start">Starts</Label>
          <Input id="details-event-start" v-model="form.starts_at" type="datetime-local" />
        </div>

        <div class="grid gap-2">
          <Label for="details-event-end">Ends</Label>
          <Input id="details-event-end" v-model="form.ends_at" type="datetime-local" />
        </div>

        <div class="grid gap-2">
          <Label>Location</Label>
          <Select v-model="form.location_public_id">
            <SelectTrigger><SelectValue placeholder="Choose a location" /></SelectTrigger>
            <SelectContent>
              <SelectItem v-for="location in locations" :key="location.public_id" :value="location.public_id">
                {{ location.name }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div class="grid gap-2">
          <Label>Floor plan</Label>
          <Select v-model="form.layout_public_id">
            <SelectTrigger><SelectValue placeholder="Choose a venue layout" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="none">No floor plan</SelectItem>
              <SelectItem v-for="layout in matchingLayouts" :key="layout.public_id" :value="layout.public_id">
                {{ layout.name }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div class="grid gap-2">
          <Label for="details-organizer-name">Organizer name</Label>
          <Input id="details-organizer-name" v-model.trim="form.organizer_name" />
        </div>

        <div class="grid gap-2">
          <Label for="details-max-guests">Maximum attendance</Label>
          <Input id="details-max-guests" v-model.number="form.max_guests" type="number" min="1" max="10000" />
          <p class="text-xs text-muted-foreground">Confirmed party sizes cannot exceed this limit.</p>
        </div>

        <div class="grid gap-2">
          <Label for="details-organizer-email">Organizer email</Label>
          <Input id="details-organizer-email" v-model.trim="form.organizer_email" type="email" />
        </div>

        <div class="grid gap-2">
          <Label for="details-organizer-phone">Organizer phone</Label>
          <Input id="details-organizer-phone" v-model.trim="form.organizer_phone" type="tel" />
        </div>

        <div class="grid gap-2 sm:col-span-2">
          <Label for="details-event-description">Event description</Label>
          <Textarea id="details-event-description" v-model.trim="form.description" rows="5" placeholder="Share arrival details, context, or a short welcome." />
        </div>
      </div>

      <aside class="space-y-5 xl:border-l xl:pl-6">
        <div>
          <Label for="details-thumbnail">Event thumbnail</Label>
          <div class="mt-2 aspect-[4/3] overflow-hidden rounded-xl border bg-muted">
            <img v-if="thumbnailPreview" :src="thumbnailPreview" alt="Event thumbnail preview" class="h-full w-full object-cover">
            <div v-else class="grid h-full place-items-center text-muted-foreground">
              <ImageIcon class="h-10 w-10" aria-hidden="true" />
            </div>
          </div>
          <Input id="details-thumbnail" class="mt-3" type="file" accept="image/jpeg,image/png,image/webp" @change="selectThumbnail" />
          <p class="mt-2 text-xs leading-5 text-muted-foreground">JPG, PNG, or WebP up to 5 MB.</p>
        </div>

        <div class="flex items-center justify-between gap-4 rounded-xl border p-4">
          <div>
            <Label for="details-public-rsvp">Public RSVP</Label>
            <p class="mt-1 text-xs leading-5 text-muted-foreground">Allow invitees to submit responses from the event page.</p>
          </div>
          <Switch id="details-public-rsvp" v-model:checked="form.public_rsvp_enabled" />
        </div>
      </aside>
    </div>
  </form>
</template>

<script setup>
import { Image as ImageIcon, Loader2, Save } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'

const props = defineProps({
  businessId: { type: String, required: true },
  event: { type: Object, required: true },
  locations: { type: Array, default: () => [] },
  layouts: { type: Array, default: () => [] },
})

const emit = defineEmits(['updated'])
const { apiFetch } = useApiClient()
const saving = ref(false)
const thumbnailFile = ref(null)
const localThumbnailPreview = ref('')
const form = reactive(createForm(props.event))

const matchingLayouts = computed(() => props.layouts.filter(layout => (
  !form.location_public_id || layout.location_public_id === form.location_public_id
)))
const thumbnailPreview = computed(() => localThumbnailPreview.value || props.event.thumbnail_url || '')
const canSave = computed(() => Boolean(
  form.title
  && form.organizer_name
  && form.starts_at
  && form.location_public_id
  && Number(form.max_guests) > 0
))

watch(
  () => props.event,
  event => {
    Object.assign(form, createForm(event))
    clearThumbnailPreview()
  },
)

watch(
  () => form.location_public_id,
  () => {
    if (form.layout_public_id !== 'none' && !matchingLayouts.value.some(layout => layout.public_id === form.layout_public_id)) {
      form.layout_public_id = 'none'
    }
  },
)

onBeforeUnmount(clearThumbnailPreview)

function createForm(event) {
  return {
    title: event.title || '',
    event_type: event.event_type || 'general',
    status: event.status || 'planning',
    starts_at: toLocalDateTime(event.starts_at),
    ends_at: toLocalDateTime(event.ends_at),
    location_public_id: event.location_public_id || '',
    layout_public_id: event.layout_public_id || 'none',
    organizer_name: event.organizer_name || '',
    organizer_email: event.organizer_email || '',
    organizer_phone: event.organizer_phone || '',
    description: event.description || '',
    max_guests: Number(event.max_guests || 1),
    public_rsvp_enabled: Boolean(event.public_rsvp_enabled),
  }
}

function selectThumbnail(event) {
  clearThumbnailPreview()
  thumbnailFile.value = event.target.files?.[0] || null
  if (thumbnailFile.value) localThumbnailPreview.value = URL.createObjectURL(thumbnailFile.value)
}

function clearThumbnailPreview() {
  if (localThumbnailPreview.value) URL.revokeObjectURL(localThumbnailPreview.value)
  localThumbnailPreview.value = ''
  thumbnailFile.value = null
}

async function saveDetails() {
  saving.value = true
  try {
    const payload = {
      ...form,
      max_guests: Number(form.max_guests),
      starts_at: new Date(form.starts_at).toISOString(),
      ends_at: form.ends_at ? new Date(form.ends_at).toISOString() : null,
      layout_public_id: form.layout_public_id === 'none' ? null : form.layout_public_id,
    }

    let body = payload
    if (thumbnailFile.value) {
      body = new FormData()
      for (const [key, value] of Object.entries(payload)) {
        if (value !== null && value !== undefined) body.append(key, String(value))
      }
      body.append('thumbnail', thumbnailFile.value)
    }

    const saved = await apiFetch(`businesses/${props.businessId}/venue-events/${props.event.public_id}/`, {
      method: 'PATCH',
      body,
    })
    clearThumbnailPreview()
    emit('updated', saved)
    toast({ title: 'Event details updated', description: `${saved.title} now uses the latest schedule and capacity.` })
  } catch (error) {
    toast({
      title: 'Event details could not be saved',
      description: error?.data?.error?.message || error?.data?.detail || 'Review the event details and try again.',
      variant: 'destructive',
    })
  } finally {
    saving.value = false
  }
}

function toLocalDateTime(value) {
  if (!value) return ''
  const date = new Date(value)
  const offset = date.getTimezoneOffset()
  return new Date(date.getTime() - offset * 60 * 1000).toISOString().slice(0, 16)
}
</script>
