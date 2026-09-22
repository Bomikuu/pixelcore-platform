<template>
  <div class="min-h-screen bg-[#f6f2ec] text-slate-950">
    <main class="mx-auto max-w-6xl px-4 py-7 sm:px-6 sm:py-10">
      <div v-if="pending || servicesPending" class="grid min-h-[65vh] place-items-center">
        <div class="text-center">
          <Loader2 class="mx-auto h-8 w-8 animate-spin text-primary" aria-hidden="true" />
          <p class="mt-3 text-sm font-medium text-slate-600">
            Preparing the {{ bookingLabel.toLowerCase() }} form…
          </p>
        </div>
      </div>

      <Card
        v-else-if="error || servicesError || !identity"
        class="mx-auto max-w-xl border-slate-200 text-center shadow-xl"
      >
        <CardContent class="p-10">
          <div class="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-slate-100 text-slate-500">
            <Store class="h-6 w-6" aria-hidden="true" />
          </div>
          <h1 class="mt-5 text-2xl font-bold">{{ bookingLabel }} unavailable</h1>
          <p class="mt-2 text-sm text-muted-foreground">
            This scheduling page may have moved or the business is no longer public.
          </p>
          <ButtonLink :to="base || '/'" class="mt-6">Return to storefront</ButtonLink>
        </CardContent>
      </Card>

      <Card
        v-else-if="identity.public_booking_enabled === false"
        class="mx-auto max-w-2xl overflow-hidden border-slate-200 shadow-xl shadow-slate-950/5"
      >
        <div class="relative h-56 bg-[#0d2f2a] sm:h-64">
          <img v-if="identity.cover_image" :src="identity.cover_image" :alt="identity.display_name" class="h-full w-full object-cover opacity-70">
          <div class="absolute inset-0 bg-gradient-to-t from-[#0d2f2a] via-[#0d2f2a]/45 to-transparent" />
          <div class="absolute bottom-5 left-5 right-5 text-white">
            <p class="text-xs font-bold uppercase tracking-[0.18em] text-emerald-200">Private schedule</p>
            <h1 class="mt-1 text-3xl font-black">{{ identity.display_name }}</h1>
          </div>
        </div>
        <CardContent class="px-6 py-9 text-center sm:px-10">
          <div class="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-slate-100 text-slate-600"><CalendarX2 class="h-8 w-8" aria-hidden="true" /></div>
          <h2 class="mt-5 text-2xl font-bold">Online {{ bookingLabel.toLowerCase() }}s are not open yet</h2>
          <p class="mx-auto mt-2 max-w-lg text-sm leading-6 text-muted-foreground">Contact the team directly for availability, or check again when the public schedule opens.</p>
          <div class="mt-6 flex flex-col justify-center gap-3 sm:flex-row">
            <ButtonLink :to="base || '/'">View storefront</ButtonLink>
            <ButtonAnchor v-if="identity.contact_phone" variant="outline" :href="`tel:${identity.contact_phone}`"><Phone class="h-4 w-4" aria-hidden="true" />Call the team</ButtonAnchor>
          </div>
        </CardContent>
      </Card>

      <Card
        v-else-if="!services.length"
        class="mx-auto max-w-2xl overflow-hidden border-amber-200 shadow-xl shadow-amber-950/5"
      >
        <div class="relative h-56 bg-slate-900 sm:h-64">
          <img
            v-if="identity.cover_image"
            :src="identity.cover_image"
            :alt="identity.display_name"
            class="h-full w-full object-cover"
          >
          <div class="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-slate-950/25 to-transparent" />
          <div class="absolute bottom-5 left-5 right-5 text-white">
            <p class="text-xs font-bold uppercase tracking-[0.18em] text-white/70">{{ bookingLabel }}</p>
            <h1 class="mt-1 text-3xl font-black">{{ identity.display_name }}</h1>
            <p class="mt-1 text-sm text-white/75">{{ locationLabel }}</p>
          </div>
        </div>
        <CardContent class="px-6 py-9 text-center sm:px-10">
          <div class="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-amber-100 text-amber-700">
            <CalendarX2 class="h-8 w-8" aria-hidden="true" />
          </div>
          <h2 class="mt-5 text-2xl font-bold">No bookable service is published yet</h2>
          <p class="mx-auto mt-2 max-w-lg text-sm leading-6 text-muted-foreground">
            The public form is open, but {{ identity.display_name }} still needs a published service with staff availability before customers can choose a time.
          </p>
          <div class="mt-6 flex flex-col justify-center gap-3 sm:flex-row">
            <ButtonLink :to="base || '/'">View storefront</ButtonLink>
            <ButtonAnchor v-if="identity.contact_phone" variant="outline" :href="`tel:${identity.contact_phone}`">
              <Phone class="h-4 w-4" aria-hidden="true" />
              Call {{ isRestaurant ? 'restaurant' : 'business' }}
            </ButtonAnchor>
          </div>
        </CardContent>
      </Card>

      <div v-else-if="bookingResult" class="mx-auto max-w-3xl">
        <Card class="overflow-hidden border-emerald-200 shadow-xl shadow-emerald-950/5">
          <CardContent class="p-7 text-center sm:p-12">
            <div class="mx-auto grid h-20 w-20 place-items-center rounded-full bg-emerald-100 text-emerald-700">
              <CheckCircle2 class="h-10 w-10" aria-hidden="true" />
            </div>
            <p class="mt-6 text-xs font-bold uppercase tracking-[0.2em] text-emerald-700">
              {{ bookingResult.status === 'pending' ? 'Request received' : 'Booking confirmed' }}
            </p>
            <h1 class="mt-2 text-3xl font-black tracking-tight">
              Your {{ bookingLabel.toLowerCase() }} is with {{ identity.display_name }}.
            </h1>
            <p class="mx-auto mt-3 max-w-xl text-sm leading-6 text-muted-foreground">
              <template v-if="bookingResult.status === 'pending'">
                The team will review your request and use your contact information if anything needs to be confirmed.
              </template>
              <template v-else>
                Your time is confirmed. Keep the reference below if you need to contact the business.
              </template>
            </p>

            <dl class="mx-auto mt-7 grid max-w-xl gap-3 rounded-2xl border bg-slate-50 p-5 text-left sm:grid-cols-2">
              <div>
                <dt class="text-xs text-muted-foreground">Booking ID</dt>
                <dd class="mt-1 font-mono text-lg font-black text-primary">{{ bookingResult.confirmation_code }}</dd>
              </div>
              <div>
                <dt class="text-xs text-muted-foreground">Status</dt>
                <dd class="mt-1 font-semibold capitalize">{{ bookingResult.status }}</dd>
              </div>
              <div>
                <dt class="text-xs text-muted-foreground">Service</dt>
                <dd class="mt-1 font-semibold">{{ bookingResult.offering_name || selectedService?.name }}</dd>
              </div>
              <div>
                <dt class="text-xs text-muted-foreground">Date and time</dt>
                <dd class="mt-1 font-semibold">{{ bookingDateLabel }}</dd>
              </div>
              <div>
                <dt class="text-xs text-muted-foreground">{{ resourceWord }}</dt>
                <dd class="mt-1 font-semibold">
                  {{ bookingResult.resources?.[0]?.name || 'No resource assigned' }} · {{ bookingResult.seats }} {{ guestWord }}
                </dd>
              </div>
            </dl>

            <div class="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
              <ButtonLink :to="base || '/'">Return to storefront</ButtonLink>
              <Button variant="outline" type="button" @click="startAnotherBooking">
                Make another {{ bookingLabel.toLowerCase() }}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <div v-else class="grid gap-6 lg:grid-cols-[0.72fr_1.28fr] lg:items-start">
        <aside class="overflow-hidden rounded-3xl border border-primary/10 bg-white shadow-sm lg:sticky lg:top-6">
          <div class="relative h-48 bg-slate-900">
            <img
              v-if="identity.cover_image"
              :src="identity.cover_image"
              :alt="identity.display_name"
              class="h-full w-full object-cover"
            >
            <div class="absolute inset-0 bg-gradient-to-t from-slate-950/75 via-slate-950/10 to-transparent" />
            <div class="absolute bottom-4 left-4 right-4 text-white">
              <p class="text-xs font-bold uppercase tracking-[0.18em] text-white/70">{{ bookingVerb }} online</p>
              <h1 class="mt-1 text-2xl font-black">{{ identity.display_name }}</h1>
              <p class="mt-1 text-sm font-semibold text-white/80">
                {{ selectedService?.name || `Choose a ${bookingLabel.toLowerCase()}` }}
              </p>
            </div>
          </div>

          <div class="space-y-5 p-5">
            <div class="flex gap-3 text-sm text-slate-600">
              <MapPin class="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
              <span>{{ locationLabel }}</span>
            </div>
            <div class="rounded-2xl bg-primary/5 p-4">
              <p class="text-sm font-semibold">How it works</p>
              <div class="mt-3 space-y-3">
                <div
                  v-for="(step, index) in steps"
                  :key="step"
                  class="flex gap-3 text-xs leading-5 text-muted-foreground"
                >
                  <span class="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-white font-bold text-primary">
                    {{ index + 1 }}
                  </span>
                  {{ step }}
                </div>
              </div>
            </div>
            <p v-if="identity.booking_intro" class="text-sm leading-6 text-slate-600">{{ identity.booking_intro }}</p>
            <p class="text-xs leading-5 text-muted-foreground">
              The selected service lasts about {{ durationMinutes }} minutes.
              {{ isRestaurant ? 'A pending request is final once the restaurant confirms it.' : 'Availability is checked against staff, resources, and existing bookings.' }}
            </p>
          </div>
        </aside>

        <Card class="overflow-hidden border-slate-200 shadow-xl shadow-slate-950/5">
          <CardHeader class="border-b bg-white p-5 sm:p-7">
            <div class="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
              <div>
                <p class="text-xs font-bold uppercase tracking-[0.18em] text-primary">Online {{ bookingLabel.toLowerCase() }}</p>
                <CardTitle class="mt-2 text-2xl sm:text-3xl">
                  {{ selectedService ? `${bookingVerb} ${selectedService.name}` : 'Choose your visit' }}
                </CardTitle>
                <CardDescription class="mt-1">Check live availability before adding your contact details.</CardDescription>
              </div>
              <Badge variant="outline" class="w-fit bg-primary/5 text-primary">{{ formProgress }}% complete</Badge>
            </div>
            <Progress :model-value="formProgress" class="mt-4 h-2" />
          </CardHeader>

          <CardContent class="space-y-7 bg-white p-5 sm:p-7">
            <Alert class="border-primary/20 bg-primary/[0.045]">
              <CalendarCheck2 class="h-4 w-4 text-primary" aria-hidden="true" />
              <AlertTitle>
                {{ isRestaurant ? 'Restaurant table reservation' : 'Service appointment' }}
              </AlertTitle>
              <AlertDescription>
                <template v-if="isRestaurant">
                  This form reserves a visit and an available table at {{ identity.display_name }}.
                </template>
                <template v-else>
                  This form books a published service with {{ identity.display_name }}.
                </template>
                Weddings and private events use a separate invitation-specific RSVP link from their organizer.
              </AlertDescription>
            </Alert>

            <section>
              <div class="mb-4 flex items-center gap-3">
                <span class="grid h-9 w-9 place-items-center rounded-xl bg-primary text-sm font-bold text-primary-foreground">1</span>
                <div>
                  <h2 class="font-bold">Visit details</h2>
                  <p class="text-xs text-muted-foreground">Select a service, date, time, and party size.</p>
                </div>
              </div>

              <div class="grid gap-4">
                <div v-if="services.length > 1" class="grid gap-2">
                  <Label>Service</Label>
                  <Select v-model="selectedServiceSlug">
                    <SelectTrigger><SelectValue placeholder="Choose a service" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem v-for="item in services" :key="item.public_id" :value="item.slug">
                        {{ item.name }} · {{ item.duration_minutes || 60 }} minutes
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div class="grid gap-4 sm:grid-cols-3">
                  <div class="grid gap-2">
                    <Label for="booking-date">Date</Label>
                    <ScheduleDatePicker
                      id="booking-date"
                      v-model="form.date"
                      :min="minimumDate"
                      :max="maximumDate"
                      label="Booking date"
                      @change="resetSelection"
                    />
                  </div>
                  <div class="grid gap-2">
                    <Label>Time</Label>
                    <Select v-model="form.time" @update:model-value="resetResourceSelection">
                      <SelectTrigger><SelectValue placeholder="Select time" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem v-for="slot in timeOptions" :key="slot.value" :value="slot.value">{{ slot.label }}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div class="grid gap-2">
                    <Label>{{ isRestaurant ? 'Guests' : 'People' }}</Label>
                    <Select v-model="form.seats" @update:model-value="refreshForPartySize">
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem v-for="size in partySizes" :key="size" :value="String(size)">
                          {{ size }} {{ size === 1 ? guestWordSingular : guestWord }}
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              <p v-if="form.date && slotsLoaded && !timeOptions.length" class="mt-3 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
                {{ identity.display_name }} has no available times on this day.
              </p>

              <Button class="mt-4 w-full sm:w-auto" type="button" :disabled="loadingSlots || !form.date || !form.time" @click="checkAvailability">
                <Loader2 v-if="loadingSlots" class="h-4 w-4 animate-spin" aria-hidden="true" />
                <Search v-else class="h-4 w-4" aria-hidden="true" />
                Check {{ resourceWord.toLowerCase() }} availability
              </Button>
            </section>

            <section class="border-t pt-7">
              <div class="mb-4 flex items-center gap-3">
                <span class="grid h-9 w-9 place-items-center rounded-xl text-sm font-bold" :class="availabilityChecked ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'">2</span>
                <div>
                  <h2 class="font-bold">Available {{ resourceWord.toLowerCase() }}s</h2>
                  <p class="text-xs text-muted-foreground">Choose the option that works for your visit.</p>
                </div>
              </div>

              <div v-if="availabilityChecked && eligibleResources.length" class="grid gap-3 sm:grid-cols-2">
                <Button
                  v-for="resource in eligibleResources"
                  :key="resource.public_id"
                  type="button"
                  variant="outline"
                  class="group h-auto min-h-44 flex-col items-stretch justify-start gap-3 rounded-2xl p-4 text-left"
                  :class="form.resource_public_id === resource.public_id ? 'border-primary bg-primary/5 ring-2 ring-primary/15' : 'hover:border-primary/50 hover:bg-primary/[.03]'"
                  @click="selectResource(resource)"
                >
                  <span class="relative grid h-24 w-full place-items-center overflow-hidden rounded-xl bg-primary/[.06] text-primary">
                    <span
                      class="relative grid place-items-center border-2 border-primary/40 bg-white shadow-sm transition-transform duration-200 group-hover:scale-[1.03]"
                      :class="tableShapeClass(resource.shape)"
                    >
                      <Armchair
                        v-if="['table', 'booth'].includes(resource.element_type)"
                        class="h-6 w-6"
                        aria-hidden="true"
                      />
                      <LayoutGrid v-else class="h-6 w-6" aria-hidden="true" />
                    </span>
                    <span class="absolute left-1/2 top-2 h-2.5 w-7 -translate-x-1/2 rounded-full border border-primary/30 bg-white" />
                    <span v-if="Number(resource.capacity) > 1" class="absolute bottom-2 left-1/2 h-2.5 w-7 -translate-x-1/2 rounded-full border border-primary/30 bg-white" />
                    <span v-if="Number(resource.capacity) > 2" class="absolute left-3 top-1/2 h-7 w-2.5 -translate-y-1/2 rounded-full border border-primary/30 bg-white" />
                    <span v-if="Number(resource.capacity) > 3" class="absolute right-3 top-1/2 h-7 w-2.5 -translate-y-1/2 rounded-full border border-primary/30 bg-white" />
                    <span v-if="Number(resource.capacity) > 4" class="absolute left-7 top-2 h-2.5 w-6 rounded-full border border-primary/30 bg-white" />
                    <span v-if="Number(resource.capacity) > 5" class="absolute right-7 top-2 h-2.5 w-6 rounded-full border border-primary/30 bg-white" />
                    <span v-if="Number(resource.capacity) > 6" class="absolute bottom-2 left-7 h-2.5 w-6 rounded-full border border-primary/30 bg-white" />
                    <span v-if="Number(resource.capacity) > 7" class="absolute bottom-2 right-7 h-2.5 w-6 rounded-full border border-primary/30 bg-white" />
                  </span>
                  <span class="flex min-w-0 items-center gap-3">
                    <span class="min-w-0 flex-1">
                      <span class="block truncate text-sm font-bold">{{ resource.name }}</span>
                      <span class="mt-1 block text-xs font-normal capitalize text-muted-foreground">
                        {{ resource.capacity }} {{ Number(resource.capacity) === 1 ? guestWordSingular : guestWord }} · {{ resource.shape || 'standard' }}
                      </span>
                    </span>
                    <CheckCircle2 v-if="form.resource_public_id === resource.public_id" class="h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
                  </span>
                </Button>
              </div>

              <Button
                v-else-if="availabilityChecked && !isRestaurant && candidateSlots.length"
                type="button"
                variant="outline"
                class="h-auto w-full justify-start gap-3 rounded-2xl p-4 text-left"
                :class="form.resource_public_id === 'none' ? 'border-primary bg-primary/5 ring-2 ring-primary/15' : ''"
                @click="selectNoResource"
              >
                <span class="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary">
                  <CalendarCheck2 class="h-5 w-5" aria-hidden="true" />
                </span>
                <span>
                  <span class="block text-sm font-bold">No resource required</span>
                  <span class="mt-1 block text-xs font-normal text-muted-foreground">Continue with the available team member.</span>
                </span>
              </Button>

              <div v-else-if="availabilityChecked" class="rounded-2xl border border-dashed p-7 text-center">
                <CalendarX2 class="mx-auto h-7 w-7 text-muted-foreground/60" aria-hidden="true" />
                <p class="mt-3 text-sm font-semibold">No {{ resourceWord.toLowerCase() }} is available</p>
                <p class="mt-1 text-xs text-muted-foreground">Try another time, date, or smaller group.</p>
              </div>

              <p v-else class="rounded-2xl border border-dashed p-7 text-center text-sm text-muted-foreground">
                Check availability above to see matching {{ resourceWord.toLowerCase() }}s.
              </p>
            </section>

            <section class="border-t pt-7">
              <div class="mb-4 flex items-center gap-3">
                <span class="grid h-9 w-9 place-items-center rounded-xl text-sm font-bold" :class="selectedSlot ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'">3</span>
                <div>
                  <h2 class="font-bold">Your contact information</h2>
                  <p class="text-xs text-muted-foreground">The business uses this only for your {{ bookingLabel.toLowerCase() }}.</p>
                </div>
              </div>

              <fieldset :disabled="!selectedSlot" class="grid gap-4 disabled:opacity-55">
                <div class="grid gap-4 sm:grid-cols-2">
                  <div class="grid gap-2"><Label for="booking-first-name">First name</Label><Input id="booking-first-name" v-model.trim="form.first_name" placeholder="Alex" /></div>
                  <div class="grid gap-2"><Label for="booking-last-name">Last name</Label><Input id="booking-last-name" v-model.trim="form.last_name" placeholder="Morgan" /></div>
                </div>
                <div class="grid gap-4 sm:grid-cols-2">
                  <div class="grid gap-2"><Label for="booking-phone">Phone number</Label><Input id="booking-phone" v-model.trim="form.phone" type="tel" inputmode="tel" placeholder="+63 917 555 0142" /></div>
                  <div class="grid gap-2"><Label for="booking-email">Email <span class="font-normal text-muted-foreground">(optional if phone is provided)</span></Label><Input id="booking-email" v-model.trim="form.email" type="email" placeholder="alex@example.com" /></div>
                </div>
                <div class="grid gap-2">
                  <Label for="booking-notes">Special requests <span class="font-normal text-muted-foreground">(optional)</span></Label>
                  <Textarea id="booking-notes" v-model.trim="form.customer_notes" rows="3" maxlength="2000" placeholder="Accessibility, celebration, equipment, or other visit notes" />
                </div>
              </fieldset>

              <Alert v-if="formError" variant="destructive" class="mt-4">
                <AlertCircle class="h-4 w-4" aria-hidden="true" />
                <AlertTitle>{{ bookingLabel }} could not be sent</AlertTitle>
                <AlertDescription>{{ formError }}</AlertDescription>
              </Alert>

              <Button size="lg" class="mt-5 h-12 w-full" type="button" :disabled="submitting || !canSubmit" @click="submitBooking">
                <Loader2 v-if="submitting" class="h-5 w-5 animate-spin" aria-hidden="true" />
                <CalendarCheck2 v-else class="h-5 w-5" aria-hidden="true" />
                Send {{ bookingLabel.toLowerCase() }} request
              </Button>
              <p class="mt-3 text-center text-[11px] leading-5 text-muted-foreground">
                By submitting, you agree that {{ identity.display_name }} may contact you about this request.
              </p>
            </section>
          </CardContent>
        </Card>
      </div>
    </main>
  </div>
