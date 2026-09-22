<template>
  <section class="workspace-page space-y-5">
    <PageHeader title="Promotions" description="Manage discount codes, automatic offers, and where each promotion applies.">
      <template #actions><ButtonLink to="/workspace/sell/promotions/new"><Plus class="h-4 w-4" aria-hidden="true" />Create promotion</ButtonLink></template>
    </PageHeader>
    <dl class="grid grid-cols-2 overflow-hidden rounded-xl border bg-card lg:grid-cols-4">
      <div v-for="metric in metrics" :key="metric.key" class="border-b p-4 last:border-b-0 sm:p-5 lg:border-b-0 lg:border-r lg:last:border-r-0">
        <div class="flex items-center justify-between gap-3"><dt class="text-sm text-muted-foreground">{{ metric.label }}</dt><component :is="metric.icon" class="h-5 w-5 text-primary" aria-hidden="true" /></div>
        <dd class="mt-3 text-3xl font-bold tabular-nums">{{ summary ? summary[metric.key] : '—' }}</dd>
      </div>
    </dl>
    <form class="flex flex-wrap gap-3 rounded-xl border bg-card p-3" @submit.prevent="applyFilters">
      <div class="relative min-w-48 flex-1"><Search class="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" aria-hidden="true" /><Input v-model.trim="search" class="pl-10" aria-label="Search promotions" placeholder="Search promotion name or code" /></div>
      <Select v-model="state"><SelectTrigger class="w-full sm:w-44" aria-label="Promotion status"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="all">All statuses</SelectItem><SelectItem value="active">Active now</SelectItem><SelectItem value="scheduled">Scheduled</SelectItem><SelectItem value="ended">Ended</SelectItem><SelectItem value="inactive">Inactive</SelectItem></SelectContent></Select>
      <Select v-model="scope"><SelectTrigger class="w-full sm:w-44" aria-label="Catalog scope"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="all">All scopes</SelectItem><SelectItem value="catalog">Entire catalog</SelectItem><SelectItem value="categories">Categories</SelectItem><SelectItem value="products">Specific products</SelectItem></SelectContent></Select>
      <Button variant="outline" type="submit">Apply filters</Button><Button v-if="hasFilters" variant="ghost" type="button" @click="clearFilters">Clear</Button>
    </form>
    <StatePanel v-if="loading" kind="loading" title="Loading promotions" />
    <StatePanel v-else-if="error" kind="error" title="Promotions unavailable" :message="error"><Button type="button" variant="outline" @click="load">Retry</Button></StatePanel>
    <div v-else class="overflow-hidden rounded-xl border bg-card">
      <div class="flex flex-wrap items-center justify-between gap-3 border-b px-5 py-4"><h2 class="text-base font-bold">Your promotions</h2><span class="text-sm text-muted-foreground">{{ count }} {{ count === 1 ? 'promotion' : 'promotions' }}</span></div>
      <StatePanel v-if="!items.length" :title="hasFilters ? 'No matching promotions' : 'Create your first promotion'" :message="hasFilters ? 'Change the filters to see more campaigns.' : 'Offer a percentage or fixed discount across your catalog, chosen categories, or selected products.'">
        <Button v-if="hasFilters" variant="outline" type="button" @click="clearFilters">Clear filters</Button><ButtonLink v-else to="/workspace/sell/promotions/new">Create promotion</ButtonLink>
      </StatePanel>
      <template v-else>
        <div class="hidden overflow-x-auto md:block"><Table><TableHeader><TableRow><TableHead class="pl-5">Promotion</TableHead><TableHead>Offer</TableHead><TableHead>Applies to</TableHead><TableHead>Schedule</TableHead><TableHead>Status</TableHead><TableHead class="pr-5 text-right">Manage</TableHead></TableRow></TableHeader><TableBody>
          <TableRow v-for="item in items" :key="item.public_id" class="transition-colors hover:bg-muted/40">
            <TableCell class="pl-5"><NuxtLink :to="itemPath(item)" class="font-bold text-primary underline-offset-4 hover:underline">{{ item.name }}</NuxtLink><p class="mt-1 text-xs text-muted-foreground">{{ item.is_automatic ? 'Automatic discount' : 'Code: ' + item.code }}</p></TableCell>
            <TableCell class="whitespace-nowrap font-bold">{{ offer(item) }}</TableCell><TableCell>{{ scopeLabel(item) }}</TableCell>
            <TableCell class="text-xs leading-5 text-muted-foreground"><p>{{ item.starts_at ? 'From ' + date(item.starts_at) : 'No start date' }}</p><p>{{ item.ends_at ? 'Until ' + date(item.ends_at) : 'No end date' }}</p></TableCell>
            <TableCell><Badge :variant="status(item) === 'active' ? 'default' : 'secondary'" class="capitalize">{{ status(item) }}</Badge></TableCell>
            <TableCell class="pr-5 text-right"><ButtonLink :to="itemPath(item)" variant="outline" size="sm"><Pencil class="h-4 w-4" aria-hidden="true" />Edit</ButtonLink></TableCell>
          </TableRow>
        </TableBody></Table></div>
        <ul class="divide-y md:hidden"><li v-for="item in items" :key="item.public_id" class="space-y-4 p-4">
          <div class="flex items-start justify-between gap-3"><NuxtLink :to="itemPath(item)" class="font-bold text-primary">{{ item.name }}</NuxtLink><Badge variant="secondary" class="capitalize">{{ status(item) }}</Badge></div>
          <p class="text-xl font-bold">{{ offer(item) }}</p><p class="text-sm text-muted-foreground">{{ scopeLabel(item) }} · {{ item.is_automatic ? 'Automatic' : item.code }}</p>
          <p class="text-xs text-muted-foreground">{{ item.ends_at ? 'Ends ' + date(item.ends_at) : 'No end date' }}</p>
          <ButtonLink :to="itemPath(item)" variant="outline" size="sm"><Pencil class="h-4 w-4" aria-hidden="true" />Edit promotion</ButtonLink>
        </li></ul>
      </template>
      <RecordPagination :page="page" :count="count" :size="20" :busy="loading" @page="changePage" />
    </div>
  </section>
