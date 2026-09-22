<template>
  <section class="workspace-page space-y-5">
    <PageHeader title="Business tracker" description="A single, factual activity trail across commerce, scheduling, workforce, devices, and business settings.">
      <template #actions>
        <Button variant="outline" type="button" :disabled="loading" @click="load"><RefreshCw class="h-4 w-4" :class="loading ? 'animate-spin' : ''" aria-hidden="true" /> Refresh</Button>
      </template>
    </PageHeader>

    <dl class="grid overflow-hidden rounded-xl border bg-card sm:grid-cols-2 xl:grid-cols-4">
      <div v-for="metric in metrics" :key="metric.label" class="border-b p-4 last:border-b-0 sm:[&:nth-child(odd)]:border-r sm:[&:nth-last-child(-n+2)]:border-b-0 xl:border-b-0 xl:border-r xl:last:border-r-0">
        <div class="flex items-center justify-between gap-3"><dt class="text-sm font-semibold text-muted-foreground">{{ metric.label }}</dt><component :is="metric.icon" class="h-4 w-4 text-muted-foreground" aria-hidden="true" /></div>
        <dd class="mt-3 text-2xl font-extrabold tabular-nums">{{ metric.value }}</dd>
        <p class="mt-1 text-xs text-muted-foreground">{{ metric.detail }}</p>
      </div>
    </dl>

    <div class="grid gap-5 xl:grid-cols-[18rem_minmax(0,1fr)]">
      <aside class="space-y-5">
        <Card>
          <CardHeader><CardTitle class="text-base">Filter activity</CardTitle><CardDescription>Narrow the operational trail without changing stored records.</CardDescription></CardHeader>
          <CardContent class="space-y-4">
            <div><label class="field-label" for="tracker-search">Search</label><Input id="tracker-search" v-model.trim="search" placeholder="Action, person, or resource" /></div>
            <div><label class="field-label" for="tracker-category">Area</label><NativeSelect id="tracker-category" v-model="category"><option value="all">All activity</option><option v-for="option in categories" :key="option.value" :value="option.value">{{ option.label }}</option></NativeSelect></div>
          </CardContent>
        </Card>
        <Alert>
          <ShieldCheck class="h-4 w-4" aria-hidden="true" />
          <AlertTitle>Audit-backed</AlertTitle>
          <AlertDescription>This view uses PixelCore audit records. It does not invent status updates or forecasts.</AlertDescription>
        </Alert>
      </aside>

      <main class="min-w-0">
        <StatePanel v-if="loading" kind="loading" title="Loading business activity" message="Retrieving the latest audited changes." />
        <StatePanel v-else-if="error" kind="error" title="Tracker unavailable" :message="error"><Button variant="outline" type="button" @click="load">Try again</Button></StatePanel>
        <StatePanel v-else-if="!filteredEvents.length" title="No matching activity" message="Try another area or search term. New business changes will appear here automatically." />
        <Card v-else class="overflow-hidden">
          <CardHeader class="border-b"><div class="flex items-center justify-between gap-3"><div><CardTitle class="text-base">Recent activity</CardTitle><CardDescription>{{ filteredEvents.length }} event{{ filteredEvents.length === 1 ? '' : 's' }} shown</CardDescription></div><Badge variant="outline">Newest first</Badge></div></CardHeader>
          <CardContent class="p-0">
            <ol class="divide-y">
              <li v-for="event in filteredEvents" :key="event.id" class="grid gap-3 px-4 py-4 sm:grid-cols-[2.5rem_minmax(0,1fr)_auto] sm:px-5">
                <span class="grid h-10 w-10 place-items-center rounded-lg bg-muted text-muted-foreground"><component :is="iconFor(event)" class="h-[18px] w-[18px]" aria-hidden="true" /></span>
                <div class="min-w-0">
                  <div class="flex flex-wrap items-center gap-2"><p class="font-bold">{{ actionLabel(event.action) }}</p><Badge variant="secondary" class="capitalize">{{ areaFor(event) }}</Badge></div>
                  <p class="mt-1 text-sm text-muted-foreground">{{ event.actor_email || 'Automated system' }} · {{ resourceLabel(event.resource_type) }}</p>
                  <p v-if="event.metadata?.summary" class="mt-2 text-sm leading-6">{{ event.metadata.summary }}</p>
                </div>
                <time class="text-xs font-semibold text-muted-foreground sm:pt-1" :datetime="event.created_at">{{ formatDate(event.created_at) }}</time>
              </li>
            </ol>
          </CardContent>
        </Card>
      </main>
    </div>
  </section>