</template>

<script setup>
import {
  AlertCircle,
  Armchair,
  CalendarCheck2,
  CalendarX2,
  CheckCircle2,
  LayoutGrid,
  Loader2,
  MapPin,
  Phone,
  Search,
  Store,
} from 'lucide-vue-next'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ButtonAnchor } from '@/components/ui/button-anchor'
import { ButtonLink } from '@/components/ui/button-link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import ScheduleDatePicker from '@/components/scheduling/ScheduleDatePicker.vue'

definePageMeta({ layout: false })

const route = useRoute()
const { identity, pending, error, baseURL, siteBase: base } = useStorefrontContext(route.params.slug)
const { data: serviceData, pending: servicesPending, error: servicesError } = await useAsyncData(
  `booking-services:${route.params.slug}`,
  () => $fetch(`public/${route.params.slug}/catalog/`, {
    baseURL,
    query: { type: 'service' },
  }),
)

const services = computed(() => Array.isArray(serviceData.value) ? serviceData.value : serviceData.value?.results || [])
const selectedServiceSlug = ref(String(route.query.service || ''))
const selectedService = computed(() => services.value.find(item => item.slug === selectedServiceSlug.value) || null)
const isRestaurant = computed(() => identity.value?.industry_preset === 'restaurant')
const bookingLabel = computed(() => isRestaurant.value ? 'Reservation' : 'Booking')
const bookingVerb = computed(() => isRestaurant.value ? 'Reserve' : 'Book')
const resourceWord = computed(() => isRestaurant.value ? 'Table' : 'Resource')
const guestWordSingular = computed(() => isRestaurant.value ? 'guest' : 'person')
const guestWord = computed(() => isRestaurant.value ? 'guests' : 'people')
const durationMinutes = computed(() => Number(selectedService.value?.duration_minutes || 60))
const locationLabel = computed(() => [identity.value?.city, identity.value?.region, identity.value?.country].filter(Boolean).join(', ') || 'Location shared after confirmation')
const allSlots = ref([])
const resources = ref([])
const slotsLoaded = ref(false)
const loadingSlots = ref(false)
const availabilityChecked = ref(false)
const submitting = ref(false)
const formError = ref('')
const bookingResult = ref(null)
const selectedSlot = ref(null)
const partySizes = Array.from({ length: 20 }, (_, index) => index + 1)
const steps = computed(() => [
  `Choose your service, date, time, and ${isRestaurant.value ? 'party size' : 'group size'}.`,
  `Check live ${resourceWord.value.toLowerCase()} availability and make a selection.`,
  'Send your contact details for confirmation and reminders.',
])
const form = reactive({
  date: '',
  time: '',
  seats: '2',
  resource_public_id: '',
  first_name: '',
  last_name: '',
  phone: '',
  email: '',
  customer_notes: '',
})

