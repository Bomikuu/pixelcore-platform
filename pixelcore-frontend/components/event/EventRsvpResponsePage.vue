<template>
  <component
    :is="embedded ? 'div' : 'main'"
    class="event-rsvp relative overflow-x-hidden"
    :class="[selectedTemplate.className, embedded ? 'event-rsvp-embedded' : 'min-h-screen']"
    :style="{ ...pageStyle, ...presentation }"
  >
    <header v-if="!embedded" class="absolute inset-x-0 top-0 z-30 border-b border-white/15 bg-black/55 text-white backdrop-blur-md">
      <div class="grid min-h-20 grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-3 px-5 py-3 sm:px-8 lg:px-12">
        <NuxtLink
          :to="invitationUrl"
          class="inline-flex min-w-0 items-center gap-2 justify-self-start text-sm text-white/75 underline-offset-4 transition-colors hover:text-white hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
        >
          <ArrowLeft class="h-4 w-4 shrink-0" aria-hidden="true" />
          <span class="hidden sm:inline">View invitation</span>
          <span class="sm:hidden">Invitation</span>
        </NuxtLink>

        <img
          v-if="headerLogo"
          :src="headerLogo"
          :alt="event.business?.display_name || 'Event logo'"
          class="max-h-10 max-w-32 object-contain sm:max-w-48"
        >
        <span v-else class="max-w-40 truncate text-center text-xl event-script sm:max-w-72 sm:text-2xl">
          {{ headerMark }}
        </span>

        <span
          v-if="previewMode"
          class="justify-self-end rounded-full border border-white/25 bg-white/10 px-3 py-1 text-xs font-semibold text-white/85"
        >
          RSVP preview
        </span>
        <span v-else aria-hidden="true" />
      </div>
    </header>

    <div :class="embedded ? 'w-full' : 'grid min-h-screen lg:grid-cols-[minmax(22rem,0.82fr)_minmax(34rem,1.18fr)]'">
      <section v-if="!embedded" class="rsvp-visual relative isolate flex min-h-[34rem] overflow-hidden px-5 pb-10 pt-28 text-white sm:px-8 lg:min-h-screen lg:px-12 lg:pb-10 lg:pt-32">
        <img
          v-if="heroImage"
          :src="heroImage.image_url"
          :alt="heroImage.alt_text"
          class="absolute inset-0 h-full w-full object-cover"
        >
        <div v-else class="absolute inset-0 bg-[color:var(--event-bg)]" />
        <div class="absolute inset-0 bg-black/55" />
        <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/15 to-black/45" />
        <GardenBotanicalDecoration v-if="isGardenVow" placement="frame" />
        <GardenBotanicalDecoration v-if="isGardenVow" placement="corner" />

        <div class="rsvp-copy relative z-10 flex w-full flex-col justify-end">
          <div class="max-w-2xl pb-4 lg:pb-10">
            <p class="text-sm text-white/70">For {{ guest.full_name }}</p>
            <h1 class="mt-4 text-balance text-5xl leading-[0.94] wedding-display sm:text-6xl">
              {{ event.title }}
            </h1>
            <dl class="mt-9 grid gap-4 border-y border-white/25 py-6 text-sm sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
              <div class="flex items-start gap-3">
                <CalendarDays class="mt-0.5 h-4 w-4 shrink-0 text-white/65" aria-hidden="true" />
                <div>
                  <dt class="text-white/50">Date and time</dt>
                  <dd class="mt-1 font-semibold text-white">{{ eventDate }}</dd>
                  <dd class="mt-0.5 text-white/70">{{ eventTime }}</dd>
                </div>
              </div>
              <div class="flex items-start gap-3">
                <MapPin class="mt-0.5 h-4 w-4 shrink-0 text-white/65" aria-hidden="true" />
                <div>
                  <dt class="text-white/50">Venue</dt>
                  <dd class="mt-1 font-semibold text-white">{{ venueName }}</dd>
                  <dd v-if="venueAddress" class="mt-0.5 text-white/70">{{ venueAddress }}</dd>
                </div>
              </div>
            </dl>
          </div>
        </div>
      </section>

      <section class="rsvp-panel flex items-center bg-[color:var(--event-bg)] text-[color:var(--event-text)]" :class="embedded ? 'p-6 sm:p-10' : 'min-h-screen px-5 pb-14 pt-28 sm:px-10 lg:px-14 lg:pb-14 lg:pt-32 xl:px-20'">
        <div class="mx-auto w-full max-w-2xl">
          <div class="border-b border-[color:color-mix(in_srgb,var(--event-text)_22%,transparent)] pb-8">
            <h2 class="text-balance text-5xl leading-none wedding-display sm:text-6xl">{{ rsvpConfig.heading }}</h2>
            <p class="mt-5 max-w-xl text-base leading-7 text-[color:color-mix(in_srgb,var(--event-text)_72%,transparent)]">
              {{ rsvpConfig.subtitle }}
            </p>
            <p v-if="rsvpDeadlineLabel" class="mt-5 flex items-center gap-2 text-sm text-[color:color-mix(in_srgb,var(--event-text)_58%,transparent)]">
              <CalendarClock class="h-4 w-4" aria-hidden="true" />
              Respond by {{ rsvpDeadlineLabel }}
            </p>
          </div>

          <Transition name="rsvp-state" mode="out-in">
            <section v-if="saved" key="confirmation" class="py-9" aria-live="polite">
              <span class="grid h-12 w-12 place-items-center rounded-full border border-[color:color-mix(in_srgb,var(--event-text)_28%,transparent)]">
                <Check v-if="form.response === 'accepted'" class="h-5 w-5" aria-hidden="true" />
                <Heart v-else-if="form.response === 'maybe'" class="h-5 w-5" aria-hidden="true" />
                <X v-else class="h-5 w-5" aria-hidden="true" />
              </span>
              <h3 class="mt-8 text-4xl leading-none wedding-display sm:text-5xl">{{ confirmationCopy.title }}</h3>
              <p class="mt-5 max-w-xl text-sm leading-7 text-[color:color-mix(in_srgb,var(--event-text)_68%,transparent)]">
                {{ confirmationCopy.message }}
              </p>
              <dl class="mt-8 grid gap-4 border-y border-[color:color-mix(in_srgb,var(--event-text)_18%,transparent)] py-5 text-sm sm:grid-cols-2">
                <div>
                  <dt class="text-[color:color-mix(in_srgb,var(--event-text)_50%,transparent)]">Response</dt>
                  <dd class="mt-1 font-semibold">{{ responseLabel(form.response) }}</dd>
                </div>
                <div v-if="form.response === 'accepted' && rsvpConfig.show_party_size">
                  <dt class="text-[color:color-mix(in_srgb,var(--event-text)_50%,transparent)]">Party size</dt>
                  <dd class="mt-1 font-semibold">{{ form.party_size }} {{ Number(form.party_size) === 1 ? 'person' : 'people' }}</dd>
                </div>
              </dl>
              <div class="mt-8 flex flex-col gap-3 sm:flex-row">
                <Button
                  type="button"
                  variant="outline"
                  class="border-[color:color-mix(in_srgb,var(--event-text)_28%,transparent)] bg-transparent text-[color:var(--event-text)] hover:bg-[color:var(--event-text)] hover:text-[color:var(--event-bg)]"
                  :disabled="availability.isClosed"
                  @click="saved = false"
                >
                  <FilePenLine class="h-4 w-4" aria-hidden="true" />
                  Edit response
                </Button>
                <ButtonLink
                  :to="invitationUrl"
                  variant="outline"
                  class="border-[color:color-mix(in_srgb,var(--event-text)_28%,transparent)] bg-transparent text-[color:var(--event-text)] hover:bg-[color:var(--event-text)] hover:text-[color:var(--event-bg)]"
                >
                  View event invitation
                  <ArrowUpRight class="h-4 w-4" aria-hidden="true" />
                </ButtonLink>
              </div>
              <p v-if="availability.isClosed" class="mt-5 text-sm text-[color:color-mix(in_srgb,var(--event-text)_58%,transparent)]">
                {{ closedMessage }}
              </p>
            </section>

            <form v-else key="form" class="space-y-7 py-9" @submit.prevent="saveRsvp">
              <div class="grid gap-2">
                <Label for="rsvp-name">Invited guest</Label>
                <Input
                  id="rsvp-name"
                  :model-value="guest.full_name"
                  class="border-[color:color-mix(in_srgb,var(--event-text)_22%,transparent)] bg-transparent text-[color:var(--event-text)]"
                  disabled
                />
              </div>

              <fieldset :disabled="availability.isClosed">
                <legend class="text-sm font-medium">Will you attend?</legend>
                <div class="mt-3 grid gap-3" :class="responseOptions.length === 3 ? 'sm:grid-cols-3' : 'sm:grid-cols-2'">
                  <Button
                    v-for="option in responseOptions"
                    :key="option.value"
                    type="button"
                    variant="outline"
                    class="h-12 border-[color:color-mix(in_srgb,var(--event-text)_22%,transparent)] bg-transparent text-[color:var(--event-text)] hover:bg-[color:color-mix(in_srgb,var(--event-text)_10%,transparent)] hover:text-[color:var(--event-text)]"
                    :class="form.response === option.value ? 'border-[color:var(--event-accent)] bg-[color:var(--event-accent)] text-[color:var(--event-bg)] hover:bg-[color:var(--event-accent)] hover:text-[color:var(--event-bg)]' : ''"
                    :aria-pressed="form.response === option.value"
                    @click="form.response = option.value"
                  >
                    <component :is="option.icon" class="h-4 w-4" aria-hidden="true" />
                    {{ option.label }}
                  </Button>
                </div>
              </fieldset>

              <div v-if="form.response === 'accepted' && rsvpConfig.show_party_size" class="grid gap-2 sm:max-w-xs">
                <Label for="rsvp-party">People attending</Label>
                <Input
                  id="rsvp-party"
                  v-model.number="form.party_size"
                  class="border-[color:color-mix(in_srgb,var(--event-text)_22%,transparent)] bg-transparent text-[color:var(--event-text)]"
                  type="number"
                  min="1"
                  :max="maxPartySize"
                  :disabled="availability.isClosed"
                />
                <p class="text-xs text-[color:color-mix(in_srgb,var(--event-text)_55%,transparent)]">Up to {{ maxPartySize }} people on this invitation.</p>
              </div>

              <div v-if="rsvpConfig.show_dietary_notes" class="grid gap-2">
                <Label for="rsvp-notes">Dietary or accessibility notes</Label>
                <Textarea
                  id="rsvp-notes"
                  v-model="form.dietary_notes"
                  class="border-[color:color-mix(in_srgb,var(--event-text)_22%,transparent)] bg-transparent text-[color:var(--event-text)] placeholder:text-[color:color-mix(in_srgb,var(--event-text)_42%,transparent)]"
                  rows="3"
                  maxlength="500"
                  placeholder="Optional"
                  :disabled="availability.isClosed"
                />
              </div>

              <div v-if="rsvpConfig.show_guest_message" class="grid gap-2">
                <Label for="rsvp-message">Wish or private message</Label>
                <Textarea
                  id="rsvp-message"
                  v-model="form.guest_message"
                  class="border-[color:color-mix(in_srgb,var(--event-text)_22%,transparent)] bg-transparent text-[color:var(--event-text)] placeholder:text-[color:color-mix(in_srgb,var(--event-text)_42%,transparent)]"
                  rows="5"
                  maxlength="1000"
                  placeholder="Write a note for the hosts"
                  :disabled="availability.isClosed"
                />
                <p class="text-xs text-[color:color-mix(in_srgb,var(--event-text)_55%,transparent)]">The organizer decides whether a message appears in the public guest book.</p>
              </div>

              <p v-if="saveError" class="text-sm text-red-300" role="alert">{{ saveError }}</p>
              <p v-if="availability.isClosed" class="border-y border-[color:color-mix(in_srgb,var(--event-text)_18%,transparent)] py-5 text-sm leading-6 text-[color:color-mix(in_srgb,var(--event-text)_65%,transparent)]">
                {{ closedMessage }}
              </p>

              <Button
                type="submit"
                class="h-12 w-full bg-[color:var(--event-accent)] text-[color:var(--event-bg)] hover:bg-[color:var(--event-accent)] hover:opacity-90"
                :disabled="saving || availability.isClosed || !form.response"
              >
                <Loader2 v-if="saving" class="h-4 w-4 animate-spin" aria-hidden="true" />
                <Send v-else class="h-4 w-4" aria-hidden="true" />
                {{ rsvpConfig.submit_label }}
              </Button>

              <p class="flex items-center gap-2 text-xs text-[color:color-mix(in_srgb,var(--event-text)_50%,transparent)]">
                <LockKeyhole class="h-4 w-4" aria-hidden="true" />
                {{ previewMode ? 'Preview only. No guest response will be sent.' : 'This response is tied to your private invitation link.' }}
              </p>
            </form>
          </Transition>
        </div>
      </section>
    </div>
  </component>
