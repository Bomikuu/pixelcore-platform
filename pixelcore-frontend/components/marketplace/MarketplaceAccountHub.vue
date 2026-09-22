<template>
  <Tabs
    :model-value="activeTab"
    orientation="vertical"
    class="grid gap-8 lg:grid-cols-[17rem_minmax(0,1fr)] lg:items-start"
    @update:model-value="$emit('update:activeTab', $event)"
  >
    <aside class="overflow-hidden rounded-2xl border bg-card lg:sticky lg:top-28">
      <div class="flex items-center gap-3 border-b p-5">
        <Avatar size="base">
          <AvatarFallback class="bg-primary text-primary-foreground">
            {{ initials }}
          </AvatarFallback>
        </Avatar>
        <div class="min-w-0">
          <p class="truncate font-semibold">{{ displayName }}</p>
          <p class="truncate text-sm text-muted-foreground">
            {{ authenticated ? accountEmail : 'Guest account' }}
          </p>
        </div>
      </div>

      <div class="p-3 lg:hidden">
        <Select
          :model-value="activeTab"
          @update:model-value="$emit('update:activeTab', $event)"
        >
          <SelectTrigger aria-label="Choose account section">
            <SelectValue placeholder="Choose account section" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem
              v-for="item in navigationItems"
              :key="item.value"
              :value="item.value"
            >
              {{ item.label }}
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      <TabsList
        class="hidden h-auto w-full flex-col items-stretch justify-start gap-1 rounded-none bg-transparent p-2 lg:flex"
        aria-label="Customer account"
      >
        <TabsTrigger
          v-for="item in navigationItems"
          :key="item.value"
          :value="item.value"
          class="min-h-11 shrink-0 justify-start gap-3 px-3 data-[state=active]:bg-secondary data-[state=active]:shadow-none lg:w-full [&>span]:w-full [&>span]:justify-start"
        >
          <component :is="item.icon" class="h-4 w-4 text-primary" aria-hidden="true" />
          <span>{{ item.label }}</span>
          <Badge
            v-if="item.count !== null"
            variant="secondary"
            class="ml-auto min-w-6 justify-center px-1.5 tabular-nums"
          >
            {{ item.count }}
          </Badge>
        </TabsTrigger>
      </TabsList>

      <div class="border-t p-4">
        <ButtonAnchor :href="`${base}/shop`" variant="outline" class="w-full gap-2">
          Continue shopping
          <ArrowUpRight class="h-4 w-4" aria-hidden="true" />
        </ButtonAnchor>
      </div>
    </aside>

    <div class="min-w-0">
      <header class="border-b pb-6">
        <h1 class="display-face text-3xl font-semibold tracking-[-0.025em] sm:text-4xl">
          {{ currentSection.title }}
        </h1>
        <p class="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base">
          {{ currentSection.description }}
        </p>
      </header>

      <StatePanel
        v-if="loading"
        class="mt-8"
        kind="loading"
        title="Loading your account"
        message="Retrieving your latest activity with this business."
      />
      <StatePanel
        v-else-if="error"
        class="mt-8"
        kind="error"
        title="Account unavailable"
        :message="error"
      />

      <template v-else>
        <TabsContent value="overview" class="mt-0 pt-8">
          <Alert v-if="!authenticated" class="mb-8">
            <LockKeyhole class="h-4 w-4" aria-hidden="true" />
            <AlertTitle>Sign in to unlock your account history</AlertTitle>
            <AlertDescription class="mt-2">
              Your wishlist is available now. Sign in to see orders, bookings, payments, and saved addresses.
              <ButtonLink :to="signInUrl" size="sm" class="mt-4 w-fit">
                Sign in
              </ButtonLink>
            </AlertDescription>
          </Alert>

          <div class="grid overflow-hidden rounded-2xl border bg-card sm:grid-cols-3">
            <div
              v-for="summary in overviewSummary"
              :key="summary.label"
              class="border-b p-5 last:border-b-0 sm:border-b-0 sm:border-r sm:last:border-r-0"
            >
              <component :is="summary.icon" class="h-5 w-5 text-primary" aria-hidden="true" />
              <strong class="mt-5 block text-3xl font-semibold tabular-nums">{{ summary.value }}</strong>
              <span class="mt-1 block text-sm text-muted-foreground">{{ summary.label }}</span>
            </div>
          </div>

          <div class="mt-10 grid gap-10 xl:grid-cols-2">
            <section aria-labelledby="recent-orders-heading">
              <div class="flex items-center justify-between gap-4">
                <h2 id="recent-orders-heading" class="text-xl font-semibold">Recent orders</h2>
                <Button
                  v-if="orders.length"
                  type="button"
                  variant="ghost"
                  size="sm"
                  @click="$emit('update:activeTab', 'orders')"
                >
                  View all
                </Button>
              </div>
              <div v-if="orders.length" class="mt-4 border-y">
                <OrderRow
                  v-for="order in orders.slice(0, 3)"
                  :key="order.public_id"
                  :order="order"
                  :currency="currency"
                />
              </div>
              <p v-else class="mt-4 border-y py-8 text-sm text-muted-foreground">
                Your recent purchases will appear here.
              </p>
            </section>

            <section aria-labelledby="recent-bookings-heading">
              <div class="flex items-center justify-between gap-4">
                <h2 id="recent-bookings-heading" class="text-xl font-semibold">Upcoming bookings</h2>
                <Button
                  v-if="bookings.length"
                  type="button"
                  variant="ghost"
                  size="sm"
                  @click="$emit('update:activeTab', 'bookings')"
                >
                  View all
                </Button>
              </div>
              <div v-if="bookings.length" class="mt-4 border-y">
                <article
                  v-for="booking in bookings.slice(0, 3)"
                  :key="booking.public_id"
                  class="flex items-center justify-between gap-4 border-b py-4 last:border-b-0"
                >
                  <div class="min-w-0">
                    <p class="truncate font-medium">{{ booking.offering_name }}</p>
                    <p class="mt-1 text-xs text-muted-foreground">{{ formatDate(booking.starts_at) }}</p>
                  </div>
                  <StatusPill :value="booking.status" />
                </article>
              </div>
              <p v-else class="mt-4 border-y py-8 text-sm text-muted-foreground">
                Confirmed services and reservations will appear here.
              </p>
            </section>
          </div>
        </TabsContent>

        <TabsContent value="profile" class="mt-0 pt-8">
          <AccountSignInState v-if="!authenticated" :sign-in-url="signInUrl" />
          <AccountProfileSettings
            v-else
            :customer="customer"
            :user="user"
            :identity="identity"
            :saving="profileSaving"
            :error="profileError"
            @save="$emit('saveProfile', $event)"
          />
        </TabsContent>

        <TabsContent value="orders" class="mt-0 pt-8">
          <AccountSignInState v-if="!authenticated" :sign-in-url="signInUrl" />
          <div v-else-if="orders.length" class="divide-y border-y">
            <OrderRow
              v-for="order in orders"
              :key="order.public_id"
              :order="order"
              :currency="currency"
              detailed
            />
          </div>
          <StatePanel
            v-else
            title="No orders yet"
            message="Completed storefront and counter purchases linked to your email will appear here."
          >
            <ButtonAnchor :href="`${base}/shop`">Browse products</ButtonAnchor>
          </StatePanel>
        </TabsContent>

        <TabsContent value="bookings" class="mt-0 pt-8">
          <AccountSignInState v-if="!authenticated" :sign-in-url="signInUrl" />
          <div v-else-if="bookings.length" class="divide-y border-y">
            <article
              v-for="booking in bookings"
              :key="booking.public_id"
              class="grid gap-4 py-5 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center"
            >
              <div class="min-w-0">
                <div class="flex flex-wrap items-center gap-2">
                  <h2 class="font-semibold">{{ booking.offering_name }}</h2>
                  <StatusPill :value="booking.status" />
                </div>
                <p class="mt-2 text-sm text-muted-foreground">
                  {{ formatDate(booking.starts_at) }} · {{ booking.staff_name || 'Staff assigned by the business' }}
                </p>
              </div>
              <div class="text-sm sm:text-right">
                <p class="font-medium">{{ booking.seats }} {{ booking.seats === 1 ? 'guest' : 'guests' }}</p>
                <p class="mt-1 text-muted-foreground">{{ paymentStatus(booking.payment_status) }}</p>
              </div>
            </article>
          </div>
          <StatePanel
            v-else
            title="No bookings yet"
            message="Appointments, sessions, and reservations connected to your account will appear here."
          />
        </TabsContent>

        <TabsContent value="wishlist" class="mt-0 pt-8">
          <Alert v-if="!authenticated" class="mb-8">
            <Heart class="h-4 w-4" aria-hidden="true" />
            <AlertTitle>Your wishlist is saved on this device</AlertTitle>
            <AlertDescription>
              Sign in to carry these products to another device and keep them with your customer profile.
            </AlertDescription>
          </Alert>

          <div v-if="wishlistProducts.length" class="grid gap-x-4 gap-y-10 sm:grid-cols-2 xl:grid-cols-3">
            <ProductCard
              v-for="product in wishlistProducts"
              :key="product.public_id"
              :product="product"
              :base="base"
              :slug="slug"
              :currency="currency"
            />
          </div>
          <StatePanel
            v-else
            title="Nothing saved yet"
            message="Use the heart on any product to keep it close."
          >
            <ButtonAnchor :href="`${base}/shop`">Explore products</ButtonAnchor>
          </StatePanel>
        </TabsContent>

        <TabsContent value="payments" class="mt-0 pt-8">
          <AccountSignInState v-if="!authenticated" :sign-in-url="signInUrl" />
          <template v-else>
            <Alert class="mb-8">
              <ShieldCheck class="h-4 w-4" aria-hidden="true" />
              <AlertTitle>Payment details stay with the payment provider</AlertTitle>
              <AlertDescription>
                PixelCore shows your payment and receipt history, but does not expose or store full card or wallet credentials here.
              </AlertDescription>
            </Alert>

            <div v-if="paymentOrders.length" class="divide-y border-y">
              <article
                v-for="order in paymentOrders"
                :key="order.public_id"
                class="grid gap-4 py-5 sm:grid-cols-[minmax(0,1fr)_auto_auto] sm:items-center"
              >
                <div>
                  <p class="font-semibold">{{ order.number }}</p>
                  <p class="mt-1 text-xs text-muted-foreground">{{ formatDate(order.placed_at) }}</p>
                </div>
                <div class="sm:text-right">
                  <p class="font-medium">{{ paymentMethod(order.payment_method) }}</p>
                  <p class="mt-1 text-xs text-muted-foreground">{{ money(order.grand_total, order.currency) }}</p>
                </div>
                <StatusPill :value="order.payment_status" />
              </article>
            </div>
            <StatePanel
              v-else
              title="No payment history"
              message="Payment records and receipt totals will appear after your first order."
            />
          </template>
        </TabsContent>

        <TabsContent value="addresses" class="mt-0 pt-8">
          <AccountSignInState v-if="!authenticated" :sign-in-url="signInUrl" />
          <AccountAddressManager
            v-else
            :addresses="addresses"
            :saving="addressSaving"
            :error="addressError"
            @save="$emit('saveAddress', $event)"
            @remove="$emit('removeAddress', $event)"
          />
        </TabsContent>
      </template>
    </div>
  </Tabs>
