<template>
  <section class="workspace-page space-y-5">
    <header class="flex flex-wrap items-end justify-between gap-4"><div><h1 class="text-2xl font-extrabold tracking-tight">Live sales dashboard</h1><p class="mt-2 text-sm text-muted-foreground">{{ business.activeBusiness?.display_name }} · Sales performance and work that needs a response.</p></div><LiveRefresh v-model="live" :busy="refreshing" :stale="Boolean(error)" :updated-at="updatedAt" @refresh="refresh" /></header>
    <StatePanel v-if="loading" kind="loading" title="Loading sales activity" message="Calculating current order and request totals." />
    <Alert v-else-if="error" variant="destructive"><AlertTitle>Dashboard could not refresh</AlertTitle><AlertDescription>{{ error }}</AlertDescription></Alert>
    <template v-if="!loading && data">
      <div class="flex flex-wrap items-center justify-between gap-3"><div class="flex gap-1" aria-label="Sales period"><Button v-for="range in [7, 30, 90]" :key="range" size="sm" :variant="days === range ? 'default' : 'ghost'" :aria-pressed="days === range" @click="router.replace({ query: { ...route.query, days: range } })">{{ range }} days</Button></div><span class="text-xs text-muted-foreground">{{ data.date_from }} – {{ data.date_to }} · {{ data.timezone }}</span></div>
      <dl class="grid grid-cols-2 divide-x overflow-hidden rounded-xl border bg-card lg:grid-cols-4"><div v-for="metric in metrics" :key="metric.label" class="border-b p-4 sm:p-5 lg:border-b-0"><dt class="flex items-center justify-between gap-3 text-sm text-muted-foreground">{{ metric.label }}<component :is="metric.icon" class="h-4 w-4 shrink-0" /></dt><dd class="mt-3 text-2xl font-extrabold tabular-nums">{{ metric.value }}</dd><p class="mt-1 text-xs leading-5 text-muted-foreground">{{ metric.detail }}</p></div></dl>
      <div class="grid gap-5 xl:grid-cols-[minmax(0,1.6fr)_minmax(18rem,1fr)]">
        <section class="min-w-0 rounded-xl border bg-card p-4 sm:p-6"><RevenueChart title="Paid order value" description="Fully paid orders by placement date; not a cash-receipts or net-refund report." :points="points" :currency="data.currency" /><ButtonLink variant="link" to="/workspace/analytics" class="mt-4 px-0">Detailed analytics<ArrowUpRight class="h-4 w-4" /></ButtonLink></section>
        <section class="rounded-xl border bg-card"><div class="border-b px-5 py-4"><h2 class="flex items-center gap-2 font-bold"><CircleAlert class="h-5 w-5" />Needs attention</h2><p class="mt-1 text-xs text-muted-foreground">Current queues · independent of the sales period</p></div><div class="divide-y"><NuxtLink v-for="queue in queues" :key="queue.label" :to="queue.to" class="group flex items-center gap-3 px-5 py-4 transition-colors hover:bg-muted/50"><component :is="queue.icon" class="h-5 w-5 shrink-0" :class="queue.urgent && queue.count ? 'text-destructive' : 'text-muted-foreground'" /><div class="min-w-0 flex-1"><h3 class="text-sm font-semibold">{{ queue.label }}</h3><p class="mt-1 text-xs leading-5 text-muted-foreground">{{ queue.detail }}</p></div><strong class="text-xl tabular-nums" :class="queue.urgent && queue.count ? 'text-destructive' : ''">{{ queue.count }}</strong><ChevronRight class="h-4 w-4 text-muted-foreground" /></NuxtLink></div><p v-if="!data.can_manage_requests" class="border-t p-5 text-xs leading-5 text-muted-foreground">Rental and customer-request queues require owner, admin, or manager access.</p></section>
      </div>
      <div v-if="data.requests" class="flex flex-wrap items-center gap-x-8 gap-y-3 border-y py-4 text-sm"><NuxtLink to="/workspace/sell/requests?scope=rentals" class="inline-flex items-center gap-2 hover:underline"><CalendarRange class="h-4 w-4 text-muted-foreground" /><strong class="tabular-nums">{{ data.requests.rentals }}</strong> active rentals</NuxtLink><NuxtLink to="/workspace/sell/requests?scope=held" class="inline-flex items-center gap-2 hover:underline"><PackageCheck class="h-4 w-4 text-muted-foreground" /><strong class="tabular-nums">{{ data.requests.held }}</strong> stock holds</NuxtLink><NuxtLink to="/workspace/sell/requests?scope=returned" class="inline-flex items-center gap-2 hover:underline"><PackageCheck class="h-4 w-4 text-muted-foreground" /><strong class="tabular-nums">{{ data.requests.returned }}</strong> returned rentals</NuxtLink><NuxtLink to="/workspace/sell/requests?scope=closed" class="ml-auto text-xs font-semibold text-primary hover:underline">Request history</NuxtLink></div>
      <OrderDesk compact />
    </template>
  </section>