</template>

<script setup>
import {
  ArrowLeft,
  ArrowUpRight,
  CalendarClock,
  CalendarDays,
  Check,
  CircleHelp,
  FilePenLine,
  Heart,
  Loader2,
  LockKeyhole,
  MapPin,
  Send,
  X,
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { ButtonLink } from '@/components/ui/button-link'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import GardenBotanicalDecoration from '@/components/event/GardenBotanicalDecoration.vue'
import { eventTemplate, templateGroupForEventType } from '@/utils/eventTemplates'
import {
  normalizeEventSectionsConfig,
  resolveRsvpAvailability,
} from '@/utils/eventRsvpConfig'

const props = defineProps({
  payload: { type: Object, required: true },
  endpoint: { type: String, default: '' },
  previewMode: { type: Boolean, default: false },
  embedded: {type:Boolean,default:false},
  presentation: {type:Object,default:()=>({})},
})

const emit = defineEmits(['updated'])
const config = useRuntimeConfig()
const nowTimestamp = ref(Date.now())
const saving = ref(false)
const saveError = ref('')
const saved = ref(false)
const form = reactive({
  response: '',
  party_size: 1,
  dietary_notes: '',
  guest_message: '',
})
let deadlineTimer

const event = computed(() => props.payload?.event || {})
const guest = computed(() => props.payload?.guest || {})
const website = computed(() => event.value.website || {})
const selectedTemplate = computed(() => eventTemplate(website.value.website_template))
const isGardenVow = computed(() => website.value.website_template === 'wedding_garden')
const templateGroup = computed(() => templateGroupForEventType(event.value.event_type))
const sectionConfig = computed(() => normalizeEventSectionsConfig(website.value.sections_config))
const rsvpConfig = computed(() => sectionConfig.value.rsvp)
const firstSchedule = computed(() => website.value.schedule_entries?.[0] || null)
const invitationUrl = computed(() => `/event/${event.value.public_id}`)
const availability = computed(() => {
  const resolved = resolveRsvpAvailability({
    eventStatus: event.value.status,
    publicRsvpEnabled: event.value.public_rsvp_enabled,
    deadline: rsvpConfig.value.deadline,
    now: nowTimestamp.value,
  })
  return props.previewMode
    ? { ...resolved, isClosed: false, reason: null }
    : resolved
})
const rsvpDeadlineLabel = computed(() => {
  if (availability.value.deadlineAt === null) return ''
  return new Intl.DateTimeFormat('en-PH', {
    dateStyle: 'long',
    timeStyle: 'short',
    timeZone: event.value.timezone || 'Asia/Manila',
  }).format(new Date(availability.value.deadlineAt))
})
const closedMessage = computed(() => (
  availability.value.reason === 'deadline'
    ? `The RSVP deadline was ${rsvpDeadlineLabel.value}. Contact the organizer if your plans changed.`
    : 'Responses are closed. Contact the organizer if your plans changed.'
))
const media = computed(() => website.value.media || [])
const heroImage = computed(() => (
  media.value.find(item => item.placement === 'hero' && item.is_featured)
  || media.value.find(item => item.placement === 'hero')
  || (website.value.thumbnail_url
    ? { image_url: website.value.thumbnail_url, alt_text: `${event.value.title} event photograph` }
    : null)
))
const headerLogo = computed(() => website.value.header_mark_type === 'logo' ? event.value.business?.logo || '' : '')
const headerMark = computed(() => {
  const names = website.value.participants?.map(person => person.name).filter(Boolean).slice(0, 2) || []
  if (website.value.header_mark_text) return website.value.header_mark_text
  return templateGroup.value === 'wedding' && names.length
    ? names.join(' × ')
    : event.value.title || event.value.business?.display_name || 'Our event'
})
const venueName = computed(() => firstSchedule.value?.venue_name || event.value.location?.name || 'Venue details to follow')
const venueAddress = computed(() => firstSchedule.value?.address || '')
const eventDate = computed(() => formatDate(event.value.starts_at))
const eventTime = computed(() => formatTimeRange(event.value.starts_at, event.value.ends_at))
const headingFontStack = computed(() => `'${website.value.heading_font || 'Bodoni Moda'}', Georgia, serif`)
const bodyFontStack = computed(() => `'${website.value.body_font || 'Manrope'}', Arial, sans-serif`)
const pageStyle = computed(() => ({
  '--event-bg': website.value.theme_background || '#000000',
  '--event-text': website.value.theme_text || '#F5F3EE',
  '--event-accent': website.value.theme_accent || '#D6D1C8',
  '--event-heading': headingFontStack.value,
  '--event-body': bodyFontStack.value,
}))
const responseOptions = computed(() => {
  const options = [
    { value: 'accepted', label: rsvpConfig.value.accept_label, icon: Check },
    { value: 'declined', label: rsvpConfig.value.decline_label, icon: X },
  ]
  if (rsvpConfig.value.allow_maybe || form.response === 'maybe') {
    options.splice(1, 0, { value: 'maybe', label: 'Maybe', icon: CircleHelp })
  }
  return options
})
const maxPartySize = computed(() => Math.max(
  1,
  Math.min(
    Number(rsvpConfig.value.max_party_size || 10),
    Number(event.value.max_guests || 50),
    50,
  ),
))
const confirmationCopy = computed(() => {
  if (form.response === 'accepted') {
    return {
      title: rsvpConfig.value.attending_title,
      message: rsvpConfig.value.attending_message,
    }
  }
  if (form.response === 'maybe') {
    return {
      title: 'Your response is saved',
      message: 'The organizer knows your plans are still taking shape. You can return to this page and update your response.',
    }
  }
  return {
    title: rsvpConfig.value.declining_title,
    message: rsvpConfig.value.declining_message,
  }
})

useHead(() => ({
  title: `RSVP for ${event.value.title || 'event'} | ${event.value.business?.display_name || 'PixelCore'}`,
  meta: [
    { name: 'referrer', content: 'no-referrer' },
    { name: 'robots', content: 'noindex,nofollow' },
    { name: 'theme-color', content: website.value.theme_background || '#000000' },
  ],
  link: [{ rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Bodoni+Moda:opsz,wght@6..96,400;6..96,500&family=Cormorant+Garamond:wght@400;500&family=Italiana&family=Manrope:wght@400;500;600&family=Newsreader:opsz,wght@6..72,400;6..72,500&family=Playball&display=swap' }],
}))

watch(guest, value => {
  Object.assign(form, {
    response: value.response === 'pending' ? '' : value.response || '',
    party_size: Number(value.party_size || 1),
    dietary_notes: value.dietary_notes || '',
    guest_message: value.guest_message || '',
  })
  saved.value = Boolean(value.response && value.response !== 'pending')
}, { immediate: true })

onMounted(() => {
  if (availability.value.deadlineAt !== null) {
    deadlineTimer = window.setInterval(() => {
      nowTimestamp.value = Date.now()
    }, 1000)
  }
})

onBeforeUnmount(() => {
  if (deadlineTimer) window.clearInterval(deadlineTimer)
})

async function saveRsvp() {
  if (
    form.response === 'accepted'
    && rsvpConfig.value.show_party_size
    && (Number(form.party_size) < 1 || Number(form.party_size) > maxPartySize.value)
  ) {
    saveError.value = `Choose a party size from 1 to ${maxPartySize.value}.`
    return
  }

  if (props.previewMode) {
    saved.value = true
    saveError.value = ''
    toast({
      title: 'Preview response complete',
      description: 'This sample response was not sent to the guest list.',
    })
    return
  }

  saving.value = true
  saveError.value = ''
  try {
    const response = await $fetch(props.endpoint, {
      baseURL: config.public.apiBaseUrl,
      method: 'PATCH',
      body: {
        ...form,
        party_size: form.response === 'accepted' ? Number(form.party_size) : 1,
      },
    })
    saved.value = true
    emit('updated', response)
    toast({
      title: 'Your response is saved',
      description: 'The organizer has received your RSVP and message.',
    })
  } catch (error) {
    saveError.value = error?.data?.error?.message || 'Your response could not be saved. Please try again.'
  } finally {
    saving.value = false
  }
}

function responseLabel(response) {
  return responseOptions.value.find(option => option.value === response)?.label || 'Response saved'
}

function formatDate(value) {
  if (!value) return 'Date to follow'
  return new Intl.DateTimeFormat('en-PH', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(value))
}

function formatTimeRange(start, end) {
  if (!start) return 'Time to follow'
  const formatter = new Intl.DateTimeFormat('en-PH', {
    hour: 'numeric',
    minute: '2-digit',
  })
  return end
    ? `${formatter.format(new Date(start))} – ${formatter.format(new Date(end))}`
    : formatter.format(new Date(start))
}
</script>

<style scoped>
.event-rsvp {
  background: var(--event-bg);
  color: var(--event-text);
  font-family: var(--event-body);
  scrollbar-color: color-mix(in srgb, var(--event-accent) 55%, transparent) var(--event-bg);
}

.event-rsvp ::selection {
  background: var(--event-accent);
  color: var(--event-bg);
}

.wedding-display {
  font-family: var(--event-heading);
  font-weight: 400;
  letter-spacing: -0.03em;
}

.event-script {
  font-family: 'Playball', cursive;
  letter-spacing: -0.02em;
}

.event-rsvp-embedded .event-script {
  font-family: var(--event-heading);
}

.rsvp-visual {
  animation: visual-open 900ms cubic-bezier(0.16, 1, 0.3, 1) both;
}

.rsvp-copy {
  animation: copy-open 760ms 180ms cubic-bezier(0.16, 1, 0.3, 1) both;
}

.rsvp-panel > div {
  animation: panel-open 820ms 260ms cubic-bezier(0.16, 1, 0.3, 1) both;
}

.rsvp-state-enter-active,
.rsvp-state-leave-active {
  transition:
    opacity 300ms cubic-bezier(0.16, 1, 0.3, 1),
    transform 300ms cubic-bezier(0.16, 1, 0.3, 1),
    filter 300ms cubic-bezier(0.16, 1, 0.3, 1);
}

.rsvp-state-enter-from,
.rsvp-state-leave-to {
  opacity: 0;
  filter: blur(0.3rem);
  transform: translate3d(0, 1rem, 0);
}

@keyframes visual-open {
  from {
    clip-path: inset(0 18% 0 0);
    filter: brightness(0.55);
  }
  to {
    clip-path: inset(0 0 0 0);
    filter: brightness(1);
  }
}

@keyframes copy-open {
  from {
    opacity: 0;
    transform: translate3d(0, 1.5rem, 0);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@keyframes panel-open {
  from {
    opacity: 0.01;
    transform: translate3d(1.5rem, 0, 0);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .event-rsvp *,
  .event-rsvp *::before,
  .event-rsvp *::after {
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
    animation-delay: 0ms !important;
    animation-iteration-count: 1 !important;
  }
}
</style>