</template>

<script setup>
import {
  ArrowUpRight,
  CalendarDays,
  CreditCard,
  Heart,
  LayoutDashboard,
  LockKeyhole,
  MapPin,
  PackageCheck,
  ShieldCheck,
  UserRound,
} from 'lucide-vue-next'
import AccountSignInState from './account/AccountSignInState.vue'
import AccountAddressManager from './account/AccountAddressManager.vue'
import AccountProfileSettings from './account/AccountProfileSettings.vue'
import OrderRow from './account/OrderRow.vue'

const props = defineProps({
  activeTab: { type: String, default: 'overview' },
  identity: { type: Object, required: true },
  user: { type: Object, default: null },
  portal: { type: Object, default: null },
  wishlistProducts: { type: Array, default: () => [] },
  authenticated: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  profileSaving: { type: Boolean, default: false },
  profileError: { type: String, default: '' },
  addressSaving: { type: Boolean, default: false },
  addressError: { type: String, default: '' },
  base: { type: String, required: true },
  slug: { type: String, required: true },
  signInUrl: { type: String, required: true },
})

defineEmits([
  'update:activeTab',
  'saveProfile',
  'saveAddress',
  'removeAddress',
])

const customer = computed(() => props.portal?.customer || null)
const orders = computed(() => props.portal?.orders || [])
const bookings = computed(() => props.portal?.bookings || [])
const addresses = computed(() => customer.value?.addresses || [])
const paymentOrders = computed(() =>
  orders.value.filter((order) => order.payment_method || order.payment_attempts?.length),
)
const currency = computed(() => props.identity.currency || 'PHP')
const accountEmail = computed(() => customer.value?.email || props.user?.email || '')
const displayName = computed(() => {
  const firstName = customer.value?.first_name || props.user?.first_name || ''
  const lastName = customer.value?.last_name || props.user?.last_name || ''
  return [firstName, lastName].filter(Boolean).join(' ') || accountEmail.value || 'Your account'
})
const initials = computed(() => {
  const value = displayName.value
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
  return value || 'PC'
})