</template>
<script setup>
import { ArrowUpRight, CalendarRange, ChevronRight, CircleAlert, Clock3, PackageCheck, ReceiptText, Truck, WalletCards } from 'lucide-vue-next'
import LiveRefresh from '~/components/workspace/LiveRefresh.vue'
import OrderDesk from '~/components/workspace/OrderDesk.vue'
const route = useRoute(), router = useRouter(), business = useBusinessStore()
const days = computed(() => [7, 30, 90].includes(Number(route.query.days)) ? Number(route.query.days) : 30)
const { data, loading, refreshing, error, updatedAt, live, refresh } = useLiveWorkspaceResource(() => 'live-sales/', () => ({ days: days.value }))
const money = value => new Intl.NumberFormat(undefined, { style: 'currency', currency: data.value?.currency || 'PHP' }).format(Number(value || 0))
const metrics = computed(() => [
  { label: 'Paid order value', value: money(data.value?.sales.paid_order_value), icon: WalletCards, detail: 'Currently fully paid orders in the period' },
  { label: 'Paid orders', value: data.value?.sales.paid_orders, icon: PackageCheck, detail: 'Cancelled and refunded orders excluded' },
  { label: 'Orders placed', value: data.value?.sales.orders_placed, icon: ReceiptText, detail: 'All order states in the selected period' },
  { label: 'Average paid order', value: money(data.value?.sales.average_paid_order), icon: WalletCards, detail: 'Paid order value ÷ paid orders' },
])
const points = computed(() => (data.value?.series || []).map(item => ({ key: item.date, label: item.date.slice(5), fullLabel: item.date, value: Number(item.value) })))
const queues = computed(() => [
  ...(data.value?.requests ? [
    { label: 'Overdue rental returns', count: data.value.requests.overdue, detail: 'Contact, extend by agreement, or record return', icon: CircleAlert, urgent: true, to: '/workspace/sell/requests?scope=overdue' },
    { label: 'Returns due today', count: data.value.requests.due_today, detail: 'Coordinate collection and check-in', icon: CalendarRange, to: '/workspace/sell/requests?scope=due_today' },
    { label: 'Awaiting approval', count: data.value.requests.pending, detail: 'Review customer requests', icon: Clock3, to: '/workspace/sell/requests?scope=pending' },
    { label: 'Collection overdue', count: data.value.requests.missed_pickup, detail: 'Follow up on an approved rental not collected', icon: PackageCheck, to: '/workspace/sell/requests?scope=missed_pickup' },
  ] : []),
  { label: 'Awaiting payment', count: data.value?.orders.unpaid, detail: 'Verify payment before completing the sale', icon: WalletCards, to: '/workspace/orders?scope=unpaid' },
  { label: 'Open deliveries', count: data.value?.orders.delivery, detail: 'Review orders still being fulfilled', icon: Truck, to: '/workspace/orders?scope=delivery' },
])
</script>
