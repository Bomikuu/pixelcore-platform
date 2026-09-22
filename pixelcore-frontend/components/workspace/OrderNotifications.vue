<template>
  <Popover v-model:open="open">
    <PopoverTrigger as-child>
      <Button variant="ghost" size="icon" class="relative" type="button" aria-label="Order notifications">
        <Bell class="h-[18px] w-[18px]" aria-hidden="true" />
        <span v-if="unreadCount" class="absolute right-1 top-1 grid h-4 min-w-4 place-items-center rounded-full bg-destructive px-1 text-[9px] font-black leading-none text-destructive-foreground">
          {{ unreadCount > 9 ? '9+' : unreadCount }}
        </span>
      </Button>
    </PopoverTrigger>
    <PopoverContent align="end" class="w-[min(24rem,calc(100vw-2rem))] p-0">
      <header class="flex items-center justify-between border-b px-4 py-3">
        <div>
          <h2 class="text-sm font-extrabold">Order activity</h2>
          <p class="mt-0.5 text-xs text-muted-foreground">New online and counter sales</p>
        </div>
        <Button v-if="unreadCount" variant="ghost" size="sm" type="button" @click="markAllRead">Mark read</Button>
      </header>

      <div v-if="loading" class="space-y-3 p-4" aria-label="Loading order notifications">
        <Skeleton v-for="item in 3" :key="item" class="h-14 w-full" />
      </div>
      <div v-else-if="error" class="p-5 text-sm">
        <p class="font-bold">Notifications are unavailable</p>
        <p class="mt-1 text-muted-foreground">{{ error }}</p>
        <Button variant="outline" size="sm" class="mt-3" type="button" @click="load">Try again</Button>
      </div>
      <div v-else-if="!orders.length" class="p-6 text-center">
        <ShoppingBag class="mx-auto h-7 w-7 text-muted-foreground" aria-hidden="true" />
        <p class="mt-3 text-sm font-bold">No orders yet</p>
        <p class="mt-1 text-xs leading-5 text-muted-foreground">New storefront and POS orders will appear here.</p>
      </div>
      <div v-else class="max-h-[23rem] overflow-y-auto">
        <NuxtLink
          v-for="order in orders"
          :key="order.public_id"
          to="/workspace/sell?view=orders"
          class="flex gap-3 border-b px-4 py-3 last:border-b-0 hover:bg-muted/45 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
          @click="markAllRead"
        >
          <span class="mt-1 h-2 w-2 shrink-0 rounded-full" :class="isUnread(order) ? 'bg-primary' : 'bg-border'" aria-hidden="true" />
          <span class="min-w-0 flex-1">
            <span class="flex items-center justify-between gap-3">
              <strong class="truncate text-sm">{{ order.number }}</strong>
              <span class="shrink-0 text-sm font-extrabold tabular-nums">{{ money(order.grand_total) }}</span>
            </span>
            <span class="mt-1 flex items-center justify-between gap-3 text-xs text-muted-foreground">
              <span class="truncate">{{ customerName(order) }}</span>
              <span class="shrink-0">{{ relativeTime(order.placed_at) }}</span>
            </span>
          </span>
        </NuxtLink>
      </div>
      <footer class="border-t p-2">
        <ButtonLink variant="ghost" size="sm" class="w-full" to="/workspace/sell?view=orders" @click="open = false">View all orders <ArrowRight class="h-4 w-4" aria-hidden="true" /></ButtonLink>
      </footer>
    </PopoverContent>
  </Popover>
</template>

<script setup>
import { ArrowRight, Bell, ShoppingBag } from 'lucide-vue-next'

const business = useBusinessStore()
const { apiFetch } = useApiClient()
const open = ref(false)
const orders = ref([])
const loading = ref(false)
const error = ref('')
const lastReadAt = ref('')
let poller

const storageKey = computed(() => `pixelcore-orders-read-${business.activeBusiness?.public_id || 'none'}`)
const unreadCount = computed(() => orders.value.filter(isUnread).length)

watch(() => business.activeBusiness?.public_id, async (businessId) => {
  if (!businessId) return
  lastReadAt.value = window.localStorage.getItem(storageKey.value) || startOfToday()
  await load()
})

onMounted(async () => {
  if (!business.activeBusiness) await business.loadBusinesses()
  lastReadAt.value = window.localStorage.getItem(storageKey.value) || startOfToday()
  await load()
  poller = window.setInterval(load, 30000)
})

onBeforeUnmount(() => window.clearInterval(poller))

async function load() {
  if (!business.activeBusiness || loading.value) return
  loading.value = true
  error.value = ''
  try {
    const response = await apiFetch(`businesses/${business.activeBusiness.public_id}/orders/?page_size=12`)
    orders.value = [...(response.results || [])].sort((left, right) => new Date(right.placed_at) - new Date(left.placed_at))
  } catch (requestError) {
    error.value = requestError?.data?.error?.message || 'Could not retrieve recent orders.'
  } finally {
    loading.value = false
  }
}

function isUnread(order) {
  return Boolean(order.placed_at && new Date(order.placed_at) > new Date(lastReadAt.value || 0))
}

function markAllRead() {
  const newest = orders.value[0]?.placed_at || new Date().toISOString()
  lastReadAt.value = newest
  window.localStorage.setItem(storageKey.value, newest)
}

function customerName(order) {
  const snapshot = order.customer_snapshot || {}
  return [snapshot.first_name, snapshot.last_name].filter(Boolean).join(' ') || snapshot.email || 'Guest customer'
}

function relativeTime(value) {
  if (!value) return ''
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000))
  if (seconds < 60) return 'now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`
  return new Intl.DateTimeFormat('en-PH', { month: 'short', day: 'numeric' }).format(new Date(value))
}

function startOfToday() {
  const date = new Date()
  date.setHours(0, 0, 0, 0)
  return date.toISOString()
}

function money(value) {
  return new Intl.NumberFormat('en-PH', { style: 'currency', currency: business.activeBusiness?.currency || 'PHP', maximumFractionDigits: 0 }).format(Number(value || 0))
}
</script>