const sections = {
  overview: {
    title: `Your account at ${props.identity.display_name}`,
    description: 'A clear view of your purchases, bookings, saved products, and customer details.',
  },
  profile: {
    title: 'Profile',
    description: 'The name and contact details connected to your customer record.',
  },
  orders: {
    title: 'Orders',
    description: 'Track purchases, fulfillment progress, totals, and receipts.',
  },
  bookings: {
    title: 'Bookings',
    description: 'Review upcoming appointments, sessions, and reservations.',
  },
  wishlist: {
    title: 'Wishlist',
    description: 'Products you saved from this storefront, all in one place.',
  },
  payments: {
    title: 'Payments and receipts',
    description: 'Review payment methods, statuses, and totals from your orders.',
  },
  addresses: {
    title: 'Addresses',
    description: 'Delivery destinations connected to your customer profile.',
  },
}

const currentSection = computed(() => sections[props.activeTab] || sections.overview)
const navigationItems = computed(() => [
  { value: 'overview', label: 'Overview', icon: LayoutDashboard, count: null },
  { value: 'profile', label: 'Profile', icon: UserRound, count: null },
  { value: 'orders', label: 'Orders', icon: PackageCheck, count: props.authenticated ? orders.value.length : null },
  { value: 'bookings', label: 'Bookings', icon: CalendarDays, count: props.authenticated ? bookings.value.length : null },
  { value: 'wishlist', label: 'Wishlist', icon: Heart, count: props.wishlistProducts.length },
  { value: 'payments', label: 'Payments', icon: CreditCard, count: null },
  { value: 'addresses', label: 'Addresses', icon: MapPin, count: props.authenticated ? addresses.value.length : null },
])

