<template>
  <article
    class="grid gap-4 border-b py-4 last:border-b-0"
    :class="detailed ? 'sm:grid-cols-[minmax(0,1fr)_auto_auto] sm:items-center' : 'sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center'"
  >
    <div class="min-w-0">
      <div class="flex flex-wrap items-center gap-2">
        <p class="font-semibold">{{ order.number }}</p>
        <StatusPill v-if="detailed" :value="order.status" />
      </div>
      <p class="mt-1 text-xs text-muted-foreground">
        {{ formatDate(order.placed_at) }}
        <template v-if="detailed"> · {{ itemCount }} {{ itemCount === 1 ? 'item' : 'items' }}</template>
      </p>
    </div>
    <div class="sm:text-right">
      <p class="font-semibold">{{ money(order.grand_total) }}</p>
      <p v-if="detailed" class="mt-1 text-xs text-muted-foreground">{{ fulfillmentLabel }}</p>
    </div>
    <StatusPill v-if="detailed" :value="order.payment_status" />
  </article>
</template>

<script setup>
const props = defineProps({
  order: { type: Object, required: true },
  currency: { type: String, default: 'PHP' },
  detailed: { type: Boolean, default: false },
})

const itemCount = computed(() =>
  (props.order.items || []).reduce((total, item) => total + Number(item.quantity || 0), 0),
)

const fulfillmentLabel = computed(() => {
  const labels = {
    delivery: 'Delivery',
    pickup: 'Pickup',
    digital: 'Digital delivery',
    booking: 'Booking',
  }
  return labels[props.order.fulfillment_type] || 'Fulfillment pending'
})

function money(value) {
  return new Intl.NumberFormat('en-PH', {
    style: 'currency',
    currency: props.order.currency || props.currency,
  }).format(Number(value || 0))
}

function formatDate(value) {
  return new Intl.DateTimeFormat('en-PH', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}
</script>