</template>

<script setup>
import { Activity, CalendarDays, CreditCard, MonitorSmartphone, Package, RefreshCw, Settings2, ShieldCheck, UserRoundCog, UsersRound } from 'lucide-vue-next'

const business = useBusinessStore()
const { apiFetch } = useApiClient()
const events = ref([])
const loading = ref(true)
const error = ref('')
const search = ref('')
const category = ref('all')

const categories = [
  { value: 'commerce', label: 'Commerce' },
  { value: 'schedule', label: 'Schedule' },
  { value: 'workforce', label: 'Workforce' },
  { value: 'devices', label: 'Devices & displays' },
  { value: 'business', label: 'Business settings' },
]

const filteredEvents = computed(() => {
  const term = search.value.toLowerCase()
  return events.value.filter((event) => {
    const matchesArea = category.value === 'all' || areaFor(event) === category.value
    const haystack = `${event.action} ${event.resource_type} ${event.actor_email || ''} ${event.metadata?.summary || ''}`.toLowerCase()
    return matchesArea && (!term || haystack.includes(term))
  })
})

const metrics = computed(() => {
  const today = new Date(); today.setHours(0, 0, 0, 0)
  const todaysEvents = events.value.filter((event) => new Date(event.created_at) >= today)
  return [
    { label: 'Changes today', value: todaysEvents.length, detail: 'Audited actions since midnight', icon: Activity },
    { label: 'Order activity', value: events.value.filter((event) => areaFor(event) === 'commerce').length, detail: 'In the latest activity page', icon: CreditCard },
    { label: 'Schedule activity', value: events.value.filter((event) => areaFor(event) === 'schedule').length, detail: 'Bookings, availability, and events', icon: CalendarDays },
    { label: 'People active', value: new Set(events.value.filter((event) => event.actor_email).map((event) => event.actor_email)).size, detail: 'Actors in the latest activity page', icon: UsersRound },
  ]
})

watch(() => business.activeBusiness?.public_id, load)
onMounted(async () => { if (!business.activeBusiness) await business.loadBusinesses(); await load() })

async function load() {
  if (!business.activeBusiness) return
  loading.value = true
  error.value = ''
  try {
    const response = await apiFetch(`businesses/${business.activeBusiness.public_id}/audit-events/?page_size=50`)
    events.value = response.results || []
  } catch (requestError) {
    error.value = requestError?.data?.error?.message || 'Could not retrieve the business audit trail.'
  } finally {
    loading.value = false
  }
}

function areaFor(event) {
  const value = `${event.resource_type} ${event.action}`
  if (/(order|cart|payment|discount|customer|offering|inventory|expense|invoice|quotation|supplier)/.test(value)) return 'commerce'
  if (/(booking|event|availability|resource|session)/.test(value)) return 'schedule'
  if (/(staff|attendance|leave|workforce|invitation)/.test(value)) return 'workforce'
  if (/(device|display)/.test(value)) return 'devices'
  return 'business'
}

function iconFor(event) {
  return { commerce: Package, schedule: CalendarDays, workforce: UserRoundCog, devices: MonitorSmartphone, business: Settings2 }[areaFor(event)]
}

function actionLabel(action = '') {
  const [resource, verb] = action.split('.')
  const actionVerb = { created: 'created', updated: 'updated', deleted: 'removed', cancelled: 'cancelled', accepted: 'accepted', pairing_code_issued: 'received a new setup code' }[verb] || (verb || 'changed').replaceAll('_', ' ')
  return `${resourceLabel(resource)} ${actionVerb}`
}

function resourceLabel(value = '') {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase()) || 'Business record'
}

function formatDate(value) {
  return new Intl.DateTimeFormat('en-PH', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}
</script>