const overviewSummary = computed(() => [
  { label: 'Orders', value: props.authenticated ? orders.value.length : '—', icon: PackageCheck },
  { label: 'Bookings', value: props.authenticated ? bookings.value.length : '—', icon: CalendarDays },
  { label: 'Saved products', value: props.wishlistProducts.length, icon: Heart },
])

function money(value, valueCurrency = currency.value) {
  return new Intl.NumberFormat('en-PH', {
    style: 'currency',
    currency: valueCurrency || currency.value,
  }).format(Number(value || 0))
}

function formatDate(value) {
  if (!value) return 'Date unavailable'
  return new Intl.DateTimeFormat('en-PH', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function paymentMethod(value) {
  const labels = {
    paymongo: 'PayMongo',
    cod: 'Cash on delivery',
    manual: 'Manual payment',
    cash: 'Cash',
    card: 'Card terminal',
    gcash: 'GCash',
    maya: 'Maya',
  }
  return labels[value] || 'Payment method unavailable'
}

function paymentStatus(value) {
  const labels = {
    unpaid: 'Payment not required or unpaid',
    pending: 'Payment pending',
    paid: 'Paid',
    partially_refunded: 'Partially refunded',
    refunded: 'Refunded',
  }
  return labels[value] || 'Payment status unavailable'
}
</script>
