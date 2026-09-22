<template>
  <div class="min-h-screen bg-[#f4f1eb] text-slate-950">
    <main class="mx-auto max-w-screen-2xl px-4 py-5 sm:px-6 lg:px-8">
      <div v-if="pending" class="grid min-h-[70vh] place-items-center text-center">
        <div>
          <Loader2 class="mx-auto h-8 w-8 animate-spin text-primary" aria-hidden="true" />
          <p class="mt-3 text-sm text-muted-foreground">Opening the event workspace…</p>
        </div>
      </div>

      <StatePanel
        v-else-if="loadError || !payload"
        kind="error"
        title="Organizer link unavailable"
        message="This management link is invalid or has been replaced. Ask the PixelCore workspace administrator for a new organizer link."
      />

      <div v-else class="space-y-5">
        <section class="overflow-hidden rounded-2xl border bg-[#10362f] text-white shadow-sm">
          <div class="grid gap-0 lg:grid-cols-[minmax(0,1fr)_21rem]">
            <div class="p-5 sm:p-7">
              <div class="flex items-center gap-3">
                <Avatar class="h-10 w-10 border border-white/15 bg-white/10">
                  <AvatarImage v-if="event.business.logo" :src="event.business.logo" :alt="event.business.display_name" />
                  <AvatarFallback class="bg-white/10 text-white">{{ initials(event.business.display_name) }}</AvatarFallback>
                </Avatar>
                <div>
                  <p class="text-xs font-bold uppercase tracking-[0.18em] text-emerald-200">Organizer workspace</p>
                  <p class="mt-0.5 text-sm text-white/70">{{ event.business.display_name }}</p>
                </div>
              </div>
              <h1 class="mt-5 text-3xl font-black tracking-[-0.04em] sm:text-4xl">{{ event.title }}</h1>
              <div class="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-sm text-white/70">
                <span class="flex items-center gap-2"><CalendarDays class="h-4 w-4" aria-hidden="true" />{{ formatDateTime(event.starts_at) }}</span>
                <span class="flex items-center gap-2"><MapPin class="h-4 w-4" aria-hidden="true" />{{ event.location?.name || 'Location not assigned' }}</span>
                <span class="flex items-center gap-2"><LayoutGrid class="h-4 w-4" aria-hidden="true" />{{ event.layout?.name || 'No floor plan' }}</span>
              </div>
            </div>
            <div class="border-t border-white/10 bg-black/10 p-5 lg:border-l lg:border-t-0">
              <div class="flex items-start gap-3">
                <ShieldCheck class="mt-0.5 h-5 w-5 shrink-0 text-emerald-200" aria-hidden="true" />
                <div>
                  <p class="font-bold">Private management link</p>
                  <p class="mt-1 text-xs leading-5 text-white/65">Anyone with this link can see and update the guest list. Do not post it publicly.</p>
                </div>
              </div>
              <Button variant="outline" size="sm" class="mt-4 w-full border-white/20 bg-white/10 text-white hover:bg-white/15 hover:text-white" type="button" @click="copyCurrentLink">
                <Copy class="h-4 w-4" aria-hidden="true" />
                Copy organizer link
              </Button>
            </div>
          </div>
        </section>

        <dl class="grid overflow-hidden rounded-xl border bg-white sm:grid-cols-2 xl:grid-cols-4">
          <div v-for="metric in metrics" :key="metric.label" class="border-b p-4 sm:border-r xl:border-b-0 last:border-r-0">
            <div class="flex items-center justify-between gap-3">
              <dt class="text-xs font-bold uppercase tracking-[0.12em] text-muted-foreground">{{ metric.label }}</dt>
              <component :is="metric.icon" class="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            </div>
            <dd class="mt-2 text-2xl font-black tabular-nums">{{ metric.value }}</dd>
            <p class="mt-1 text-xs text-muted-foreground">{{ metric.detail }}</p>
          </div>
        </dl>

        <div class="grid gap-5 xl:grid-cols-[22rem_minmax(0,1fr)]">
          <Card class="h-fit xl:sticky xl:top-5">
            <CardHeader class="border-b">
              <CardTitle class="text-lg">Seating overview</CardTitle>
              <CardDescription>Choose a table to filter the invited list.</CardDescription>
            </CardHeader>
            <CardContent class="space-y-2 p-3">
              <Button
                type="button"
                variant="outline"
                class="h-auto w-full justify-start rounded-xl p-3 text-left"
                :class="selectedTableId === 'all' ? 'border-primary bg-primary/5' : ''"
                @click="selectedTableId = 'all'"
              >
                <Users class="h-5 w-5 text-primary" aria-hidden="true" />
                <span>
                  <span class="block font-bold">All invited</span>
                  <span class="text-xs text-muted-foreground">{{ guests.length }} guest records</span>
                </span>
              </Button>
              <Button
                v-for="table in tables"
                :key="table.public_id"
                type="button"
                variant="outline"
                class="h-auto w-full justify-start rounded-xl p-3 text-left transition-transform hover:-translate-y-0.5 hover:shadow-sm"
                :class="selectedTableId === table.public_id ? 'border-primary bg-primary/5' : ''"
                @click="selectedTableId = table.public_id"
              >
                <span class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-emerald-100 text-emerald-800">
                  <Armchair class="h-5 w-5" aria-hidden="true" />
                </span>
                <span class="min-w-0">
                  <span class="block truncate font-bold">{{ table.name }}</span>
                  <span class="text-xs text-muted-foreground">{{ assignedSeats(table.public_id) }} / {{ table.capacity }} seats</span>
                </span>
              </Button>
              <p v-if="!tables.length" class="px-3 py-8 text-center text-xs leading-5 text-muted-foreground">
                No seating plan is attached. The guest list still works without table assignments.
              </p>
            </CardContent>
          </Card>

          <Card class="min-w-0 overflow-hidden">
            <CardHeader class="border-b p-5">
              <div class="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                <div>
                  <CardTitle class="text-lg">{{ selectedTableName }}</CardTitle>
                  <CardDescription>{{ filteredGuests.length }} invited record{{ filteredGuests.length === 1 ? '' : 's' }}</CardDescription>
                </div>
                <Button type="button" @click="openGuestDialog">
                  <UserPlus class="h-4 w-4" aria-hidden="true" />
                  Add guest
                </Button>
              </div>
            </CardHeader>
            <CardContent class="p-0">
              <div class="overflow-x-auto">
                <Table class="min-w-[54rem]">
                  <TableHeader>
                    <TableRow>
                      <TableHead>Guest</TableHead>
                      <TableHead>Response</TableHead>
                      <TableHead>Party</TableHead>
                      <TableHead>Table</TableHead>
                      <TableHead class="text-right">Invitation</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow v-for="guest in filteredGuests" :key="guest.public_id" class="transition-colors hover:bg-muted/40">
                      <TableCell>
                        <p class="font-semibold">{{ guest.full_name }}</p>
                        <p class="text-xs text-muted-foreground">{{ guest.email || guest.phone }}</p>
                      </TableCell>
                      <TableCell>
                        <Select :model-value="guest.response" @update:model-value="value => updateGuest(guest, { response: value })">
                          <SelectTrigger class="h-9 w-36"><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="pending">Awaiting reply</SelectItem>
                            <SelectItem value="accepted">Attending</SelectItem>
                            <SelectItem value="maybe">Maybe</SelectItem>
                            <SelectItem value="declined">Not attending</SelectItem>
                          </SelectContent>
                        </Select>
                      </TableCell>
                      <TableCell>{{ guest.party_size }}</TableCell>
                      <TableCell>
                        <Select :model-value="guest.table_public_id || 'unassigned'" @update:model-value="value => updateGuest(guest, { table_public_id: value === 'unassigned' ? null : value })">
                          <SelectTrigger class="h-9 w-40"><SelectValue placeholder="Unassigned" /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="unassigned">Unassigned</SelectItem>
                            <SelectItem v-for="table in tables" :key="table.public_id" :value="table.public_id">{{ table.name }}</SelectItem>
                          </SelectContent>
                        </Select>
                      </TableCell>
                      <TableCell>
                        <div class="flex justify-end gap-2">
                          <Button variant="outline" size="sm" type="button" :disabled="saving" @click="copyInviteLink(guest)">
                            <Send class="h-4 w-4" aria-hidden="true" />
                            Copy RSVP link
                          </Button>
                          <Button variant="ghost" size="icon" type="button" :disabled="saving" :aria-label="`Remove ${guest.full_name}`" @click="removeGuest(guest)">
                            <Trash2 class="h-4 w-4 text-destructive" aria-hidden="true" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                    <TableRow v-if="!filteredGuests.length">
                      <TableCell colspan="5" class="h-32 text-center text-muted-foreground">No invited guests in this view.</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </main>

    <Dialog v-model:open="guestDialogOpen">
      <DialogContent>
        <DialogHeader>
          <DialogTitle class="flex items-center gap-2"><UserPlus class="h-5 w-5 text-primary" aria-hidden="true" />Add invited guest</DialogTitle>
          <DialogDescription>Create one invitation for a person, household, or party.</DialogDescription>
        </DialogHeader>
        <div class="grid gap-4 py-2">
          <div class="grid gap-2"><Label for="guest-name">Guest or household name</Label><Input id="guest-name" v-model="guestForm.full_name" /></div>
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="grid gap-2"><Label for="guest-email">Email</Label><Input id="guest-email" v-model="guestForm.email" type="email" /></div>
            <div class="grid gap-2"><Label for="guest-phone">Phone</Label><Input id="guest-phone" v-model="guestForm.phone" /></div>
          </div>
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="grid gap-2"><Label for="guest-party">Party size</Label><Input id="guest-party" v-model.number="guestForm.party_size" type="number" min="1" max="50" /></div>
            <div class="grid gap-2">
              <Label>Table</Label>
              <Select v-model="guestForm.table_public_id">
                <SelectTrigger><SelectValue placeholder="Unassigned" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="unassigned">Unassigned</SelectItem>
                  <SelectItem v-for="table in tables" :key="table.public_id" :value="table.public_id">{{ table.name }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" type="button" @click="guestDialogOpen = false">Cancel</Button>
          <Button type="button" :disabled="saving || !canCreateGuest" @click="createGuest">
            <Loader2 v-if="saving" class="h-4 w-4 animate-spin" aria-hidden="true" />
            Add guest
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup>
import {
  Armchair,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Copy,
  LayoutGrid,
  Loader2,
  MapPin,
  Send,
  ShieldCheck,
  Trash2,
  UserPlus,
  Users,
} from 'lucide-vue-next'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { toast } from '@/components/ui/toast'

definePageMeta({ layout: false })
useHead({
  title: 'Event organizer | PixelCore',
  meta: [{ name: 'referrer', content: 'no-referrer' }],
})

const route = useRoute()
const config = useRuntimeConfig()
const apiBase = import.meta.server ? config.apiInternalBaseUrl : config.public.apiBaseUrl
const rootEndpoint = `public/events/${route.params.eventId}/manage/${route.params.token}/`

const { data: payload, pending, error: loadError, refresh } = await useAsyncData(
  `event-organizer:${route.params.eventId}:${route.params.token}`,
  () => $fetch(rootEndpoint, { baseURL: apiBase }),
)

const saving = ref(false)
const selectedTableId = ref('all')
const guestDialogOpen = ref(false)
const event = computed(() => payload.value?.event || {})
const guests = computed(() => payload.value?.guests || [])
const tables = computed(() => payload.value?.tables || [])
const counts = computed(() => payload.value?.guest_counts || {})
const filteredGuests = computed(() => selectedTableId.value === 'all' ? guests.value : guests.value.filter(guest => guest.table_public_id === selectedTableId.value))
const selectedTableName = computed(() => selectedTableId.value === 'all' ? 'All invited guests' : tables.value.find(table => table.public_id === selectedTableId.value)?.name || 'Table guests')
const unassignedCount = computed(() => guests.value.filter(guest => !guest.table_public_id).length)
const metrics = computed(() => [
  { label: 'Invited', value: counts.value.total || guests.value.length, detail: 'Households and parties', icon: Users },
  { label: 'Attending', value: counts.value.accepted || 0, detail: `${counts.value.attending_people || 0} confirmed people`, icon: CheckCircle2 },
  { label: 'Awaiting', value: counts.value.pending || 0, detail: 'Still need a response', icon: Clock3 },
  { label: 'Unassigned', value: unassignedCount.value, detail: 'Need a table', icon: Armchair },
])
const guestForm = reactive({ full_name: '', email: '', phone: '', party_size: 1, table_public_id: 'unassigned' })
const canCreateGuest = computed(() => Boolean(guestForm.full_name.trim() && (guestForm.email.trim() || guestForm.phone.trim())))

function openGuestDialog() {
  Object.assign(guestForm, { full_name: '', email: '', phone: '', party_size: 1, table_public_id: selectedTableId.value === 'all' ? 'unassigned' : selectedTableId.value })
  guestDialogOpen.value = true
}

async function createGuest() {
  saving.value = true
  try {
    await $fetch(`${rootEndpoint}guests/`, {
      baseURL: config.public.apiBaseUrl,
      method: 'POST',
      body: { ...guestForm, party_size: Number(guestForm.party_size), table_public_id: guestForm.table_public_id === 'unassigned' ? null : guestForm.table_public_id },
    })
    await refresh()
    guestDialogOpen.value = false
    toast({ title: 'Guest added', description: 'You can now copy their private RSVP link.' })
  } catch (error) {
    failedToast(error)
  } finally {
    saving.value = false
  }
}

async function updateGuest(guest, changes) {
  saving.value = true
  const previous = { ...guest }
  Object.assign(guest, changes)
  try {
    await $fetch(`${rootEndpoint}guests/${guest.public_id}/`, { baseURL: config.public.apiBaseUrl, method: 'PATCH', body: changes })
    await refresh()
    toast({ title: 'Guest updated' })
  } catch (error) {
    Object.assign(guest, previous)
    failedToast(error)
  } finally {
    saving.value = false
  }
}

async function removeGuest(guest) {
  saving.value = true
  try {
    await $fetch(`${rootEndpoint}guests/${guest.public_id}/`, { baseURL: config.public.apiBaseUrl, method: 'DELETE' })
    await refresh()
    toast({ title: 'Guest removed', description: `${guest.full_name} is no longer on the invited list.` })
  } catch (error) {
    failedToast(error)
  } finally {
    saving.value = false
  }
}

async function copyInviteLink(guest) {
  saving.value = true
  try {
    const response = await $fetch(`${rootEndpoint}guests/${guest.public_id}/invite-link/`, { baseURL: config.public.apiBaseUrl, method: 'POST' })
    await navigator.clipboard.writeText(`${window.location.origin}/event/${event.value.public_id}/rsvp/${response.token}`)
    toast({ title: 'Private RSVP link copied', description: `Send it only to ${guest.full_name}.` })
  } catch (error) {
    failedToast(error)
  } finally {
    saving.value = false
  }
}

async function copyCurrentLink() {
  await navigator.clipboard.writeText(window.location.href)
  toast({ title: 'Organizer link copied' })
}

function assignedSeats(tableId) {
  return guests.value.filter(guest => guest.table_public_id === tableId && guest.response !== 'declined').reduce((sum, guest) => sum + Number(guest.party_size || 0), 0)
}

function formatDateTime(value) {
  return new Intl.DateTimeFormat('en-PH', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function initials(value) {
  return String(value || 'PC').split(/\s+/).slice(0, 2).map(part => part[0]).join('').toUpperCase()
}

function failedToast(error) {
  toast({ title: 'Could not save changes', description: error?.data?.error?.message || 'Please try again.', variant: 'destructive' })
}
</script>