const minimumDate = localDateKey(new Date())
const maximumDate = computed(() => {
  const date = new Date()
  date.setDate(date.getDate() + Math.min(Number(identity.value?.advance_booking_days || 31), 31))
  return localDateKey(date)
})
const dateSlots = computed(() => allSlots.value.filter(slot => localDateKey(new Date(slot.starts_at)) === form.date))
const timeOptions = computed(() => {
  const unique = new Map()
  for (const slot of dateSlots.value) {
    const value = localTimeKey(new Date(slot.starts_at))
    if (!unique.has(value)) unique.set(value, { value, label: formatTime(slot.starts_at) })
  }
  return [...unique.values()]
})
const candidateSlots = computed(() => dateSlots.value.filter(slot => localTimeKey(new Date(slot.starts_at)) === form.time))
const eligibleResources = computed(() => {
  const seats = Number(form.seats || 1)
  const availableIds = new Set(candidateSlots.value.flatMap(slot => slot.available_resource_public_ids || []))
  return resources.value.filter(resource => resource.is_active && Number(resource.capacity) >= seats && availableIds.has(resource.public_id))
})
const canSubmit = computed(() => Boolean(
  selectedSlot.value
  && form.first_name.trim().length >= 2
  && form.last_name.trim().length >= 1
  && (form.phone.trim() || form.email.trim()),
))
const formProgress = computed(() => {
  let complete = 0
  if (selectedService.value && form.date && form.time) complete += 1
  if (selectedSlot.value) complete += 1
  if (canSubmit.value) complete += 1
  return Math.round((complete / 3) * 100)
})
const bookingDateLabel = computed(() => {
  if (!bookingResult.value?.starts_at) return ''
  return new Intl.DateTimeFormat('en-PH', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(bookingResult.value.starts_at))
})

