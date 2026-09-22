<template>
  <section class="overflow-hidden rounded-xl border bg-card" aria-label="Order activity">
    <div class="space-y-4 p-4 sm:p-5">
      <div class="flex flex-wrap items-center justify-between gap-3"><h2 class="font-bold">{{ compact ? 'Order activity' : 'Order queue' }}</h2><LiveRefresh v-model="live" :busy="refreshing" :stale="Boolean(error)" :updated-at="updatedAt" @refresh="refresh" /></div>
      <div class="flex flex-wrap gap-2" aria-label="Order views"><Button v-for="tab in tabs" :key="tab.key" type="button" size="sm" :variant="scope === tab.key ? 'default' : 'ghost'" :aria-pressed="scope === tab.key" @click="filter('scope', tab.key)">{{ tab.label }}<span v-if="data?.summary" class="ml-2 font-bold tabular-nums">{{ data.summary[tab.key] }}</span></Button></div>
      <form class="flex gap-2" @submit.prevent="filter('search', search)"><Input v-model.trim="search" aria-label="Search orders by reference or customer" placeholder="Search order number, name, or email" class="max-w-lg" /><Button type="submit" variant="outline"><Search class="h-4 w-4" /><span class="hidden sm:inline">Search</span></Button></form>
    </div>
    <StatePanel v-if="loading" kind="loading" title="Loading orders" />
    <Alert v-else-if="error" variant="destructive" class="m-4 w-auto"><AlertTitle>Orders could not refresh</AlertTitle><AlertDescription>{{ error }}</AlertDescription></Alert>
    <template v-if="!loading && data">
      <div v-if="!data.results.length" class="border-t px-5 py-12 text-center"><PackageOpen class="mx-auto h-7 w-7 text-muted-foreground" /><h3 class="mt-3 font-semibold">No matching orders</h3><p class="mt-2 text-sm text-muted-foreground">Try another view or search. Storefront and counter orders appear here.</p></div>
      <div v-else class="divide-y border-t">
        <div class="hidden grid-cols-[1.15fr_1.2fr_1fr_.8fr_auto] gap-4 bg-muted/40 px-5 py-3 text-xs font-semibold text-muted-foreground lg:grid"><span>Order / placed</span><span>Customer</span><span>Fulfillment / payment</span><span class="text-right">Order total</span><span class="w-20 text-right">Details</span></div>
        <article v-for="order in data.results" :key="order.public_id" class="grid gap-3 px-4 py-4 transition-colors hover:bg-muted/40 sm:px-5 lg:grid-cols-[1.15fr_1.2fr_1fr_.8fr_auto] lg:items-center lg:gap-4">
          <div class="flex items-center gap-3"><ReceiptText class="h-5 w-5 shrink-0 text-muted-foreground" /><div><h3 class="text-sm font-bold">{{ order.number }}</h3><p class="mt-1 text-xs text-muted-foreground">{{ dateTime(order.placed_at) }}</p></div></div>
          <div class="min-w-0"><p class="truncate text-sm font-medium">{{ name(order) }}</p><p class="mt-1 truncate text-xs text-muted-foreground">{{ order.customer_snapshot?.email || 'No email provided' }}</p></div>
          <div><p class="text-xs capitalize">{{ order.fulfillment_type || 'Standard' }} · {{ order.status.replaceAll('_', ' ') }}</p><Badge class="mt-2" :variant="order.payment_status === 'paid' ? 'secondary' : 'outline'">{{ order.payment_status.replaceAll('_', ' ') }}</Badge></div>
          <p class="text-sm font-bold tabular-nums lg:text-right">{{ money(order.grand_total, order.currency) }}</p><Button type="button" variant="outline" size="sm" class="justify-self-start lg:justify-self-end" @click="selected = order">Review<ArrowUpRight class="h-3.5 w-3.5" /></Button>
        </article>
      </div>
      <RecordPagination :page="page" :size="20" :count="data.count" :busy="refreshing" @page="filter('page', $event, false)" />
    </template>
    <Dialog :open="Boolean(selected)" @update:open="value => { if (!value) selected = null }"><DialogContent class="max-h-[90dvh] overflow-y-auto sm:max-w-2xl"><template v-if="selected"><DialogHeader><DialogTitle>{{ selected.number }}</DialogTitle><DialogDescription>{{ name(selected) }} · {{ dateTime(selected.placed_at) }}</DialogDescription></DialogHeader><div class="flex flex-wrap gap-2"><Badge variant="secondary">{{ selected.status }}</Badge><Badge variant="outline">{{ selected.payment_status.replaceAll('_', ' ') }}</Badge><Badge variant="outline">{{ selected.fulfillment_type || 'Standard fulfillment' }}</Badge></div><CustomerContactActions :email="selected.customer_snapshot?.email" :phone="selected.customer_snapshot?.phone" :reference="selected.number" /><div class="divide-y border-y"><div v-for="item in selected.items" :key="item.public_id" class="flex items-center gap-3 py-3"><img v-if="item.image_url" :src="item.image_url" alt="" class="h-12 w-12 rounded-md object-cover" /><div class="min-w-0 flex-1"><p class="text-sm font-semibold">{{ item.name }}</p><p class="mt-1 text-xs text-muted-foreground">{{ item.quantity }} × {{ money(item.unit_price, selected.currency) }} · {{ item.sku || 'No SKU' }}</p></div><strong class="text-sm tabular-nums">{{ money(item.line_total, selected.currency) }}</strong></div></div><dl class="space-y-2 text-sm"><div class="flex justify-between"><dt>Shipping</dt><dd>{{ money(selected.shipping_total, selected.currency) }}</dd></div><div class="flex justify-between"><dt>Discount</dt><dd>{{ money(selected.discount_total, selected.currency) }}</dd></div><div class="flex justify-between text-base font-bold"><dt>Total</dt><dd>{{ money(selected.grand_total, selected.currency) }}</dd></div></dl><p v-if="selected.notes" class="whitespace-pre-line text-sm leading-6">{{ selected.notes }}</p><Alert v-if="['unpaid', 'pending'].includes(selected.payment_status)"><AlertTitle>Payment needs review</AlertTitle><AlertDescription>Verify the payment through the existing order or counter flow. Opening this record does not mark it paid.</AlertDescription></Alert><DialogFooter><Button variant="outline" @click="selected = null">Close</Button><ButtonLink to="/workspace/sell/pos">Open counter setup</ButtonLink></DialogFooter></template></DialogContent></Dialog>
  </section>
