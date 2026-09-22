<template>
  <section class="workspace-page space-y-5">
    <header class="flex flex-wrap items-end justify-between gap-4"><div><h1 class="text-2xl font-extrabold tracking-tight">Product requests</h1><p class="mt-2 text-sm text-muted-foreground">Stock holds, rentals, returns, and customer follow-up.</p></div><ButtonLink variant="outline" to="/settings/commerce"><Settings2 class="h-4 w-4" />Request settings</ButtonLink></header>
    <div v-if="data?.summary" class="flex flex-wrap gap-x-8 gap-y-3 border-y py-4 text-sm"><span class="inline-flex items-center gap-2"><Clock3 class="h-4 w-4 text-muted-foreground" /><strong class="text-xl tabular-nums">{{ data.summary.pending }}</strong> awaiting review</span><span class="inline-flex items-center gap-2"><CalendarRange class="h-4 w-4 text-muted-foreground" /><strong class="text-xl tabular-nums">{{ data.summary.rentals }}</strong> active rentals</span><NuxtLink to="/workspace/sell/requests?scope=overdue" class="inline-flex items-center gap-2 font-semibold hover:underline" :class="data.summary.overdue ? 'text-destructive' : 'text-muted-foreground'"><CircleAlert class="h-4 w-4" /><strong class="text-xl tabular-nums">{{ data.summary.overdue }}</strong> overdue returns</NuxtLink></div>
    <section class="overflow-hidden rounded-xl border bg-card">
      <div class="space-y-4 p-4 sm:p-5">
        <div class="flex flex-wrap gap-2" aria-label="Request queues"><Button v-for="tab in tabs" :key="tab.key" type="button" size="sm" :variant="scope === tab.key ? 'default' : 'ghost'" :aria-pressed="scope === tab.key" @click="setScope(tab.key)">{{ tab.label }}<span v-if="data?.summary" class="ml-2 font-bold tabular-nums">{{ data.summary[tab.key] }}</span></Button></div>
        <div class="flex flex-wrap items-center justify-between gap-3"><form class="flex w-full gap-2 sm:max-w-md" @submit.prevent="filter({ search, page: undefined })"><Input v-model.trim="search" aria-label="Search requests by product or customer" placeholder="Search product, customer, email or phone" /><Button type="submit" variant="outline"><Search class="h-4 w-4" /><span class="sr-only">Search requests</span></Button></form><LiveRefresh v-model="live" :busy="refreshing" :stale="Boolean(error)" :updated-at="updatedAt" @refresh="refresh" /></div>
        <p v-if="scope === 'overdue'" class="text-sm leading-6 text-muted-foreground">Oldest due dates first. Contact the customer, record an agreed extension, or confirm the physical return. Dates use {{ business.activeBusiness?.timezone }}.</p>
        <p v-else-if="scope === 'returned'" class="text-sm text-muted-foreground">Returned rentals no longer hold stock. Use Review to inspect details or add a follow-up note.</p>
        <p v-else-if="scope === 'attention'" class="text-sm text-muted-foreground">Requests awaiting review, overdue returns, and missed rental collections.</p>
        <div v-if="route.query.kind || route.query.status || route.query.search" class="flex flex-wrap items-center gap-2 text-xs text-muted-foreground"><span v-if="route.query.kind">Type: {{ route.query.kind }}</span><span v-if="route.query.status">Status: {{ label(route.query.status) }}</span><span v-if="route.query.search">Search: {{ route.query.search }}</span><Button variant="ghost" size="sm" @click="filter({ kind: undefined, status: undefined, search: undefined, page: undefined })">Clear filters</Button></div>
      </div>
      <StatePanel v-if="loading" kind="loading" title="Loading product requests" />
      <Alert v-else-if="error" variant="destructive" class="m-4 w-auto"><AlertTitle>Requests could not refresh</AlertTitle><AlertDescription>{{ error }}</AlertDescription></Alert>
      <template v-if="!loading && data">
        <div v-if="!data.results.length" class="border-t px-5 py-12 text-center"><PackageCheck class="mx-auto h-7 w-7 text-muted-foreground" /><h2 class="mt-3 font-semibold">No matching requests</h2><p class="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">There is nothing in this queue. Choose another view or clear your search to find earlier requests.</p><Button class="mt-4" variant="outline" @click="setScope('all')">View all requests</Button></div>
        <div v-else class="divide-y border-t">
          <div class="hidden grid-cols-[1.5fr_1fr_1fr_auto] gap-4 bg-muted/40 px-5 py-3 text-xs font-semibold text-muted-foreground lg:grid"><span>Product / customer</span><span>Collection / dates</span><span>Status / attention</span><span class="min-w-32 text-right">Action</span></div>
          <article v-for="item in data.results" :key="item.public_id" class="grid gap-4 px-4 py-5 transition-colors hover:bg-muted/40 sm:px-5 lg:grid-cols-[1.5fr_1fr_1fr_auto] lg:items-center">
            <div class="flex items-start gap-3"><component :is="item.kind === 'rental' ? CalendarRange : PackageCheck" class="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground" /><div class="min-w-0"><h2 class="text-sm font-bold">{{ item.snapshot.name }}</h2><p class="mt-1 text-xs text-muted-foreground">{{ item.snapshot.variant }} · {{ item.quantity }} units · {{ item.kind === 'rental' ? 'Rental' : 'Stock hold' }}</p><p class="mt-3 text-sm">{{ item.first_name }} {{ item.last_name }}</p><p class="mt-1 break-all text-xs text-muted-foreground">{{ item.email }}</p></div></div>
            <div class="text-sm"><p>{{ item.location_name }}</p><p class="mt-1 text-xs leading-5 text-muted-foreground">{{ item.kind === 'rental' ? item.starts_on + ' – ' + item.ends_on : 'Hold until ' + dateTime(item.expires_at) }}</p><p v-if="item.status === 'returned'" class="mt-2 text-xs text-muted-foreground">Updated {{ dateTime(item.updated_at) }}</p></div>
            <div><Badge :variant="item.attention?.code === 'overdue' ? 'destructive' : 'secondary'">{{ item.attention?.label || label(item.status) }}</Badge><p class="mt-2 text-xs text-muted-foreground">{{ item.stock_held ? 'Stock set aside' : 'No stock held' }}</p><p v-if="item.order_number" class="mt-1 text-xs">{{ item.order_number }}</p></div>
            <div class="flex flex-wrap gap-2 lg:min-w-32 lg:flex-col"><Button type="button" variant="outline" size="sm" @click="review(item)">Review & contact<ArrowUpRight class="h-3.5 w-3.5" /></Button><Button v-if="item.status === 'collected'" type="button" variant="ghost" size="sm" @click="review(item, 'return')"><PackageCheck class="h-3.5 w-3.5" />Record return</Button></div>
          </article>
        </div>
        <RecordPagination :page="page" :count="data.count" :size="20" :busy="refreshing" @page="filter({ page: $event })" />
      </template>
    </section>
    <RequestReviewDialog :item="selected" :initial-action="initialAction" @close="selected = null" @updated="refresh" />
  </section>