</template>
<script setup>
import { BadgeCheck, CalendarClock, PauseCircle, Pencil, Plus, Search, Tags } from 'lucide-vue-next'
import RecordPagination from '~/components/workspace/RecordPagination.vue'
const route = useRoute(), router = useRouter(), business = useBusinessStore()
const { apiFetch } = useApiClient()
const items = ref([]), count = ref(0), summary = ref(null), loading = ref(true), error = ref('')
const search = ref(String(route.query.search || '')), state = ref(String(route.query.status || 'all')), scope = ref(String(route.query.scope || 'all'))
const page = computed(() => Math.max(1, Number.parseInt(String(route.query.page || '1'), 10) || 1))
const hasFilters = computed(() => Boolean(route.query.search || route.query.status || route.query.scope))
const metrics = [{ key: 'total', label: 'All promotions', icon: Tags }, { key: 'active', label: 'Active now', icon: BadgeCheck }, { key: 'scheduled', label: 'Scheduled', icon: CalendarClock }, { key: 'inactive', label: 'Inactive', icon: PauseCircle }]
let version = 0
async function load() {
  if (!business.activeBusiness) return
  const request = ++version; loading.value = true; error.value = ''
  search.value = String(route.query.search || ''); state.value = String(route.query.status || 'all'); scope.value = String(route.query.scope || 'all')
  const query = new URLSearchParams({ page: String(page.value), page_size: '20' })
  for (const key of ['search', 'status', 'scope']) if (route.query[key]) query.set(key, String(route.query[key]))
  try {
    const response = await apiFetch(`businesses/${business.activeBusiness.public_id}/discounts/?${query}`)
    if (request !== version) return
    items.value = response.results || []; count.value = response.count || 0; summary.value = response.summary
  } catch (err) { if (request === version) error.value = err?.data?.error?.message || 'Could not load promotions.' }
  finally { if (request === version) loading.value = false }
}
function applyFilters() { router.push({ query: { ...(search.value && { search: search.value }), ...(state.value !== 'all' && { status: state.value }), ...(scope.value !== 'all' && { scope: scope.value }) } }) }
function clearFilters() { router.push({ query: {} }) }
function changePage(value) { router.push({ query: { ...route.query, page: value } }) }
const itemPath = (item) => `/workspace/sell/promotions/${item.public_id}`
function status(item) { const now = Date.now(); return !item.is_active ? 'inactive' : item.ends_at && new Date(item.ends_at).getTime() <= now ? 'ended' : item.starts_at && new Date(item.starts_at).getTime() > now ? 'scheduled' : 'active' }
function scopeLabel(item) { return item.category_ids?.length ? `${item.category_ids.length} categories` : item.offering_ids?.length ? `${item.offering_ids.length} products` : 'Entire catalog' }
function offer(item) { return item.value_type === 'percentage' ? `${Number(item.value)}% off` : `${new Intl.NumberFormat('en-PH', { style: 'currency', currency: business.activeBusiness?.currency || 'PHP' }).format(Number(item.value))} off` }
function date(value) { return new Intl.DateTimeFormat('en-PH', { dateStyle: 'medium', timeStyle: 'short', timeZone: business.activeBusiness?.timezone || 'Asia/Manila' }).format(new Date(value)) }
watch(() => [route.fullPath, business.activeBusiness?.public_id], load)
onMounted(async () => { if (!business.activeBusiness) await business.loadBusinesses(); await load() })
</script>