</template>
<script setup>
import { ArrowUpRight, PackageOpen, ReceiptText, Search } from 'lucide-vue-next'
import LiveRefresh from './LiveRefresh.vue'
import RecordPagination from './RecordPagination.vue'
import CustomerContactActions from './CustomerContactActions.vue'
const props = defineProps({ compact: Boolean })
const route = useRoute(), router = useRouter(), business = useBusinessStore()
const prefix = computed(() => props.compact ? 'orders_' : '')
const value = key => route.query[`${prefix.value}${key}`]
const page = computed(() => Math.max(1, Math.floor(Number(value('page')) || 1)))
const scope = computed(() => String(value('scope') || 'active'))
const search = ref(String(value('search') || '')), selected = ref(null)
const tabs = [{ key: 'active', label: 'Active' }, { key: 'unpaid', label: 'Awaiting payment' }, { key: 'delivery', label: 'Deliveries' }, { key: 'fulfilled', label: 'Fulfilled' }, { key: 'cancelled', label: 'Cancelled' }, { key: 'refunded', label: 'Refunds' }, { key: 'all', label: 'All orders' }]
const { data, loading, refreshing, error, updatedAt, live, refresh } = useLiveWorkspaceResource(() => 'orders/', () => ({ scope: scope.value, page: page.value, page_size: 20, search: value('search') }), computed(() => Boolean(selected.value)))
watch(() => value('search'), next => { search.value = String(next || '') })
watch(() => business.activeBusiness?.public_id, () => { selected.value = null })
function filter(key, next, reset = true) { router.replace({ query: { ...route.query, ...(reset ? { [`${prefix.value}page`]: undefined } : {}), [`${prefix.value}${key}`]: next || undefined } }) }
function name(order) { const customer = order.customer_snapshot || {}; return [customer.first_name, customer.last_name].filter(Boolean).join(' ') || customer.email || 'Guest customer' }
function money(amount, currency) { return new Intl.NumberFormat(undefined, { style: 'currency', currency: currency || 'PHP' }).format(Number(amount || 0)) }
function dateTime(date) { return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short', timeZone: business.activeBusiness?.timezone || 'Asia/Manila' }).format(new Date(date)) }
</script>