</template>
<script setup>
import { ArrowUpRight, CalendarRange, CircleAlert, Clock3, PackageCheck, Search, Settings2 } from 'lucide-vue-next'
import LiveRefresh from '~/components/workspace/LiveRefresh.vue'
import RecordPagination from '~/components/workspace/RecordPagination.vue'
import RequestReviewDialog from '~/components/workspace/RequestReviewDialog.vue'
import { requestStatusLabel } from '~/utils/requestStatus'
const route = useRoute(), router = useRouter(), business = useBusinessStore()
const page = computed(() => Math.max(1, Math.floor(Number(route.query.page)) || 1))
const scope = computed(() => String(route.query.scope || 'all'))
const selected = ref(null), initialAction = ref(''), search = ref(String(route.query.search || ''))
const label = requestStatusLabel
const tabs = [{ key: 'attention', label: 'Needs attention' }, { key: 'overdue', label: 'Overdue' }, { key: 'due_today', label: 'Due today' }, { key: 'pending', label: 'Awaiting review' }, { key: 'rentals', label: 'Active rentals' }, { key: 'held', label: 'Stock holds' }, { key: 'returned', label: 'Returned' }, { key: 'closed', label: 'History' }, { key: 'all', label: 'All requests' }]
const { data, loading, refreshing, error, updatedAt, live, refresh } = useLiveWorkspaceResource(() => 'product-requests/', () => ({ scope: scope.value, page: page.value, page_size: 20, kind: route.query.kind, status: route.query.status, search: route.query.search }), computed(() => Boolean(selected.value)))
watch(() => route.query.search, value => { search.value = String(value || '') })
watch(() => business.activeBusiness?.public_id, () => { selected.value = null })
function filter(query) { router.replace({ query: { ...route.query, ...query } }) }
function setScope(value) { filter({ scope: value, status: undefined, kind: undefined, search: undefined, page: undefined }) }
function review(item, action = '') { initialAction.value = action; selected.value = item }
function dateTime(value) { return value ? new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short', timeZone: business.activeBusiness?.timezone || 'Asia/Manila' }).format(new Date(value)) : '—' }
</script>