watch(services, (items) => {
  if (items.length && !items.some(item => item.slug === selectedServiceSlug.value)) {
    selectedServiceSlug.value = items[0].slug
  }
}, { immediate: true })

watch(selectedServiceSlug, async () => {
  resetFormAvailability()
  await loadAvailability()
})

onMounted(async () => {
  if (selectedService.value && !slotsLoaded.value) await loadAvailability()
})

async function loadAvailability() {
  if (!selectedService.value) return
  loadingSlots.value = true
  formError.value = ''
  try {
    const response = await $fetch(`public/${route.params.slug}/availability/${selectedService.value.slug}/`, {
      baseURL,
      query: {
        start: minimumDate,
        end: maximumDate.value,
        seats: Number(form.seats || 1),
      },
    })
    allSlots.value = response.slots || []
    resources.value = response.resources || []
    slotsLoaded.value = true
  } catch (requestError) {
    allSlots.value = []
    resources.value = []
    slotsLoaded.value = true
    formError.value = apiError(requestError, 'Availability could not be loaded. Please try again.')
  } finally {
    loadingSlots.value = false
  }
}

async function refreshForPartySize() {
  resetResourceSelection()
  await loadAvailability()
}

async function checkAvailability() {
  formError.value = ''
  availabilityChecked.value = true
  selectedSlot.value = null
  form.resource_public_id = ''
  if (!slotsLoaded.value) await loadAvailability()
  if (!isRestaurant.value && candidateSlots.value.length && !eligibleResources.value.length) selectNoResource()
}

function selectResource(resource) {
  form.resource_public_id = resource.public_id
  selectedSlot.value = candidateSlots.value.find(slot => slot.available_resource_public_ids?.includes(resource.public_id)) || null
}

function selectNoResource() {
  form.resource_public_id = 'none'
  selectedSlot.value = candidateSlots.value[0] || null
}

function tableShapeClass(shape) {
  if (shape === 'round') return 'h-16 w-16 rounded-full'
  if (shape === 'square') return 'h-16 w-16 rounded-xl'
  return 'h-14 w-24 rounded-xl'
}

function resetSelection() {
  form.time = ''
  resetResourceSelection()
}

function resetResourceSelection() {
  availabilityChecked.value = false
  form.resource_public_id = ''
  selectedSlot.value = null
  formError.value = ''
}

function resetFormAvailability() {
  allSlots.value = []
  resources.value = []
  slotsLoaded.value = false
  form.date = ''
  resetSelection()
}

async function submitBooking() {
  if (!canSubmit.value || !selectedService.value || submitting.value) return
  submitting.value = true
  formError.value = ''
  try {
    bookingResult.value = await $fetch(`public/${route.params.slug}/bookings/`, {
      baseURL,
      method: 'POST',
      body: {
        offering_public_id: selectedService.value.public_id,
        staff_public_id: selectedSlot.value.staff_public_id,
        location_public_id: selectedSlot.value.location_public_id,
        resource_public_ids: form.resource_public_id && form.resource_public_id !== 'none' ? [form.resource_public_id] : [],
        starts_at: selectedSlot.value.starts_at,
        ends_at: selectedSlot.value.ends_at,
        timezone: identity.value.timezone || 'Asia/Manila',
        seats: Number(form.seats),
        payment_method: 'manual',
        first_name: form.first_name,
        last_name: form.last_name,
        phone: form.phone,
        email: form.email,
        customer_notes: form.customer_notes,
      },
    })
  } catch (requestError) {
    formError.value = apiError(requestError, `The ${bookingLabel.value.toLowerCase()} request could not be sent.`)
    if (requestError?.status === 409 || requestError?.statusCode === 409) {
      await loadAvailability()
      availabilityChecked.value = true
    }
  } finally {
    submitting.value = false
  }
}

function startAnotherBooking() {
  bookingResult.value = null
  Object.assign(form, {
    date: '',
    time: '',
    seats: '2',
    resource_public_id: '',
    first_name: '',
    last_name: '',
    phone: '',
    email: '',
    customer_notes: '',
  })
  resetResourceSelection()
}

function apiError(requestError, fallback) {
  const payload = requestError?.data || {}
  const details = payload?.error?.details || payload
  const firstFieldError = Object.values(details).find(value => Array.isArray(value) && value.length)?.[0]
  return payload?.error?.message || payload?.detail || firstFieldError || fallback
}

function localDateKey(date) {
  const pad = value => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function localTimeKey(date) {
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function formatTime(value) {
  return new Intl.DateTimeFormat('en-PH', { hour: 'numeric', minute: '2-digit' }).format(new Date(value))
}

useHead(() => ({
  title: identity.value ? `${bookingVerb.value} with ${identity.value.display_name} | PixelCore` : `${bookingLabel.value} | PixelCore`,
  meta: [
    {
      name: 'description',
      content: identity.value
        ? `Check live availability and request a ${bookingLabel.value.toLowerCase()} with ${identity.value.display_name}.`
        : 'Check live business availability and request a booking.',
    },
    { name: 'robots', content: 'index,follow' },
  ],
  link: [{ rel: 'canonical', href: `/site/${route.params.slug}/booking` }],
}))
</script>
